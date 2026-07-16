"""مشغّل التداول الآلي متعدد المحافظ.

يقرأ multi_account_config.json ويطلق عملية continuous_auto_trader.py مستقلة لكل حساب
مُفعّل، كل واحدة مربوطة بمحفظة MT5 خاصة (login/server/path) وإعدادات إستراتيجية خاصة.
يراقب العمليات ويعيد تشغيل المتعطل منها مع تأخير تصاعدي.

قيد مهم: مكتبة MetaTrader5 لبايثون تتصل بمحطة/حساب واحد لكل عملية. لتشغيل عدة حسابات
في نفس الوقت يجب أن يكون لكل حساب نسخة محطة MetaTrader 5 مستقلة (path مختلف لـ terminal64.exe).

الاستخدام:
    python run_multi_account_traders.py
    python run_multi_account_traders.py --registry multi_account_config.json
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
TRADER_SCRIPT = PROJECT_ROOT / "continuous_auto_trader.py"
DEFAULT_REGISTRY = PROJECT_ROOT / "multi_account_config.json"
DEFAULT_MAX_ACCOUNTS = 10

# إعادة التشغيل عند التعطل
MIN_RESTART_DELAY_SEC = 5
MAX_RESTART_DELAY_SEC = 120
# إن بقيت العملية حيّة هذه المدة نعتبرها مستقرة ونصفّر تأخير إعادة التشغيل
HEALTHY_UPTIME_SEC = 60
MAX_QUICK_FAILURES = 3
QUICK_FAILURE_WINDOW_SEC = 15


def _resolve_path(base: Path, value: str) -> Path:
    p = Path(str(value or "").strip()).expanduser()
    if not p.is_absolute():
        p = base / p
    return p


def load_registry(registry_path: Path) -> list:
    if not registry_path.exists():
        print(f"[multi-trader] registry not found: {registry_path}", flush=True)
        return []
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[multi-trader] failed to read registry: {exc}", flush=True)
        return []

    accounts = []
    for raw in (data.get("accounts") or []):
        if not isinstance(raw, dict):
            continue
        if not bool(raw.get("enabled", True)):
            continue
        account_id = str(raw.get("id") or "").strip()
        if not account_id:
            print("[multi-trader] skipping account with empty id", flush=True)
            continue

        config_path = _resolve_path(PROJECT_ROOT, raw.get("config") or f"accounts/{account_id}/config.json")
        wallet_path = _resolve_path(PROJECT_ROOT, raw.get("wallet") or f"accounts/{account_id}/wallet.json")
        state_path = _resolve_path(PROJECT_ROOT, raw.get("state") or f"accounts/{account_id}/runtime_state.json")

        accounts.append({
            "id": account_id,
            "label": str(raw.get("label") or account_id),
            "config": config_path,
            "wallet": wallet_path,
            "state": state_path,
        })
    return accounts


def _terminal_path_for(wallet_path: Path) -> str:
    try:
        payload = json.loads(wallet_path.read_text(encoding="utf-8")) if wallet_path.exists() else {}
        return str(payload.get("path") or "").strip()
    except Exception:
        return ""


def _wallet_payload(wallet_path: Path) -> dict:
    try:
        return json.loads(wallet_path.read_text(encoding="utf-8")) if wallet_path.exists() else {}
    except Exception:
        return {}


def _clean_text(value: str) -> str:
    text = str(value or "").strip()
    while len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
        text = text[1:-1].strip()
    return text


def _wallet_readiness_error(wallet_path: Path) -> str:
    payload = _wallet_payload(wallet_path)
    if not payload:
        return "wallet file is empty or unreadable"
    if not int(payload.get("login") or 0):
        return "missing MT5 login"
    if not str(payload.get("password") or "").strip():
        return "missing MT5 password"
    if not str(payload.get("server") or "").strip():
        return "missing MT5 server"
    terminal = _clean_text(payload.get("path") or "")
    if not terminal:
        return "missing MT5 terminal path"
    if not os.path.exists(terminal):
        return f"MT5 terminal not found at: {terminal}"
    return ""


def validate_accounts(accounts: list) -> list:
    """فلترة الحسابات غير الجاهزة مع تحذيرات واضحة."""
    seen_terminals = {}
    runnable_accounts = []
    for acc in accounts:
        if not acc["config"].exists():
            print(f"[multi-trader] WARNING [{acc['id']}] config file missing: {acc['config']}", flush=True)
        if not acc["wallet"].exists():
            print(f"[multi-trader] WARNING [{acc['id']}] wallet file missing: {acc['wallet']}", flush=True)
            continue

        readiness_error = _wallet_readiness_error(acc["wallet"])
        if readiness_error:
            print(f"[multi-trader] SKIP [{acc['id']}] {readiness_error}", flush=True)
            continue

        terminal = _terminal_path_for(acc["wallet"])
        if terminal in seen_terminals:
            print(
                f"[multi-trader] SKIP [{acc['id']}] shares the same MT5 terminal path as "
                f"[{seen_terminals[terminal]}]: {terminal}. لا يمكن تشغيل حسابين على نفس المحطة في آن واحد؛ "
                f"استخدم نسخة محطة MT5 مستقلة لكل حساب.",
                flush=True,
            )
            continue

        seen_terminals[terminal] = acc["id"]
        runnable_accounts.append(acc)
    return runnable_accounts


def build_command(acc: dict) -> list:
    return [
        sys.executable,
        str(TRADER_SCRIPT),
        "--config", str(acc["config"]),
        "--state", str(acc["state"]),
        "--wallet-config", str(acc["wallet"]),
        "--account-id", acc["id"],
    ]


def spawn(acc: dict):
    acc["state"].parent.mkdir(parents=True, exist_ok=True)
    log_path = acc["state"].parent / "trader.out.log"
    log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    log_file.write(f"\n===== [{acc['id']}] start {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")

    env = dict(os.environ)
    env["AUTO_TRADER_ACCOUNT_ID"] = acc["id"]
    env["MT5_WALLET_CONFIG"] = str(acc["wallet"])
    env["AUTO_TRADER_USE_MT5_MARKET_DATA"] = "1"
    env["AUTO_TRADER_REQUIRE_MT5_MARKET_DATA"] = "1"
    env["ENABLE_MT5_MARKET_DATA"] = "1"
    env["MT5_MARKET_DATA_MODE"] = "mt5_only"
    env.setdefault("PYTHONUTF8", "1")

    creationflags = 0
    if os.name == "nt":
        # مجموعة عمليات مستقلة حتى لا يقتل Ctrl+C الأبناء فورًا قبل التنظيف
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(
        build_command(acc),
        cwd=str(PROJECT_ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=creationflags,
    )
    print(f"[multi-trader] started [{acc['id']}] pid={proc.pid} -> {log_path}", flush=True)
    return proc, log_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the auto trader across multiple MT5 wallets/accounts")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Path to multi_account_config.json")
    parser.add_argument("--max-accounts", type=int, default=DEFAULT_MAX_ACCOUNTS, help="Maximum enabled accounts to run")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    accounts = load_registry(registry_path)
    if not accounts:
        print("[multi-trader] no enabled accounts found. Nothing to run.", flush=True)
        return 1

    max_accounts = max(1, int(args.max_accounts or DEFAULT_MAX_ACCOUNTS))
    if len(accounts) > max_accounts:
        print(
            f"[multi-trader] enabled accounts ({len(accounts)}) exceed limit ({max_accounts}); "
            f"running first {max_accounts} only.",
            flush=True,
        )
        accounts = accounts[:max_accounts]

    accounts = validate_accounts(accounts)
    if not accounts:
        print("[multi-trader] no runnable accounts found after validation.", flush=True)
        return 1

    # حالة كل حساب: process, log file, آخر وقت بدء, تأخير إعادة التشغيل الحالي
    runtime = {}
    for acc in accounts:
        proc, log_file = spawn(acc)
        runtime[acc["id"]] = {
            "acc": acc,
            "proc": proc,
            "log": log_file,
            "started_at": time.time(),
            "restart_delay": MIN_RESTART_DELAY_SEC,
            "restart_at": 0.0,
            "quick_failures": 0,
            "paused": False,
        }

    stopping = {"flag": False}

    def _handle_stop(signum, frame):
        stopping["flag"] = True
        print("\n[multi-trader] stop requested, terminating child traders...", flush=True)

    try:
        signal.signal(signal.SIGINT, _handle_stop)
        signal.signal(signal.SIGTERM, _handle_stop)
    except Exception:
        pass

    try:
        while not stopping["flag"]:
            now = time.time()
            for state in runtime.values():
                acc = state["acc"]
                proc = state["proc"]

                if state.get("paused"):
                    continue

                if proc is not None and proc.poll() is None:
                    # حيّة؛ صفّر التأخير إن استقرت
                    if state["restart_delay"] > MIN_RESTART_DELAY_SEC and (now - state["started_at"]) >= HEALTHY_UPTIME_SEC:
                        state["restart_delay"] = MIN_RESTART_DELAY_SEC
                    if (now - state["started_at"]) >= QUICK_FAILURE_WINDOW_SEC:
                        state["quick_failures"] = 0
                    continue

                # العملية انتهت
                if proc is not None:
                    code = proc.returncode
                    lived_for = now - state["started_at"]
                    print(f"[multi-trader] [{acc['id']}] exited code={code}", flush=True)
                    try:
                        state["log"].write(f"===== [{acc['id']}] exited code={code} {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
                    except Exception:
                        pass
                    state["proc"] = None

                    if code not in (0, None) and lived_for < QUICK_FAILURE_WINDOW_SEC:
                        state["quick_failures"] += 1
                    else:
                        state["quick_failures"] = 0

                    if state["quick_failures"] >= MAX_QUICK_FAILURES:
                        state["paused"] = True
                        print(
                            f"[multi-trader] PAUSED [{acc['id']}] after {state['quick_failures']} quick failures. "
                            f"راجع ملف السجل وبيانات تسجيل الدخول ثم أعد التشغيل.",
                            flush=True,
                        )
                        continue

                    state["restart_at"] = now + state["restart_delay"]

                if state["restart_at"] and now >= state["restart_at"]:
                    print(f"[multi-trader] restarting [{acc['id']}] (delay was {state['restart_delay']}s)", flush=True)
                    new_proc, new_log = spawn(acc)
                    state["proc"] = new_proc
                    state["log"] = new_log
                    state["started_at"] = now
                    state["restart_at"] = 0.0
                    state["restart_delay"] = min(MAX_RESTART_DELAY_SEC, state["restart_delay"] * 2)

            time.sleep(2)
    finally:
        for state in runtime.values():
            proc = state.get("proc")
            if proc is not None and proc.poll() is None:
                try:
                    if os.name == "nt":
                        proc.send_signal(getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
                    else:
                        proc.terminate()
                except Exception:
                    pass
        # مهلة للإنهاء النظيف
        deadline = time.time() + 15
        for state in runtime.values():
            proc = state.get("proc")
            if proc is None:
                continue
            remaining = max(0, deadline - time.time())
            try:
                proc.wait(timeout=remaining)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                state["log"].close()
            except Exception:
                pass
        print("[multi-trader] all child traders stopped.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

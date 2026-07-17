import json
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ACCOUNTS_FILE = PROJECT_ROOT / "multi_wallet_trader_accounts.json"
TRADER_SCRIPT = PROJECT_ROOT / "continuous_auto_trader.py"


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_file(raw_value: str, fallback: str) -> Path:
    text = str(raw_value or "").strip()
    if not text:
        text = fallback
    file_path = Path(text)
    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path
    return file_path


def _launch_account(py_exe: str, item: dict) -> subprocess.Popen:
    account_id = str(item.get("account_id") or "").strip()
    if not account_id:
        raise ValueError("account_id is required for each account")

    wallet_cfg = _resolve_file(item.get("wallet_config"), f"mt5_wallet_config.{account_id}.json")
    trader_cfg = _resolve_file(item.get("trader_config"), f"auto_trading_user_config.{account_id}.json")
    state_file = _resolve_file(item.get("state_file"), f"auto_trading_runtime_state.{account_id}.json")

    cmd = [
        py_exe,
        str(TRADER_SCRIPT),
        "--account-id",
        account_id,
        "--wallet-config",
        str(wallet_cfg),
        "--config",
        str(trader_cfg),
        "--state",
        str(state_file),
    ]

    return subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))


def main() -> int:
    if not ACCOUNTS_FILE.exists():
        print(json.dumps({"ok": False, "error": "accounts_file_not_found", "path": str(ACCOUNTS_FILE)}, ensure_ascii=False))
        return 1

    payload = _read_json(ACCOUNTS_FILE) or {}
    accounts = payload.get("accounts") if isinstance(payload, dict) else None
    if not isinstance(accounts, list):
        print(json.dumps({"ok": False, "error": "invalid_accounts_payload"}, ensure_ascii=False))
        return 1

    py_exe = sys.executable
    started = []
    skipped = []

    for item in accounts:
        if not isinstance(item, dict):
            continue
        if not bool(item.get("enabled", True)):
            skipped.append({"account_id": item.get("account_id"), "reason": "disabled"})
            continue
        try:
            proc = _launch_account(py_exe=py_exe, item=item)
            started.append({"account_id": item.get("account_id"), "pid": int(proc.pid)})
            time.sleep(0.6)
        except Exception as exc:
            skipped.append({"account_id": item.get("account_id"), "reason": str(exc)})

    print(
        json.dumps(
            {
                "ok": True,
                "started_count": len(started),
                "skipped_count": len(skipped),
                "started": started,
                "skipped": skipped,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
import json
import os
import signal
import subprocess
import sys
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import time

try:
    import psutil
except Exception:
    psutil = None


IS_FROZEN = bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    if IS_FROZEN:
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PROJECT_ROOT = app_root()
REGISTRY_PATH = PROJECT_ROOT / "multi_account_config.json"
RUNNER_SCRIPT = PROJECT_ROOT / "run_multi_account_traders.py"
TRADER_SCRIPT = PROJECT_ROOT / "continuous_auto_trader.py"
TRADER_EXE = PROJECT_ROOT / "continuous_auto_trader.exe"

CUSTOM_PRESET_LABEL = "✏️ مخصص"
EXECUTION_MODE_MARKET = "سوق مباشر"
EXECUTION_MODE_PENDING = "أوامر معلقة فقط"
EXECUTION_MODE_PENDING_FALLBACK = "أوامر معلقة ثم سوق"
EXECUTION_MODES = [EXECUTION_MODE_MARKET, EXECUTION_MODE_PENDING, EXECUTION_MODE_PENDING_FALLBACK]

TRADING_PRESETS = {
    "🌐 إشارات الموقع - الرموز المختارة فقط": {
        "strategy_name": "site_db_selected_symbols_v1",
        "strategy_label": "إشارات الموقع حسب الرموز المختارة",
        "signal_source": "site_db",
        "site_signals_db_path": "vip_signals.db",
        "site_signals_limit": 50,
        "site_signals_max_age_minutes": 1,
        "site_signals_min_quality": 70,
        "site_signal_symbols": [],
        "blocked_symbols": [],
        "risk_percent": 1.0,
        "max_risk_percent_of_equity": 1.0,
        "max_risk_usd_per_trade": 0.0,
        "daily_loss_limit_usd": 0.0,
        "daily_loss_limit_percent_of_equity": 3.0,
        "max_consecutive_losses": 3,
        "scan_every_sec": 15,
        "min_score_gap": 24,
        "max_open_positions": 9,
        "max_open_positions_cap": 9,
        "max_trades_per_cycle": 1,
        "max_total_open_risk_percent": 2.0,
        "min_open_positions": 1,
        "one_position_per_symbol": True,
        "cooldown_minutes_per_symbol": 12,
        "pending_entry": False,
        "pending_fallback_to_market": False,
        "market_reprice_entry": True,
        "force_gold_trading_now": False,
        "trading_sessions_utc": [],
        "split_tp": True,
        "tp_execution_mode": "tp3_only",
        "dry_run": False,
        "fixed_volume": 0.0,
        "gold_trend_filter_enabled": True,
        "gold_trend_filter_intervals": ["15m", "30m"],
        "gold_trend_min_gap": 25,
        "gold_trend_fail_open": False,
        "gold_scalping_strategy_enabled": True,
        "gold_scalping_entry_intervals": ["5m"],
        "gold_scalping_context_intervals": ["15m", "30m"],
        "gold_scalping_min_context_agreement": 0,
        "gold_scalping_require_rsi_momentum": False,
        "trailing_stop_enabled": True,
        "trailing_stop_trigger_rr": 0.35,
        "trailing_stop_lock_rr": 0.2,
        "no_loss_after_profit_enabled": True,
    },
    "🏆 XAUUSD TP3 Focus (Best Report)": {
        "strategy_name": "xauusd_tp3_focus_v1",
        "strategy_label": "XAUUSD TP3 Focus",
        "symbols": ["XAUUSD"],
        "blocked_symbols": [
            "BTCUSD", "ETHUSD", "US30", "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
            "AUDUSD", "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "XAGUSD",
        ],
        "intervals": ["5m", "15m", "30m"],
        "risk_percent": 1.0,
        "max_risk_percent_of_equity": 1.0,
        "max_risk_usd_per_trade": 0.0,
        "daily_loss_limit_usd": 0.0,
        "daily_loss_limit_percent_of_equity": 3.0,
        "daily_profit_lock_usd": 0.0,
        "daily_profit_lock_percent_of_equity": 6.0,
        "ignore_consecutive_losses_if_daily_pnl_above_usd": 0.0,
        "ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity": 1.0,
        "max_consecutive_losses": 3,
        "scan_every_sec": 15,
        "min_score_gap": 24,
        "max_open_positions": 1,
        "max_open_positions_cap": 1,
        "max_trades_per_cycle": 1,
        "max_total_open_risk_percent": 2.0,
        "min_open_positions": 1,
        "one_position_per_symbol": True,
        "cooldown_minutes_per_symbol": 12,
        "pending_entry": False,
        "pending_fallback_to_market": False,
        "market_reprice_entry": True,
        "force_gold_trading_now": False,
        "trading_sessions_utc": [
            {"start": "15:00", "end": "21:00", "weekdays": [0, 1, 2]},
        ],
        "gold_trend_filter_enabled": True,
        "gold_trend_filter_intervals": ["15m", "30m"],
        "gold_trend_min_gap": 25,
        "gold_trend_fail_open": False,
        "gold_scalping_strategy_enabled": True,
        "gold_scalping_entry_intervals": ["5m"],
        "gold_scalping_context_intervals": ["15m", "30m"],
        "gold_scalping_min_context_agreement": 0,
        "gold_scalping_require_rsi_momentum": False,
        "split_tp": True,
        "tp_execution_mode": "tp3_only",
        "fixed_volume": 0.0,
        "trailing_stop_enabled": True,
        "trailing_stop_trigger_rr": 0.35,
        "trailing_stop_lock_rr": 0.2,
        "no_loss_after_profit_enabled": True,
    },
    "🚀 Gold Aggressive v3 (XAUUSD)": {
        "strategy_name": "gold_aggressive_v3",
        "symbols": ["XAUUSD"],
        "blocked_symbols": [
            "BTCUSD", "ETHUSD", "US30", "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
            "AUDUSD", "USDCAD", "NZDUSD", "EURGBP", "EURJPY",
        ],
        "intervals": ["5m", "15m", "30m"],
        "risk_percent": 2.0,
        "max_risk_percent_of_equity": 2.0,
        "max_risk_usd_per_trade": 150.0,
        "daily_loss_limit_usd": 300.0,
        "scan_every_sec": 5,
        "min_score_gap": 24,
        "max_open_positions": 3,
        "max_open_positions_cap": 3,
        "max_trades_per_cycle": 3,
        "max_total_open_risk_percent": 10.0,
        "min_open_positions": 1,
        "one_position_per_symbol": False,
        "cooldown_minutes_per_symbol": 0,
        "pending_entry": False,
        "pending_fallback_to_market": False,
        "market_reprice_entry": True,
        "force_gold_trading_now": True,
        "gold_trend_filter_enabled": False,
        "gold_trend_filter_intervals": ["15m", "30m"],
        "gold_trend_fail_open": False,
        "gold_scalping_strategy_enabled": True,
        "gold_scalping_entry_intervals": ["5m"],
        "gold_scalping_context_intervals": ["15m", "30m"],
        "gold_scalping_min_context_agreement": 0,
        "gold_scalping_require_rsi_momentum": False,
        "split_tp": False,
        "trailing_stop_enabled": True,
        "no_loss_after_profit_enabled": True,
    },
    "🛡️ ذهب محافظ - صفقة واحدة": {
        "symbols": ["XAUUSD"],
        "blocked_symbols": ["BTCUSD", "ETHUSD", "US30", "US500"],
        "intervals": ["3m", "5m", "15m"],
        "max_open_positions": 1,
        "max_open_positions_cap": 1,
        "max_trades_per_cycle": 1,
        "one_position_per_symbol": True,
        "cooldown_minutes_per_symbol": 30,
        "pending_entry": False,
        "pending_fallback_to_market": False,
        "market_reprice_entry": True,
        "force_gold_trading_now": False,
        "gold_trend_filter_enabled": True,
        "gold_trend_filter_intervals": ["15m"],
        "gold_trend_fail_open": False,
        "gold_scalping_strategy_enabled": True,
        "gold_scalping_entry_intervals": ["3m", "5m"],
        "gold_scalping_context_intervals": ["15m"],
        "gold_scalping_min_context_agreement": 1,
        "gold_scalping_require_rsi_momentum": True,
        "gold_scalping_rsi_sell_min": 32.0,
        "fixed_volume": 0.01,
    },
    "⚖️ ذهب متوازن مباشر": {
        "symbols": ["XAUUSD"],
        "blocked_symbols": ["BTCUSD", "ETHUSD", "US30"],
        "intervals": ["3m", "5m", "15m"],
        "max_open_positions": 2,
        "max_open_positions_cap": 2,
        "max_trades_per_cycle": 1,
        "one_position_per_symbol": True,
        "cooldown_minutes_per_symbol": 15,
        "pending_entry": False,
        "pending_fallback_to_market": False,
        "market_reprice_entry": True,
        "force_gold_trading_now": False,
        "gold_trend_filter_enabled": True,
        "gold_trend_filter_intervals": ["15m"],
        "gold_trend_fail_open": False,
        "gold_scalping_strategy_enabled": True,
        "gold_scalping_entry_intervals": ["3m", "5m"],
        "gold_scalping_context_intervals": ["15m"],
        "gold_scalping_min_context_agreement": 1,
        "gold_scalping_require_rsi_momentum": True,
        "gold_scalping_rsi_sell_min": 32.0,
    },
    "⚡ ذهب هجومي مباشر": {
        "symbols": ["XAUUSD"],
        "blocked_symbols": ["BTCUSD", "ETHUSD", "US30"],
        "intervals": ["1m", "3m", "5m", "15m"],
        "max_open_positions": 3,
        "max_open_positions_cap": 3,
        "max_trades_per_cycle": 2,
        "one_position_per_symbol": False,
        "cooldown_minutes_per_symbol": 3,
        "pending_entry": False,
        "pending_fallback_to_market": False,
        "market_reprice_entry": True,
        "force_gold_trading_now": False,
        "gold_trend_filter_enabled": True,
        "gold_trend_filter_intervals": ["15m"],
        "gold_trend_fail_open": True,
        "gold_scalping_strategy_enabled": True,
        "gold_scalping_entry_intervals": ["1m", "3m", "5m", "15m"],
        "gold_scalping_context_intervals": ["15m"],
        "gold_scalping_min_context_agreement": 0,
        "gold_scalping_require_rsi_momentum": False,
        "gold_scalping_rsi_sell_min": 25.0,
    },
    "⏳ ذهب بأوامر معلقة": {
        "symbols": ["XAUUSD"],
        "blocked_symbols": ["BTCUSD", "ETHUSD", "US30"],
        "intervals": ["1m", "3m", "5m", "15m"],
        "max_open_positions": 2,
        "max_open_positions_cap": 2,
        "max_trades_per_cycle": 1,
        "one_position_per_symbol": True,
        "cooldown_minutes_per_symbol": 15,
        "pending_entry": True,
        "pending_fallback_to_market": False,
        "pending_expiry_minutes": 5,
        "pending_dedupe_price_tolerance": 1.0,
        "max_pending_orders": 2,
        "market_reprice_entry": False,
        "force_gold_trading_now": False,
        "gold_trend_filter_enabled": True,
        "gold_trend_filter_intervals": ["15m"],
        "gold_trend_fail_open": False,
        "gold_scalping_strategy_enabled": True,
        "gold_scalping_entry_intervals": ["1m", "3m", "5m"],
        "gold_scalping_context_intervals": ["15m"],
        "gold_scalping_min_context_agreement": 1,
        "gold_scalping_require_rsi_momentum": True,
        "gold_scalping_rsi_sell_min": 32.0,
    },
    "🧪 مراقبة فقط بدون تنفيذ": {
        "dry_run": True,
        "pending_entry": False,
        "pending_fallback_to_market": False,
        "market_reprice_entry": True,
        "max_open_positions": 0,
        "max_open_positions_cap": 0,
        "max_trades_per_cycle": 0,
        "one_position_per_symbol": True,
        "gold_scalping_strategy_enabled": True,
    },
}


def detect_execution_mode(config_data: dict) -> str:
    if bool(config_data.get("pending_entry", False)):
        if bool(config_data.get("pending_fallback_to_market", False)):
            return EXECUTION_MODE_PENDING_FALLBACK
        return EXECUTION_MODE_PENDING
    return EXECUTION_MODE_MARKET


def is_site_signal_strategy(config_data: dict) -> bool:
    strategy_name = str(config_data.get("strategy_name") or "").strip().lower()
    signal_source = str(config_data.get("signal_source") or "").strip().lower()
    return strategy_name == "site_db_selected_symbols_v1" or signal_source in {"site_db", "site", "website", "site_signals"}


def detect_strategy_preset(config_data: dict) -> str:
    strategy_name = str(config_data.get("strategy_name") or "").strip().lower()
    if is_site_signal_strategy(config_data):
        return "🌐 إشارات الموقع - الرموز المختارة فقط"
    if strategy_name.endswith("xauusd_tp3_focus_v1") or str(config_data.get("tp_execution_mode") or "").strip().lower() == "tp3_only":
        return "🏆 XAUUSD TP3 Focus (Best Report)"
    if strategy_name in {
        "gold_aggressive_v3",
        "wallet1_gold_aggressive_v3",
        "wallet2_gold_aggressive_v3",
    }:
        return "🚀 Gold Aggressive v3 (XAUUSD)"
    if bool(config_data.get("dry_run", False)):
        return "🧪 مراقبة فقط بدون تنفيذ"
    if bool(config_data.get("pending_entry", False)):
        return "⏳ ذهب بأوامر معلقة"
    if bool(config_data.get("gold_scalping_strategy_enabled", False)) and config_data.get("symbols") == ["XAUUSD"]:
        min_context = int(config_data.get("gold_scalping_min_context_agreement", 1) or 0)
        rsi_momentum = bool(config_data.get("gold_scalping_require_rsi_momentum", True))
        one_symbol = bool(config_data.get("one_position_per_symbol", True))
        max_positions = int(config_data.get("max_open_positions", 0) or 0)
        if min_context <= 0 or not rsi_momentum or not one_symbol:
            return "⚡ ذهب هجومي مباشر"
        if max_positions <= 1:
            return "🛡️ ذهب محافظ - صفقة واحدة"
        return "⚖️ ذهب متوازن مباشر"
    return CUSTOM_PRESET_LABEL


def find_account_trader_pid(account_id: str) -> int:
    """ابحث عن عملية المتداول النشطة لحساب محدد عبر سطر الأوامر."""
    account_id = str(account_id or "").strip()
    if not account_id:
        return 0

    if psutil is None:
        return 0

    target = account_id.lower()
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            joined = " ".join(str(x) for x in cmdline).lower()
            if "continuous_auto_trader.py" in joined and f"--account-id {target}" in joined:
                return int(proc.info.get("pid") or 0)
        except Exception:
            continue
    return 0


def stop_conflicting_traders(target_account_id: str) -> list[int]:
    """أوقف أي عمليات متداول قد تمنع تشغيل الحساب المختار بشكل مستقل.

    - يوقف مشغّل الحسابات المتعددة.
    - يوقف أي continuous_auto_trader لحساب آخر أو بدون --account-id.
    - يترك عملية الحساب المختار كما هي.
    """
    stopped = []
    if psutil is None:
        return stopped

    target = str(target_account_id or "").strip().lower()
    me = os.getpid()
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            pid = int(proc.info.get("pid") or 0)
            if pid <= 0 or pid == me:
                continue
            cmdline = proc.info.get("cmdline") or []
            joined = " ".join(str(x) for x in cmdline).lower()
            if not joined:
                continue

            should_stop = False
            if "run_multi_account_traders.py" in joined:
                should_stop = True
            elif "continuous_auto_trader.py" in joined:
                token = "--account-id "
                idx = joined.find(token)
                if idx >= 0:
                    current_acc = joined[idx + len(token):].split()[0].strip()
                    if current_acc != target:
                        should_stop = True
                else:
                    # عملية قديمة بدون account-id تُعد متعارضة.
                    should_stop = True

            if should_stop:
                proc.terminate()
                try:
                    proc.wait(timeout=4)
                except Exception:
                    proc.kill()
                stopped.append(pid)
        except Exception:
            continue
    return stopped


def probe_wallet_ready(wallet_path: Path, symbols: list[str]) -> dict:
    """يتحقق من جاهزية المحفظة لاستقبال أوامر التداول بدون إرسال أوامر فعلية."""
    try:
        from mt5_bridge import MT5Bridge
    except Exception as exc:
        return {"success": False, "error": f"تعذر تحميل mt5_bridge: {exc}"}

    previous_wallet_config = os.environ.get("MT5_WALLET_CONFIG")
    os.environ["MT5_WALLET_CONFIG"] = str(wallet_path)
    bridge = MT5Bridge()
    try:
        connect_result = bridge.connect()
        if not connect_result.get("success"):
            return {
                "success": False,
                "error": str(connect_result.get("error") or "connect failed"),
                "hint": str(connect_result.get("hint") or ""),
            }

        normalized = bridge.normalize_symbols(symbols[:20])
        if not normalized.get("success"):
            return {
                "success": False,
                "error": str(normalized.get("error") or "normalize symbols failed"),
            }

        items = normalized.get("items") or []
        ok_items = [it for it in items if isinstance(it, dict) and it.get("success")]
        fail_items = [it for it in items if isinstance(it, dict) and not it.get("success")]

        return {
            "success": True,
            "resolved_count": len(ok_items),
            "failed_count": len(fail_items),
            "failed_symbols": [str(it.get("requested_symbol") or "") for it in fail_items],
            "account_login": int((bridge.status().get("account") or {}).get("login") or 0),
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        try:
            bridge.shutdown()
        except Exception:
            pass
        if previous_wallet_config is None:
            os.environ.pop("MT5_WALLET_CONFIG", None)
        else:
            os.environ["MT5_WALLET_CONFIG"] = previous_wallet_config


def load_json(path: Path, fallback):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def resolve_path(raw_value: str, fallback: str) -> Path:
    text = str(raw_value or "").strip() or fallback
    p = Path(text)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def parse_csv_values(text: str):
    return [x.strip().upper().replace("/", "") for x in str(text or "").split(",") if x.strip()]


def parse_intervals(text: str):
    return [x.strip() for x in str(text or "").split(",") if x.strip()]


def clean_text(value) -> str:
    text = str(value or "").strip()
    while len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
        text = text[1:-1].strip()
    return text


def build_trader_launch_command(config_path: Path, state_path: Path, wallet_path: Path, account_id: str) -> list[str]:
    """Build a trader launch command that works in source and frozen desktop builds."""
    account_token = str(account_id or "").strip()
    if IS_FROZEN and TRADER_EXE.exists():
        return [
            str(TRADER_EXE),
            "--config", str(config_path),
            "--state", str(state_path),
            "--wallet-config", str(wallet_path),
            "--account-id", account_token,
        ]

    return [
        sys.executable,
        str(TRADER_SCRIPT),
        "--config", str(config_path),
        "--state", str(state_path),
        "--wallet-config", str(wallet_path),
        "--account-id", account_token,
    ]


class AccountCard:
    def __init__(self, parent, account_row: dict, on_status_change=None):
        self.account_row = account_row
        self.account_id = str(account_row.get("id") or "").strip()
        self.label = str(account_row.get("label") or self.account_id)
        self.enabled_var = tk.BooleanVar(value=bool(account_row.get("enabled", True)))
        self.on_status_change = on_status_change
        self.process = None

        self.wallet_path = resolve_path(account_row.get("wallet"), f"accounts/{self.account_id}/wallet.json")
        self.config_path = resolve_path(account_row.get("config"), f"accounts/{self.account_id}/config.json")
        self.state_path = resolve_path(account_row.get("state"), f"accounts/{self.account_id}/runtime_state.json")
        self.log_path = self.state_path.parent / "trader.out.log"
        self._log_handle = None

        self.wallet_data = load_json(self.wallet_path, {})
        self.config_data = load_json(self.config_path, {})

        # حالة الحساب
        self.status_var = tk.StringVar(value="🔴 متوقف")
        self.status_color_var = tk.StringVar(value="red")

        self.frame = ttk.LabelFrame(parent, text=f"📊 {self.account_id} - {self.label}")
        self.frame.columnconfigure(1, weight=1)
        self.entry_menu = tk.Menu(self.frame, tearoff=0)
        self.entry_menu.add_command(label="قص", command=lambda: self._entry_event("<<Cut>>"))
        self.entry_menu.add_command(label="نسخ", command=lambda: self._entry_event("<<Copy>>"))
        self.entry_menu.add_command(label="لصق", command=lambda: self._entry_event("<<Paste>>"))
        self._active_entry = None

        # الصف الأول: معلومات الحالة
        top_frame = ttk.Frame(self.frame)
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=6)
        top_frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(top_frame, text="مفعّل", variable=self.enabled_var).pack(side="left", padx=4)
        ttk.Label(top_frame, textvariable=self.status_var, font=("Arial", 10, "bold")).pack(side="left", padx=4)
        ttk.Label(top_frame, text=str(self.wallet_path), font=("Arial", 8), foreground="gray").pack(side="left", padx=4)

        self.login_var = tk.StringVar(value=str(self.wallet_data.get("login", "")))
        self.password_var = tk.StringVar(value=str(self.wallet_data.get("password", "")))
        self.server_var = tk.StringVar(value=str(self.wallet_data.get("server", "")))
        self.path_var = tk.StringVar(value=str(self.wallet_data.get("path", "")))
        self.magic_var = tk.StringVar(value=str(self.wallet_data.get("magic", 88001)))

        self.symbols_var = tk.StringVar(value=",".join(self.config_data.get("symbols") or ["XAUUSD", "BTCUSD"]))
        self.intervals_var = tk.StringVar(value=",".join(self.config_data.get("intervals") or ["15m", "1h"]))
        self.risk_pct_var = tk.StringVar(value=str(self.config_data.get("max_risk_percent_of_equity", 1.0)))
        self.daily_loss_var = tk.StringVar(value=str(self.config_data.get("daily_loss_limit_usd", 200.0)))
        self.scan_sec_var = tk.StringVar(value=str(self.config_data.get("scan_every_sec", 20)))
        self.strategy_preset_var = tk.StringVar(value=detect_strategy_preset(self.config_data))
        self.execution_mode_var = tk.StringVar(value=detect_execution_mode(self.config_data))
        self.gold_only_var = tk.BooleanVar(value=(not is_site_signal_strategy(self.config_data) and self.config_data.get("symbols") == ["XAUUSD"]))
        self.dry_run_var = tk.BooleanVar(value=bool(self.config_data.get("dry_run", False)))
        self.force_gold_now_var = tk.BooleanVar(value=bool(self.config_data.get("force_gold_trading_now", False)))
        self.market_reprice_var = tk.BooleanVar(value=bool(self.config_data.get("market_reprice_entry", False)))
        self.gold_scalping_enabled_var = tk.BooleanVar(value=bool(self.config_data.get("gold_scalping_strategy_enabled", False)))
        self.one_position_per_symbol_var = tk.BooleanVar(value=bool(self.config_data.get("one_position_per_symbol", True)))
        self.rsi_momentum_var = tk.BooleanVar(value=bool(self.config_data.get("gold_scalping_require_rsi_momentum", True)))
        self.gold_trend_fail_open_var = tk.BooleanVar(value=bool(self.config_data.get("gold_trend_fail_open", False)))
        self.reset_daily_loss_var = tk.BooleanVar(value=False)
        self.max_positions_var = tk.StringVar(value=str(self.config_data.get("max_open_positions", 1)))
        self.max_trades_cycle_var = tk.StringVar(value=str(self.config_data.get("max_trades_per_cycle", 1)))
        self.cooldown_minutes_var = tk.StringVar(value=str(self.config_data.get("cooldown_minutes_per_symbol", 30)))
        self.fixed_volume_var = tk.StringVar(value=str(self.config_data.get("fixed_volume", 0.0)))
        self.max_risk_usd_var = tk.StringVar(value=str(self.config_data.get("max_risk_usd_per_trade", 0.0)))
        self.blocked_symbols_var = tk.StringVar(value=",".join(self.config_data.get("blocked_symbols") or []))
        self.gold_entry_intervals_var = tk.StringVar(value=",".join(self.config_data.get("gold_scalping_entry_intervals") or ["3m", "5m"]))
        self.gold_context_intervals_var = tk.StringVar(value=",".join(self.config_data.get("gold_scalping_context_intervals") or ["15m"]))
        self.gold_context_agreement_var = tk.StringVar(value=str(self.config_data.get("gold_scalping_min_context_agreement", 1)))

        # أوضاع الوقف المتحرك
        self._TRAILING_MODES = {
            "🔴 معطل": {"enabled": False, "trigger_rr": 1.0, "lock_rr": 0.5},
            "⚡ هجومي  (تفعيل عند 0.7R — قفل 30%)": {"enabled": True, "trigger_rr": 0.7, "lock_rr": 0.3},
            "⚖️ متوازن  (تفعيل عند 1.0R — قفل 50%)": {"enabled": True, "trigger_rr": 1.0, "lock_rr": 0.5},
            "🛡️ محافظ   (تفعيل عند 1.5R — قفل 80%)": {"enabled": True, "trigger_rr": 1.5, "lock_rr": 0.8},
            "✏️ مخصص": None,
        }
        # اكتشاف الوضع الحالي من الكونفيج
        _ts_enabled = bool(self.config_data.get("trailing_stop_enabled", False))
        _ts_trigger = float(self.config_data.get("trailing_stop_trigger_rr", 1.0))
        _ts_lock = float(self.config_data.get("trailing_stop_lock_rr", 0.5))
        _detected_mode = "✏️ مخصص"
        if not _ts_enabled:
            _detected_mode = "🔴 معطل"
        else:
            for _lbl, _vals in self._TRAILING_MODES.items():
                if _vals and _vals["enabled"] and abs(_vals["trigger_rr"] - _ts_trigger) < 0.01 and abs(_vals["lock_rr"] - _ts_lock) < 0.01:
                    _detected_mode = _lbl
                    break
        self.trailing_mode_var = tk.StringVar(value=_detected_mode)
        self.trailing_trigger_var = tk.StringVar(value=str(_ts_trigger))
        self.trailing_lock_var = tk.StringVar(value=str(_ts_lock))

        row = 1
        self._add_entry(row, "🔐 رقم الحساب (MT5 Login)", self.login_var)
        row += 1
        self._add_entry(row, "🔑 كلمة المرور (Password)", self.password_var, show="*")
        row += 1
        self._add_entry(row, "🖥️ الخادم (MT5 Server)", self.server_var)
        row += 1
        self._add_entry(row, "📁 مسار المحطة (Terminal Path)", self.path_var)
        browse = ttk.Button(self.frame, text="استعرض", command=self._browse_terminal)
        browse.grid(row=row, column=2, sticky="w", padx=8, pady=4)
        row += 1
        self._add_entry(row, "✨ Magic Number", self.magic_var)
        row += 1
        self._add_entry(row, "💱 الأزواج (Symbols)", self.symbols_var)
        row += 1
        self._add_entry(row, "⏱️ الفترات الزمنية (Intervals)", self.intervals_var)
        row += 1
        self._add_entry(row, "⚠️ نسبة المخاطرة (Risk %)", self.risk_pct_var)
        row += 1
        self._add_entry(row, "💰 أقصى خسارة يومية (Daily Loss USD)", self.daily_loss_var)
        row += 1
        self._add_entry(row, "🔄 فحص كل (Scan Every Sec)", self.scan_sec_var)
        row += 1

        # ── قسم خيارات الاستراتيجية التي تم اختبارها ─────────────────────────
        sep = ttk.Separator(self.frame, orient="horizontal")
        sep.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
        row += 1
        ttk.Label(self.frame, text="🎛️ خيارات استراتيجية التداول",
                  font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=8, pady=2)
        row += 1
        ttk.Label(self.frame, text="Preset").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        strategy_combo = ttk.Combobox(
            self.frame,
            textvariable=self.strategy_preset_var,
            values=[CUSTOM_PRESET_LABEL] + list(TRADING_PRESETS.keys()),
            state="readonly",
            width=55,
        )
        strategy_combo.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        strategy_combo.bind("<<ComboboxSelected>>", self._on_strategy_preset_change)
        ttk.Button(self.frame, text="تطبيق", command=self._on_strategy_preset_change).grid(row=row, column=2, sticky="w", padx=8, pady=4)
        row += 1
        ttk.Label(self.frame, text="نمط التنفيذ").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        execution_combo = ttk.Combobox(
            self.frame,
            textvariable=self.execution_mode_var,
            values=EXECUTION_MODES,
            state="readonly",
            width=30,
        )
        execution_combo.grid(row=row, column=1, sticky="w", padx=8, pady=4)
        row += 1

        option_frame = ttk.Frame(self.frame)
        option_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8, pady=2)
        ttk.Checkbutton(option_frame, text="ذهب فقط", variable=self.gold_only_var).pack(side="left", padx=6)
        ttk.Checkbutton(option_frame, text="Dry Run", variable=self.dry_run_var).pack(side="left", padx=6)
        ttk.Checkbutton(option_frame, text="تجاوز وقت الذهب الآن", variable=self.force_gold_now_var).pack(side="left", padx=6)
        ttk.Checkbutton(option_frame, text="إعادة تسعير السوق", variable=self.market_reprice_var).pack(side="left", padx=6)
        ttk.Checkbutton(option_frame, text="صفقة واحدة لكل رمز", variable=self.one_position_per_symbol_var).pack(side="left", padx=6)
        row += 1

        filter_frame = ttk.Frame(self.frame)
        filter_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8, pady=2)
        ttk.Checkbutton(filter_frame, text="فلتر سكالبينج الذهب", variable=self.gold_scalping_enabled_var).pack(side="left", padx=6)
        ttk.Checkbutton(filter_frame, text="زخم RSI مطلوب", variable=self.rsi_momentum_var).pack(side="left", padx=6)
        ttk.Checkbutton(filter_frame, text="السماح عند فشل فلتر الاتجاه", variable=self.gold_trend_fail_open_var).pack(side="left", padx=6)
        ttk.Checkbutton(filter_frame, text="تصفير خسائر اليوم عند الحفظ", variable=self.reset_daily_loss_var).pack(side="left", padx=6)
        row += 1

        self._add_entry(row, "🚫 رموز محظورة", self.blocked_symbols_var)
        row += 1
        self._add_entry(row, "📌 أقصى صفقات مفتوحة", self.max_positions_var)
        row += 1
        self._add_entry(row, "🔁 أقصى صفقات في الدورة", self.max_trades_cycle_var)
        row += 1
        self._add_entry(row, "⏳ تبريد الرمز بالدقائق", self.cooldown_minutes_var)
        row += 1
        self._add_entry(row, "📏 حجم ثابت 0=تلقائي", self.fixed_volume_var)
        row += 1
        self._add_entry(row, "💵 أقصى مخاطرة بالدولار 0=تعطيل", self.max_risk_usd_var)
        row += 1
        self._add_entry(row, "⚡ فريمات دخول الذهب", self.gold_entry_intervals_var)
        row += 1
        self._add_entry(row, "🧭 فريمات سياق الذهب", self.gold_context_intervals_var)
        row += 1
        self._add_entry(row, "✅ عدد موافقات السياق", self.gold_context_agreement_var)
        row += 1

        # ── قسم الوقف المتحرك ────────────────────────────────────────────────
        sep = ttk.Separator(self.frame, orient="horizontal")
        sep.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8, pady=4)
        row += 1
        ttk.Label(self.frame, text="📈 وقف الخسارة المتحرك (Trailing Stop)",
                  font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", padx=8, pady=2)
        row += 1
        ttk.Label(self.frame, text="🎚️ الوضع").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        mode_combo = ttk.Combobox(
            self.frame, textvariable=self.trailing_mode_var,
            values=list(self._TRAILING_MODES.keys()), state="readonly", width=55)
        mode_combo.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        mode_combo.bind("<<ComboboxSelected>>", self._on_trailing_mode_change)
        row += 1
        ttk.Label(self.frame, text="🔢 تفعيل عند (Trigger RR)").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        self._trailing_trigger_entry = ttk.Entry(self.frame, textvariable=self.trailing_trigger_var, width=20)
        self._trailing_trigger_entry.grid(row=row, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(self.frame, text="(مثال: 1.0 = عندما يصل الربح لضعف المخاطرة)",
                  foreground="gray").grid(row=row, column=2, sticky="w", padx=4)
        row += 1
        ttk.Label(self.frame, text="🔒 قفل الربح (Lock RR)").grid(row=row, column=0, sticky="w", padx=8, pady=4)
        self._trailing_lock_entry = ttk.Entry(self.frame, textvariable=self.trailing_lock_var, width=20)
        self._trailing_lock_entry.grid(row=row, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(self.frame, text="(مثال: 0.5 = يقفل 50% من الربح الحالي)",
                  foreground="gray").grid(row=row, column=2, sticky="w", padx=4)
        row += 1
        # تطبيق الحالة الأولية على الحقول
        self._on_trailing_mode_change()
        # ────────────────────────────────────────────────────────────────────

        # أزرار التحكم
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8, pady=8)

        self.save_btn = ttk.Button(button_frame, text="💾 حفظ الحساب", command=self.save_account)
        self.save_btn.pack(side="left", padx=4)

        self.start_btn = ttk.Button(button_frame, text="▶️ ابدأ التداول على هذا الحساب", command=self.start_trading)
        self.start_btn.pack(side="left", padx=4)

        self.stop_btn = ttk.Button(button_frame, text="⏹️ إيقاف", command=self.stop_trading, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        self.test_btn = ttk.Button(button_frame, text="🧪 اختبار الاتصال", command=self.test_connection)
        self.test_btn.pack(side="left", padx=4)

    def _add_entry(self, row: int, label: str, var: tk.StringVar, show: str = ""):
        ttk.Label(self.frame, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        entry = ttk.Entry(self.frame, textvariable=var, width=70, show=show)
        entry.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        self._bind_entry_shortcuts(entry)

    def _bind_entry_shortcuts(self, entry: ttk.Entry):
        entry.bind("<Button-3>", self._show_entry_menu)
        entry.bind("<Control-v>", self._paste_into_entry)
        entry.bind("<Control-V>", self._paste_into_entry)
        entry.bind("<Shift-Insert>", self._paste_into_entry)

    def _show_entry_menu(self, event):
        self._active_entry = event.widget
        try:
            self.entry_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.entry_menu.grab_release()
        return "break"

    def _entry_event(self, sequence: str):
        if self._active_entry is not None:
            self._active_entry.focus_set()
            self._active_entry.event_generate(sequence)

    def _paste_into_entry(self, event):
        event.widget.focus_set()
        event.widget.event_generate("<<Paste>>")
        return "break"

    def _on_trailing_mode_change(self, event=None):
        """تحديث حقلي Trigger/Lock بناءً على الوضع المختار، وتمكين/تعطيل التحرير"""
        mode = self.trailing_mode_var.get()
        vals = self._TRAILING_MODES.get(mode)
        if vals is not None:  # وضع محدد مسبقاً
            self.trailing_trigger_var.set(str(vals["trigger_rr"]))
            self.trailing_lock_var.set(str(vals["lock_rr"]))
            self._trailing_trigger_entry.configure(state="disabled")
            self._trailing_lock_entry.configure(state="disabled")
        else:  # مخصص
            self._trailing_trigger_entry.configure(state="normal")
            self._trailing_lock_entry.configure(state="normal")

    def _on_strategy_preset_change(self, event=None):
        preset = TRADING_PRESETS.get(self.strategy_preset_var.get())
        if not preset:
            return

        keep_user_symbols = is_site_signal_strategy(preset)
        current_symbols = parse_csv_values(self.symbols_var.get())
        current_intervals = parse_intervals(self.intervals_var.get())
        for preset_key, preset_value in preset.items():
            self.config_data[preset_key] = list(preset_value) if isinstance(preset_value, list) else preset_value

        if keep_user_symbols:
            self.config_data["symbols"] = current_symbols
            self.config_data["intervals"] = current_intervals
            self.config_data["site_signal_symbols"] = []

        if "tp_execution_mode" not in preset:
            self.config_data["tp_execution_mode"] = "single" if preset.get("split_tp") is False else "split"

        if "symbols" in preset and not keep_user_symbols:
            self.symbols_var.set(",".join(preset.get("symbols") or []))
            self.gold_only_var.set(False if is_site_signal_strategy(preset) else preset.get("symbols") == ["XAUUSD"])
        elif keep_user_symbols:
            self.gold_only_var.set(False)
        if "blocked_symbols" in preset:
            self.blocked_symbols_var.set(",".join(preset.get("blocked_symbols") or []))
        if "intervals" in preset and not keep_user_symbols:
            self.intervals_var.set(",".join(preset.get("intervals") or []))
        if "gold_scalping_entry_intervals" in preset:
            self.gold_entry_intervals_var.set(",".join(preset.get("gold_scalping_entry_intervals") or []))
        if "gold_scalping_context_intervals" in preset:
            self.gold_context_intervals_var.set(",".join(preset.get("gold_scalping_context_intervals") or []))

        if bool(preset.get("pending_entry", False)):
            self.execution_mode_var.set(
                EXECUTION_MODE_PENDING_FALLBACK
                if bool(preset.get("pending_fallback_to_market", False))
                else EXECUTION_MODE_PENDING
            )
        else:
            self.execution_mode_var.set(EXECUTION_MODE_MARKET)

        if "dry_run" in preset:
            self.dry_run_var.set(bool(preset.get("dry_run")))
        if "force_gold_trading_now" in preset:
            self.force_gold_now_var.set(bool(preset.get("force_gold_trading_now")))
        if "market_reprice_entry" in preset:
            self.market_reprice_var.set(bool(preset.get("market_reprice_entry")))
        if "gold_scalping_strategy_enabled" in preset:
            self.gold_scalping_enabled_var.set(bool(preset.get("gold_scalping_strategy_enabled")))
        if "one_position_per_symbol" in preset:
            self.one_position_per_symbol_var.set(bool(preset.get("one_position_per_symbol")))
        if "gold_scalping_require_rsi_momentum" in preset:
            self.rsi_momentum_var.set(bool(preset.get("gold_scalping_require_rsi_momentum")))
        if "gold_trend_fail_open" in preset:
            self.gold_trend_fail_open_var.set(bool(preset.get("gold_trend_fail_open")))

        if "max_open_positions" in preset:
            self.max_positions_var.set(str(preset.get("max_open_positions")))
        if "max_trades_per_cycle" in preset:
            self.max_trades_cycle_var.set(str(preset.get("max_trades_per_cycle")))
        if "cooldown_minutes_per_symbol" in preset:
            self.cooldown_minutes_var.set(str(preset.get("cooldown_minutes_per_symbol")))
        if "fixed_volume" in preset:
            self.fixed_volume_var.set(str(preset.get("fixed_volume")))
        if "max_risk_usd_per_trade" in preset:
            self.max_risk_usd_var.set(str(preset.get("max_risk_usd_per_trade")))
        if "gold_scalping_min_context_agreement" in preset:
            self.gold_context_agreement_var.set(str(preset.get("gold_scalping_min_context_agreement")))
        if "max_risk_percent_of_equity" in preset:
            self.risk_pct_var.set(str(preset.get("max_risk_percent_of_equity")))
        if "daily_loss_limit_usd" in preset:
            self.daily_loss_var.set(str(preset.get("daily_loss_limit_usd")))
        if "scan_every_sec" in preset:
            self.scan_sec_var.set(str(preset.get("scan_every_sec")))

    def _browse_terminal(self):
        path = filedialog.askopenfilename(
            title="اختر terminal64.exe",
            filetypes=[("Executable", "*.exe"), ("جميع الملفات", "*.*")],
        )
        if path:
            self.path_var.set(path)

    def collect_account_payload(self):
        wallet_data = dict(self.wallet_data)
        config_data = dict(self.config_data)

        wallet_data["enabled"] = bool(self.enabled_var.get())
        wallet_data["allow_trading"] = True
        wallet_data["allow_site_signals"] = True
        wallet_data["auto_execution_enabled"] = True
        wallet_data["login"] = int(self.login_var.get().strip() or "0")
        wallet_data["password"] = clean_text(self.password_var.get())
        wallet_data["server"] = clean_text(self.server_var.get())
        wallet_data["path"] = clean_text(self.path_var.get())
        wallet_data["magic"] = int(self.magic_var.get().strip() or "88001")
        wallet_data.setdefault("deviation", 20)
        wallet_data.setdefault("default_volume", 0.01)

        config_data["enabled"] = bool(self.enabled_var.get())
        site_signal_mode = is_site_signal_strategy(config_data)
        if bool(self.gold_only_var.get()) and not site_signal_mode:
            self.symbols_var.set("XAUUSD")
        selected_symbols = parse_csv_values(self.symbols_var.get())
        if not selected_symbols and not site_signal_mode:
            selected_symbols = ["XAUUSD", "BTCUSD"]
        wallet_data["auto_execution_symbols"] = selected_symbols
        config_data["symbols"] = selected_symbols
        if site_signal_mode:
            config_data["signal_source"] = "site_db"
            config_data["site_signal_symbols"] = []
        config_data["blocked_symbols"] = parse_csv_values(self.blocked_symbols_var.get())
        config_data["intervals"] = parse_intervals(self.intervals_var.get()) or ["15m", "1h"]
        risk_percent = float(self.risk_pct_var.get().strip() or "1.0")
        config_data["risk_percent"] = risk_percent
        config_data["max_risk_percent_of_equity"] = risk_percent
        config_data["daily_loss_limit_usd"] = float(self.daily_loss_var.get().strip() or "200")
        config_data["scan_every_sec"] = int(self.scan_sec_var.get().strip() or "20")

        execution_mode = self.execution_mode_var.get()
        config_data["dry_run"] = bool(self.dry_run_var.get())
        config_data["pending_entry"] = execution_mode in (EXECUTION_MODE_PENDING, EXECUTION_MODE_PENDING_FALLBACK)
        config_data["pending_fallback_to_market"] = execution_mode == EXECUTION_MODE_PENDING_FALLBACK
        config_data["market_reprice_entry"] = bool(self.market_reprice_var.get())
        config_data["force_gold_trading_now"] = bool(self.force_gold_now_var.get())
        config_data["one_position_per_symbol"] = bool(self.one_position_per_symbol_var.get())
        max_positions = max(0, int(self.max_positions_var.get().strip() or "0"))
        config_data["max_open_positions"] = max_positions
        config_data["max_open_positions_cap"] = max_positions
        config_data["max_trades_per_cycle"] = max(0, int(self.max_trades_cycle_var.get().strip() or "0"))
        config_data["cooldown_minutes_per_symbol"] = max(0, int(self.cooldown_minutes_var.get().strip() or "0"))
        config_data["fixed_volume"] = max(0.0, float(self.fixed_volume_var.get().strip() or "0"))
        config_data["max_risk_usd_per_trade"] = max(0.0, float(self.max_risk_usd_var.get().strip() or "0"))
        config_data["gold_scalping_strategy_enabled"] = bool(self.gold_scalping_enabled_var.get())
        config_data["gold_scalping_entry_intervals"] = parse_intervals(self.gold_entry_intervals_var.get()) or ["3m", "5m"]
        config_data["gold_scalping_context_intervals"] = parse_intervals(self.gold_context_intervals_var.get()) or ["15m"]
        config_data["gold_scalping_min_context_agreement"] = max(0, int(self.gold_context_agreement_var.get().strip() or "1"))
        config_data["gold_scalping_require_rsi_momentum"] = bool(self.rsi_momentum_var.get())
        config_data["gold_trend_filter_enabled"] = True
        config_data["gold_trend_filter_intervals"] = parse_intervals(self.gold_context_intervals_var.get()) or ["15m"]
        config_data["gold_trend_fail_open"] = bool(self.gold_trend_fail_open_var.get())
        config_data.setdefault("gold_scalping_context_min_ema_gap_percent", 0.01)
        config_data.setdefault("gold_scalping_min_entry_score_gap", 35)
        config_data.setdefault("gold_scalping_rsi_buy_min", 38.0)
        config_data.setdefault("gold_scalping_rsi_buy_max", 68.0)
        config_data.setdefault("gold_scalping_rsi_sell_min", 32.0)
        config_data.setdefault("gold_scalping_rsi_sell_max", 62.0)
        config_data.setdefault("gold_scalping_max_entry_distance_atr", 1.4)
        config_data.setdefault("gold_scalping_min_volume_ratio", 0.8)
        config_data.setdefault("gold_scalping_skip_bollinger_extreme", True)
        config_data.setdefault("gold_scalping_atr_reference_interval", "5m")
        config_data.setdefault("gold_scalping_stop_atr_multiplier", 1.0)
        config_data.setdefault("gold_scalping_tp1_rr", 1.0)
        config_data.setdefault("gold_scalping_tp2_rr", 1.5)
        config_data.setdefault("gold_scalping_tp3_rr", 2.0)
        config_data.setdefault("cancel_expired_pending", True)
        config_data.setdefault("pending_expiry_minutes", 5)
        config_data.setdefault("pending_dedupe_price_tolerance", 1.0)
        if bool(self.reset_daily_loss_var.get()):
            reset_text = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            config_data["daily_loss_reset_at_utc"] = reset_text

        # الوقف المتحرك
        mode = self.trailing_mode_var.get()
        vals = self._TRAILING_MODES.get(mode)
        if vals is not None:
            config_data["trailing_stop_enabled"] = bool(vals["enabled"])
            config_data["trailing_stop_trigger_rr"] = float(vals["trigger_rr"])
            config_data["trailing_stop_lock_rr"] = float(vals["lock_rr"])
        else:  # مخصص
            config_data["trailing_stop_enabled"] = True
            config_data["trailing_stop_trigger_rr"] = float(self.trailing_trigger_var.get().strip() or "1.0")
            config_data["trailing_stop_lock_rr"] = float(self.trailing_lock_var.get().strip() or "0.5")
        config_data["trailing_stop_breakeven"] = True

        config_data.setdefault("use_equity_for_risk", True)
        config_data.setdefault("allow_normal_signals", True)
        config_data.setdefault("allow_strong_signals", True)
        config_data.setdefault("split_tp", True)
        return wallet_data, config_data

    def save_account(self, silent: bool = False):
        """حفظ إعدادات الحساب فقط بدون تشغيل"""
        try:
            wallet_data, config_data = self.collect_account_payload()
            save_json(self.wallet_path, wallet_data)
            save_json(self.config_path, config_data)
            self.wallet_data = wallet_data
            self.config_data = config_data
            self.reset_daily_loss_var.set(False)
            if not silent:
                messagebox.showinfo("✅ تم الحفظ", f"تم حفظ إعدادات الحساب {self.account_id} بنجاح")
            return True
        except Exception as exc:
            if not silent:
                messagebox.showerror("❌ خطأ في الحفظ", str(exc))
            else:
                raise
            return False

    def start_trading(self):
        """حفظ وبدء التداول على هذا الحساب"""
        try:
            # حفظ الإعدادات أولاً
            self.save_account(silent=True)

            # وضع تشغيل حساب مفرد: أوقف العمليات المتعارضة أولاً.
            stopped_pids = stop_conflicting_traders(self.account_id)

            # إن كانت العملية تعمل مسبقًا لنفس الحساب، اعرض الحالة بدل تشغيل نسخة ثانية.
            existing_pid = find_account_trader_pid(self.account_id)
            if existing_pid > 0:
                self._update_status(f"🟢 يعمل مسبقاً (PID: {existing_pid})", "green")
                self.start_btn.config(state="disabled")
                self.stop_btn.config(state="normal")
                messagebox.showinfo("ℹ️ الحساب يعمل", f"الحساب {self.account_id} يعمل مسبقاً\nPID: {existing_pid}")
                return

            # التحقق من المعلومات الأساسية
            if not self.wallet_data.get("login"):
                messagebox.showerror("❌ بيانات ناقصة", "يرجى إدخال رقم الحساب (Login)")
                return
            if not self.wallet_data.get("password"):
                messagebox.showerror("❌ بيانات ناقصة", "يرجى إدخال كلمة المرور")
                return
            if not self.wallet_data.get("server"):
                messagebox.showerror("❌ بيانات ناقصة", "يرجى إدخال اسم الخادم")
                return
            if not self.wallet_data.get("path"):
                messagebox.showerror("❌ بيانات ناقصة", "يرجى إدخال مسار المحطة")
                return

            # بناء أمر التشغيل
            cmd = build_trader_launch_command(
                config_path=self.config_path,
                state_path=self.state_path,
                wallet_path=self.wallet_path,
                account_id=self.account_id,
            )

            env = dict(os.environ)
            env["AUTO_TRADER_ACCOUNT_ID"] = self.account_id
            env["MT5_WALLET_CONFIG"] = str(self.wallet_path)
            env.setdefault("PYTHONUTF8", "1")

            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = open(self.log_path, "a", encoding="utf-8", buffering=1)
            self._log_handle.write(f"\n===== [{self.account_id}] start {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")

            # تشغيل العملية
            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

            self.process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                creationflags=creationflags,
                env=env,
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
            )

            # تحقق سريع: إن خرجت العملية مباشرة، اعرض آخر سطر خطأ واضح للمستخدم.
            time.sleep(1.0)
            exit_code = self.process.poll()
            if exit_code is not None:
                self._update_status("🔴 فشل البدء", "red")
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
                try:
                    tail = ""
                    if self.log_path.exists():
                        lines = self.log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                        tail = "\n".join(lines[-6:])
                    raise RuntimeError(f"خرجت العملية مباشرة (code={exit_code})\n{tail}")
                finally:
                    self.process = None
                    if self._log_handle is not None:
                        try:
                            self._log_handle.close()
                        except Exception:
                            pass
                        self._log_handle = None

            # تحديث الحالة
            self._update_status(f"🟢 يعمل (PID: {self.process.pid})", "green")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")

            extra = ""
            if stopped_pids:
                extra = f"\n\nتم إيقاف عمليات متعارضة: {', '.join(str(x) for x in stopped_pids)}"
            messagebox.showinfo("✅ بدء التداول", f"بدأ التداول على الحساب {self.account_id}\nPID: {self.process.pid}{extra}")
        except Exception as exc:
            messagebox.showerror("❌ خطأ", f"فشل بدء التداول: {str(exc)}")

    def test_connection(self):
        """اختبار اتصال المحفظة وجاهزية استقبال الأوامر."""
        try:
            self.save_account(silent=True)
            symbols = parse_csv_values(self.symbols_var.get()) or ["XAUUSD", "BTCUSD"]
            result = probe_wallet_ready(self.wallet_path, symbols)
            if not result.get("success"):
                self._update_status("🔴 فشل الاختبار", "red")
                err = str(result.get("error") or "unknown error")
                hint = str(result.get("hint") or "")
                msg = f"فشل اختبار الحساب {self.account_id}\n\nالسبب: {err}"
                if hint:
                    msg += f"\n\nتلميح: {hint}"
                messagebox.showerror("❌ اختبار الاتصال", msg)
                return

            resolved_count = int(result.get("resolved_count") or 0)
            failed_count = int(result.get("failed_count") or 0)
            login_value = int(result.get("account_login") or 0)
            failed_symbols = result.get("failed_symbols") or []
            self._update_status("🟢 جاهز لاستقبال الأوامر", "green")

            msg = (
                f"نجح اختبار الحساب {self.account_id}\n"
                f"Login فعلي: {login_value}\n"
                f"رموز صالحة: {resolved_count}\n"
                f"رموز غير متاحة: {failed_count}"
            )
            if failed_symbols:
                msg += f"\n\nغير المتاح: {', '.join(failed_symbols)}"
            messagebox.showinfo("✅ اختبار الاتصال", msg)
        except Exception as exc:
            self._update_status("🔴 خطأ في الاختبار", "red")
            messagebox.showerror("❌ اختبار الاتصال", str(exc))

    def stop_trading(self):
        """إيقاف التداول على هذا الحساب"""
        # إذا لم تكن العملية منطلقة من هذه الواجهة، حاول إيقافها عبر PID المكتشف للحساب.
        if (not self.process or self.process.poll() is not None):
            existing_pid = find_account_trader_pid(self.account_id)
            if existing_pid > 0:
                try:
                    if psutil is not None:
                        p = psutil.Process(existing_pid)
                        p.terminate()
                        try:
                            p.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            p.kill()
                    self._update_status("🔴 متوقف", "red")
                    self.start_btn.config(state="normal")
                    self.stop_btn.config(state="disabled")
                    messagebox.showinfo("✅ تم الإيقاف", f"تم إيقاف الحساب {self.account_id} (PID: {existing_pid})")
                    return
                except Exception as exc:
                    messagebox.showerror("❌ خطأ", f"فشل إيقاف العملية الحالية: {exc}")
                    return

            messagebox.showwarning("⚠️ تنبيه", "العملية غير مفعّلة")
            self._update_status("🔴 متوقف", "red")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            return

        try:
            if os.name == "nt":
                self.process.send_signal(getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
            else:
                self.process.terminate()

            self.process.wait(timeout=5)
            self._update_status("🔴 متوقف", "red")
            messagebox.showinfo("✅ تم الإيقاف", f"تم إيقاف التداول على الحساب {self.account_id}")
        except subprocess.TimeoutExpired:
            self.process.kill()
            self._update_status("🔴 متوقف (إجباري)", "red")
            messagebox.showwarning("⚠️ تنبيه", "تم إيقاف العملية بشكل إجباري")
        except Exception as exc:
            messagebox.showerror("❌ خطأ", f"فشل الإيقاف: {str(exc)}")

        self.process = None
        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except Exception:
                pass
            self._log_handle = None
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _update_status(self, text: str, color: str):
        """تحديث حالة الحساب"""
        self.status_var.set(text)
        self.status_color_var.set(color)
        if self.on_status_change:
            self.on_status_change()


class MultiTraderGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🚀 نظام التداول متعدد المحافظ - Multi Account Trader")
        self.geometry("1120x800")
        self.runner_proc = None
        self.single_mode_only = True

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Button(top, text="🔄 تحديث", command=self.reload_accounts).pack(side="left", padx=4)
        ttk.Button(top, text="💾 حفظ الكل", command=self.save_all).pack(side="left", padx=4)
        ttk.Button(top, text="🧪 فحص جاهزية المحافظ", command=self.validate_all_wallets).pack(side="left", padx=4)
        ttk.Button(top, text="🚫 تشغيل الكل (معطل)", command=self.start_runner).pack(side="left", padx=4)
        ttk.Button(top, text="📁 فتح مجلد المحافظ", command=self.open_accounts_folder).pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="✅ جاهز")
        ttk.Label(top, textvariable=self.status_var).pack(side="right", padx=4)

        self.canvas = tk.Canvas(self, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.container = ttk.Frame(self.canvas)
        self.container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width),
        )

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.cards = []
        self.reload_accounts()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def reload_accounts(self):
        """إعادة تحميل جميع الحسابات من ملف الإعدادات"""
        for widget in self.container.winfo_children():
            widget.destroy()
        self.cards = []

        registry = load_json(REGISTRY_PATH, {})
        rows = registry.get("accounts") if isinstance(registry, dict) else []
        if not isinstance(rows, list):
            rows = []

        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            card = AccountCard(self.container, row, on_status_change=self.on_account_status_change)
            card.frame.pack(fill="x", padx=8, pady=6)
            self.cards.append(card)

        self.status_var.set(f"✅ تم تحميل {len(self.cards)} حساب")

    def on_account_status_change(self):
        """عند تغيير حالة أي حساب"""
        pass

    def save_all(self, silent: bool = False):
        """حفظ جميع الحسابات"""
        try:
            for card in self.cards:
                card.save_account(silent=True)

            registry = load_json(REGISTRY_PATH, {})
            rows = registry.get("accounts") if isinstance(registry, dict) else []
            if isinstance(rows, list):
                by_id = {card.account_id: card for card in self.cards}
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    account_id = str(row.get("id") or "").strip()
                    card = by_id.get(account_id)
                    if card:
                        row["enabled"] = bool(card.enabled_var.get())
                save_json(REGISTRY_PATH, registry)

            self.status_var.set("✅ تم حفظ جميع الحسابات")
            if not silent:
                messagebox.showinfo("✅ تم الحفظ", "تم تحديث ملفات جميع الحسابات بنجاح")
            return True
        except Exception as exc:
            if not silent:
                messagebox.showerror("❌ خطأ في الحفظ", str(exc))
            else:
                raise
            return False

    def validate_all_wallets(self):
        """فحص جميع المحافظ المفعلة والتأكد أنها جاهزة لاستقبال الأوامر."""
        try:
            self.save_all(silent=True)
            total_enabled = 0
            ok_count = 0
            failed_rows = []

            for card in self.cards:
                if not bool(card.enabled_var.get()):
                    continue
                total_enabled += 1
                symbols = parse_csv_values(card.symbols_var.get()) or ["XAUUSD", "BTCUSD"]
                result = probe_wallet_ready(card.wallet_path, symbols)
                if result.get("success"):
                    ok_count += 1
                    card._update_status("🟢 جاهز لاستقبال الأوامر", "green")
                else:
                    card._update_status("🔴 غير جاهز", "red")
                    failed_rows.append(f"{card.account_id}: {result.get('error')}")

            if total_enabled == 0:
                messagebox.showwarning("⚠️ فحص المحافظ", "لا توجد محافظ مفعّلة للفحص")
                self.status_var.set("⚠️ لا توجد محافظ مفعّلة")
                return

            if not failed_rows:
                self.status_var.set(f"✅ جميع المحافظ جاهزة ({ok_count}/{total_enabled})")
                messagebox.showinfo(
                    "✅ فحص المحافظ",
                    f"كل المحافظ المفعّلة جاهزة لاستقبال الأوامر\nالنتيجة: {ok_count}/{total_enabled}",
                )
                return

            self.status_var.set(f"⚠️ محافظ غير جاهزة ({ok_count}/{total_enabled})")
            details = "\n".join(failed_rows[:12])
            if len(failed_rows) > 12:
                details += f"\n... +{len(failed_rows) - 12} أخرى"
            messagebox.showwarning(
                "⚠️ فحص المحافظ",
                f"بعض المحافظ غير جاهزة لاستقبال الأوامر\nالجاهز: {ok_count}/{total_enabled}\n\n{details}",
            )
        except Exception as exc:
            messagebox.showerror("❌ فحص المحافظ", str(exc))

    def start_runner(self):
        """تشغيل جميع المحافظ المفعّلة معاً"""
        if self.single_mode_only:
            self.status_var.set("🔒 وضع المحفظة المفردة فقط")
            messagebox.showinfo(
                "🔒 وضع التشغيل",
                "تشغيل الكل معطّل حسب الإعداد الحالي.\n\n"
                "استخدم زر (ابدأ التداول على هذا الحساب) داخل بطاقة المحفظة المطلوبة فقط.",
            )
            return

        if self.runner_proc and self.runner_proc.poll() is None:
            self.status_var.set(f"⚠️ المتعدد يعمل بالفعل (pid={self.runner_proc.pid})")
            return

        self.save_all(silent=True)
        cmd = [sys.executable, str(RUNNER_SCRIPT), "--registry", str(REGISTRY_PATH)]
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        self.runner_proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), creationflags=creationflags)
        self.status_var.set(f"🟢 المتعدد يعمل (pid={self.runner_proc.pid})")

    def stop_runner(self):
        """إيقاف تشغيل المتعدد"""
        if self.single_mode_only:
            self.status_var.set("🔒 وضع المحفظة المفردة فقط")
            return

        if not self.runner_proc or self.runner_proc.poll() is not None:
            self.status_var.set("🔴 المتعدد متوقف")
            return
        try:
            if os.name == "nt":
                self.runner_proc.send_signal(getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
            else:
                self.runner_proc.terminate()
        except Exception:
            try:
                self.runner_proc.kill()
            except Exception:
                pass
        self.status_var.set("⚠️ تم إرسال إشارة الإيقاف للمتعدد")

    def open_accounts_folder(self):
        """فتح مجلد المحافظ"""
        path = str(PROJECT_ROOT / "accounts")
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            messagebox.showinfo("📁 مسار المحافظ", path)

    def on_close(self):
        """عند إغلاق البرنامج"""
        try:
            self.stop_runner()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = MultiTraderGui()
    app.mainloop()
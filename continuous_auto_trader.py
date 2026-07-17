import argparse
import atexit
import json
import math
import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

def app_root() -> Path:
    if bool(getattr(sys, "frozen", False)):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PROJECT_ROOT = app_root()
APP_ROOT = PROJECT_ROOT / "my-forex-app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from services.advanced_analyzer_engine import SUPPORTED_INTERVALS, SUPPORTED_SYMBOLS, perform_full_analysis
from mt5_bridge import MT5Bridge, mt5


<<<<<<< Updated upstream
_SINGLE_INSTANCE_LOCK_PATH: str | None = None
_SINGLE_INSTANCE_LOCK_OWNER = False


def _release_single_instance_lock() -> None:
    global _SINGLE_INSTANCE_LOCK_OWNER
    if not _SINGLE_INSTANCE_LOCK_OWNER:
        return
    try:
        if _SINGLE_INSTANCE_LOCK_PATH and Path(_SINGLE_INSTANCE_LOCK_PATH).exists():
            Path(_SINGLE_INSTANCE_LOCK_PATH).unlink(missing_ok=True)
    except Exception:
        pass
    _SINGLE_INSTANCE_LOCK_OWNER = False


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return False
    return True


def acquire_single_instance_lock() -> bool:
    global _SINGLE_INSTANCE_LOCK_PATH
    global _SINGLE_INSTANCE_LOCK_OWNER

    account_id = os.environ.get("AUTO_TRADER_ACCOUNT_ID", "").strip()
    safe_account_id = re.sub(r"[^A-Za-z0-9_.-]", "_", account_id) if account_id else ""
    lock_name = f"continuous_auto_trader.{safe_account_id}.lock" if safe_account_id else "continuous_auto_trader.lock"
    lock_path = PROJECT_ROOT / lock_name
    lock_path_str = str(lock_path)
    _SINGLE_INSTANCE_LOCK_PATH = lock_path_str

    def _try_create_lock() -> bool:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(lock_path_str, flags)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True

    try:
        _try_create_lock()
        _SINGLE_INSTANCE_LOCK_OWNER = True
        atexit.register(_release_single_instance_lock)
        return True
    except FileExistsError:
        try:
            existing_pid = int(lock_path.read_text(encoding="utf-8").strip() or "0")
        except Exception:
            existing_pid = 0

        if _is_pid_running(existing_pid):
            return False

        try:
            age_sec = time.time() - lock_path.stat().st_mtime
        except Exception:
            age_sec = 0
        if age_sec < 120:
            return False

        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            return False

        try:
            _try_create_lock()
            _SINGLE_INSTANCE_LOCK_OWNER = True
            atexit.register(_release_single_instance_lock)
            return True
        except Exception:
            return False
    except Exception:
        return False
=======
TRADE_ANALYSIS_SOURCE = "advanced_analyzer"
TRADE_ANALYSIS_ENGINE = "services.advanced_analyzer_engine.perform_full_analysis"
>>>>>>> Stashed changes


DEFAULT_CONFIG = {
    "enabled": True,
    "analysis_source": TRADE_ANALYSIS_SOURCE,
    "analysis_engine": TRADE_ANALYSIS_ENGINE,
    "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"],
    "blocked_symbols": [],
    "intervals": ["1h", "4h"],
    "risk_percent": 1.0,
    "fixed_volume": 0.0,
    "use_equity_for_risk": True,
    "max_risk_usd_per_trade": 8.0,
    "max_risk_percent_of_equity": 0.8,
    "max_stop_distance_percent": 1.2,
    "max_target_distance_percent": 3.5,
    "min_rr_ratio": 1.1,
    "scan_every_sec": 60,
    "min_score_gap": 18,
    "allow_normal_signals": True,
    "allow_strong_signals": True,
    "strong_pending_only": False,
    "max_open_positions": 0,
    "dynamic_max_positions_enabled": True,
    "max_total_open_risk_percent": 2.1,
    "min_open_positions": 3,
    "max_open_positions_cap": 24,
    "one_position_per_symbol": True,
    "cooldown_minutes_per_symbol": 90,
    "pending_entry": False,
    "pending_fallback_to_market": True,
    "max_pending_orders": 0,
    "pending_dedupe_price_tolerance": 0.0,
    "cancel_expired_pending": True,
    "pending_expiry_minutes": 180,
    "market_reprice_entry": False,
    "max_market_entry_drift_percent": 0.6,
    "tick_confirmation_enabled": False,
    "tick_confirmation_samples": 3,
    "tick_confirmation_sample_delay_ms": 250,
    "tick_confirmation_min_move_points": 1.0,
    "tick_confirmation_require_direction": True,
    "tick_confirmation_max_tick_age_sec": 5.0,
    "tick_confirmation_max_spread_to_stop": 0.18,
    "cancel_on_market_invalidation": True,
    "split_tp": True,
    "tp_execution_mode": "split",
    "trading_sessions_utc": [{"start": "06:00", "end": "22:00", "weekdays": [0, 1, 2, 3, 4]}],
    "daily_loss_limit_usd": 25.0,
    "daily_loss_limit_percent_of_equity": 0.0,
<<<<<<< Updated upstream
    "daily_loss_limit_follow_risk_percent": True,
=======
>>>>>>> Stashed changes
    "max_consecutive_losses": 3,
    "daily_profit_lock_usd": 0.0,
    "daily_profit_lock_percent_of_equity": 0.0,
    "ignore_consecutive_losses_if_daily_pnl_above_usd": 0.0,
    "ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity": 0.0,
    "interval_loss_freeze_enabled": True,
    "interval_loss_freeze_after": 2,
    "interval_loss_freeze_minutes": 180,
    "interval_loss_freeze_scope": "interval",
    "gold_trend_filter_enabled": True,
    "gold_trend_filter_intervals": ["1h", "4h"],
    "gold_trend_min_gap": 20,
    "gold_trend_override_score_gap": 75,
    "gold_trend_fail_open": False,
    "ema_trend_filter_enabled": False,
    "ema_trend_interval": "4h",
    "ema_trend_fast_key": "ema50",
    "ema_trend_slow_key": "ema200",
    "ema_trend_require_order": True,
    "ema_trend_override_score_gap": 0,
    "bos_retest_filter_enabled": False,
    "bos_retest_entry_intervals": ["5m", "15m"],
    "bos_retest_break_buffer_atr": 0.05,
    "bos_retest_retest_tolerance_atr": 0.35,
    "bos_retest_require_candle_confirmation": True,
    "bos_retest_fail_open": False,
    "gold_scalping_strategy_enabled": False,
    "gold_scalping_entry_intervals": ["1m", "3m", "5m"],
    "gold_scalping_context_intervals": ["15m"],
    "gold_scalping_min_context_agreement": 1,
    "gold_scalping_context_min_ema_gap_percent": 0.01,
    "gold_scalping_min_entry_score_gap": 35,
    "gold_scalping_rsi_buy_min": 38.0,
    "gold_scalping_rsi_buy_max": 68.0,
    "gold_scalping_rsi_sell_min": 32.0,
    "gold_scalping_rsi_sell_max": 62.0,
    "gold_scalping_require_rsi_momentum": True,
    "gold_scalping_max_entry_distance_atr": 1.4,
    "gold_scalping_min_volume_ratio": 0.8,
    "gold_scalping_skip_bollinger_extreme": True,
    "gold_scalping_atr_reference_interval": "5m",
    "gold_scalping_stop_atr_multiplier": 1.0,
    "gold_scalping_min_stop_price_distance": 3.0,
    "gold_scalping_max_stop_price_distance": 12.0,
    "gold_scalping_tp1_rr": 1.0,
    "gold_scalping_tp2_rr": 1.5,
    "gold_scalping_tp3_rr": 2.0,
    "gold_scalping_max_spread_to_stop": 0.18,
    "gold_fixed_tp_after_spread_points": 0.0,
    "min_rr_ratio_fixed_tp": 0.0,
    "no_loss_after_profit_enabled": True,
    "no_loss_after_profit_trigger_rr": 0.05,
    "no_loss_after_profit_buffer_rr": 0.02,
    "tp_step_guard_enabled": True,
    "tp1_trigger_rr": 1.0,
    "tp1_lock_rr": 0.5,
    "tp2_trigger_rr": 2.0,
    "tp2_lock_rr": 1.5,
    "tp3_trigger_rr": 3.0,
    "tp3_lock_rr": 2.5,
    "forex_scalping_strategy_enabled": False,
    "forex_scalping_entry_intervals": ["1m", "3m", "5m"],
    "forex_scalping_context_intervals": ["15m"],
    "forex_scalping_min_context_agreement": 1,
    "forex_scalping_context_min_ema_gap_percent": 0.005,
    "forex_scalping_min_entry_score_gap": 35,
    "forex_scalping_rsi_buy_min": 38.0,
    "forex_scalping_rsi_buy_max": 68.0,
    "forex_scalping_rsi_sell_min": 32.0,
    "forex_scalping_rsi_sell_max": 62.0,
    "forex_scalping_require_rsi_momentum": True,
    "forex_scalping_max_entry_distance_atr": 1.6,
    "forex_scalping_min_volume_ratio": 0.0,
    "forex_scalping_skip_bollinger_extreme": True,
    "forex_scalping_atr_reference_interval": "5m",
    "forex_scalping_stop_atr_multiplier": 0.9,
    "forex_scalping_min_stop_price_distance": 0.0,
    "forex_scalping_max_stop_price_distance": 0.0,
    "forex_scalping_tp1_rr": 1.0,
    "forex_scalping_tp2_rr": 1.5,
    "forex_scalping_tp3_rr": 2.0,
    "forex_scalping_max_spread_to_stop": 0.18,
    "dry_run": True,
    "signal_source": "analysis",
    "site_signals_db_path": "vip_signals.db",
    "site_signals_limit": 30,
    "site_signals_max_age_minutes": 1,
    "site_signals_min_quality": 0,
    "site_signal_symbols": [],
}

_SINGLE_INSTANCE_LOCK_PATH = None
_SINGLE_INSTANCE_LOCK_OWNER = False


def _release_single_instance_lock() -> None:
    global _SINGLE_INSTANCE_LOCK_OWNER
    if not _SINGLE_INSTANCE_LOCK_OWNER:
        return
    try:
        if _SINGLE_INSTANCE_LOCK_PATH and Path(_SINGLE_INSTANCE_LOCK_PATH).exists():
            Path(_SINGLE_INSTANCE_LOCK_PATH).unlink(missing_ok=True)
    except Exception:
        pass
    _SINGLE_INSTANCE_LOCK_OWNER = False


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        # Process exists but we cannot signal it; treat as running.
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return False
    return True


def acquire_single_instance_lock() -> bool:
    global _SINGLE_INSTANCE_LOCK_PATH
    global _SINGLE_INSTANCE_LOCK_OWNER

    # Namespace the lock per account so multiple wallets can run concurrently,
    # each in its own process (MetaTrader5 allows one terminal per process).
    account_id = os.environ.get("AUTO_TRADER_ACCOUNT_ID", "").strip()
    safe_account_id = re.sub(r"[^A-Za-z0-9_.-]", "_", account_id) if account_id else ""
    lock_name = (
        f"continuous_auto_trader.{safe_account_id}.lock"
        if safe_account_id
        else "continuous_auto_trader.lock"
    )
    lock_path = PROJECT_ROOT / lock_name
    lock_path_str = str(lock_path)
    _SINGLE_INSTANCE_LOCK_PATH = lock_path_str

    def _try_create_lock() -> bool:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(lock_path_str, flags)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True

    try:
        _try_create_lock()
        _SINGLE_INSTANCE_LOCK_OWNER = True
        atexit.register(_release_single_instance_lock)
        return True
    except FileExistsError:
        try:
            existing_pid = int(lock_path.read_text(encoding="utf-8").strip() or "0")
        except Exception:
            existing_pid = 0

        if _is_pid_running(existing_pid):
            return False

        # Replace stale lock only if it is old enough to avoid startup races.
        try:
            age_sec = time.time() - lock_path.stat().st_mtime
        except Exception:
            age_sec = 0
        if age_sec < 120:
            return False

        # Stale lock from crashed process; replace it once.
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            return False

        try:
            _try_create_lock()
            _SINGLE_INSTANCE_LOCK_OWNER = True
            atexit.register(_release_single_instance_lock)
            return True
        except Exception:
            return False
    except Exception:
        return False


def recommendation_side(recommendation: str) -> str:
    text = str(recommendation or "").strip()
    if "شراء" in text:
        return "buy"
    if "بيع" in text:
        return "sell"
    return "none"


def _extract_interval_from_comment(comment: str) -> str:
    text = str(comment or "").strip().upper()
    if not text:
        return ""
    match = re.search(r"(?:^|[_\-\s])TF([0-9]+[MHDW])(?:$|[_\-\s])", text)
    if not match:
        return ""
    interval = match.group(1).lower()
    if interval in SUPPORTED_INTERVALS:
        return interval
    return ""


def is_recommendation_allowed(recommendation: str, allow_normal: bool, allow_strong: bool) -> bool:
    text = str(recommendation or "").strip()
    if text in {"شراء قوي", "بيع قوي"}:
        return allow_strong
    if text in {"شراء", "بيع"}:
        return allow_normal
    return False


def normalize_volume(value: float, vol_min: float, vol_step: float, vol_max: float) -> float:
    if vol_step <= 0:
        vol_step = 0.01
    stepped = math.floor(value / vol_step) * vol_step
    bounded = max(vol_min, min(vol_max, stepped))
    return round(bounded, 6)


def to_base_symbol(broker_symbol: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]", "", str(broker_symbol or "").upper())
    for base_symbol in SUPPORTED_SYMBOLS.keys():
        if normalized.startswith(base_symbol):
            return base_symbol
    return normalized


<<<<<<< Updated upstream
CRYPTO_BASE_SYMBOLS = {
    "BTCUSD", "BTCUSDT", "BTCUSDC",
    "ETHUSD", "ETHUSDT", "ETHUSDC",
    "XRPUSD", "ADAUSD", "SOLUSD", "DOGEUSD",
    "BNBUSD", "LTCUSD", "BCHUSD", "DOTUSD",
    "LINKUSD", "AVAXUSD", "TRXUSD", "XLMUSD",
}


def _is_crypto_symbol(symbol: str) -> bool:
    base_symbol = to_base_symbol(symbol)
    if base_symbol in CRYPTO_BASE_SYMBOLS:
        return True
    return bool(re.match(r"^(BTC|ETH|XRP|ADA|SOL|DOGE|BNB|LTC|BCH|DOT|LINK|AVAX|TRX|XLM)(USD|USDT|USDC)$", base_symbol))


def _is_market_open_for_execution(symbol: str, now_utc: datetime) -> tuple[bool, str]:
    if _is_crypto_symbol(symbol):
        return True, "crypto_24_7"

    weekday = now_utc.weekday()
    now_minutes = now_utc.hour * 60 + now_utc.minute
    saturday_close_minutes = 1 * 60

    if weekday == 5 and now_minutes >= saturday_close_minutes:
        return False, "weekend_non_crypto_market_closed"
    if weekday == 6:
        return False, "weekend_non_crypto_market_closed"

    return True, "market_open"


def calc_risk_volume(bridge: MT5Bridge, symbol: str, entry: float, stop_loss: float, risk_percent: float) -> dict:
=======
def calc_risk_volume(
    bridge: MT5Bridge,
    symbol: str,
    entry: float,
    stop_loss: float,
    risk_percent: float,
    use_equity: bool = True,
) -> dict:
>>>>>>> Stashed changes
    resolved = bridge._resolve_symbol_name(symbol)
    if not resolved:
        return {"success": False, "error": f"Unable to resolve broker symbol for {symbol}"}

    if mt5 is None:
        return {"success": False, "error": "MetaTrader5 package is not installed"}

    mt5.symbol_select(resolved, True)
    info = mt5.symbol_info(resolved)
    account = mt5.account_info()
    if info is None or account is None:
        return {"success": False, "error": f"Missing symbol/account info for {resolved}"}

    tick_size = float(getattr(info, "trade_tick_size", 0.0) or getattr(info, "point", 0.0) or 0.0)
    tick_value = float(getattr(info, "trade_tick_value", 0.0) or 0.0)
    vol_min = float(getattr(info, "volume_min", 0.01) or 0.01)
    vol_step = float(getattr(info, "volume_step", 0.01) or 0.01)
    vol_max = float(getattr(info, "volume_max", 100.0) or 100.0)

    distance = abs(float(entry) - float(stop_loss))
    if tick_size <= 0 or tick_value <= 0 or distance <= 0:
        return {
            "success": False,
            "error": "Invalid sizing inputs",
            "resolved_symbol": resolved,
            "tick_size": tick_size,
            "tick_value": tick_value,
            "distance": distance,
        }

    account_balance = float(getattr(account, "balance", 0.0) or 0.0)
    account_equity = float(getattr(account, "equity", account_balance) or account_balance)
    account_value = account_equity if use_equity else account_balance

    risk_amount = account_value * (risk_percent / 100.0)
    loss_per_lot = (distance / tick_size) * tick_value
    raw_volume = risk_amount / loss_per_lot
    volume = normalize_volume(raw_volume, vol_min, vol_step, vol_max)
    estimated_loss = loss_per_lot * volume
    estimated_risk_percent = (estimated_loss / account_value * 100.0) if account_value > 0 else 0.0

    return {
        "success": True,
        "resolved_symbol": resolved,
        "balance": account_balance,
        "equity": account_equity,
        "account_value_used": round(account_value, 2),
        "risk_basis": "equity" if use_equity else "balance",
        "risk_amount": round(risk_amount, 2),
        "loss_per_lot": round(loss_per_lot, 2),
        "raw_volume": round(raw_volume, 6),
        "volume": volume,
        "estimated_loss_usd": round(estimated_loss, 2),
        "estimated_risk_percent": round(estimated_risk_percent, 4),
        "volume_min": vol_min,
        "volume_step": vol_step,
        "volume_max": vol_max,
    }


def distance_percent(a: float, b: float) -> float:
    base = abs(float(a) or 0.0)
    if base <= 0:
        return 0.0
    return abs(float(a) - float(b)) / base * 100.0


def round_broker_price(bridge: MT5Bridge, symbol: str, price: float) -> float:
    resolved = bridge._resolve_symbol_name(symbol)
    if mt5 is not None and resolved:
        info = mt5.symbol_info(resolved)
        if info is not None:
            digits = int(getattr(info, "digits", 5) or 5)
            return round(float(price), max(0, digits))
    return round(float(price), 5)


def load_json(path: Path, default_value):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default_value


def save_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_config(user_config: dict) -> dict:
    merged = dict(DEFAULT_CONFIG)
    merged.update(user_config or {})
<<<<<<< Updated upstream

    signal_source = str(merged.get("signal_source") or DEFAULT_CONFIG["signal_source"]).strip().lower()
    if signal_source in {"site", "website", "site_signals"}:
        signal_source = "site_db"
    if signal_source not in {"analysis", "site_db", "both"}:
        signal_source = "analysis"
    merged["signal_source"] = signal_source

    selected_symbols = [re.sub(r"[^A-Z0-9]", "", str(item).upper()) for item in merged.get("symbols", []) if str(item).strip()]
    if signal_source == "analysis":
        selected_symbols = [item for item in selected_symbols if item in SUPPORTED_SYMBOLS]
    merged["symbols"] = selected_symbols
=======
    merged["analysis_source"] = TRADE_ANALYSIS_SOURCE
    merged["analysis_engine"] = TRADE_ANALYSIS_ENGINE
    merged["symbols"] = [str(item).strip().upper() for item in merged.get("symbols", []) if str(item).strip().upper() in SUPPORTED_SYMBOLS]
    blocked_raw = merged.get("blocked_symbols", [])
    if not isinstance(blocked_raw, list):
        blocked_raw = [blocked_raw]
    merged["blocked_symbols"] = sorted(
        {
            to_base_symbol(str(item).strip().upper())
            for item in blocked_raw
            if to_base_symbol(str(item).strip().upper()) in SUPPORTED_SYMBOLS
        }
    )
    if merged["blocked_symbols"]:
        blocked_set = set(merged["blocked_symbols"])
        merged["symbols"] = [symbol for symbol in merged["symbols"] if to_base_symbol(symbol) not in blocked_set]
>>>>>>> Stashed changes
    merged["intervals"] = [str(item).strip().lower() for item in merged.get("intervals", []) if str(item).strip().lower() in SUPPORTED_INTERVALS]
    merged["blocked_symbols"] = [re.sub(r"[^A-Z0-9]", "", str(item).upper()) for item in merged.get("blocked_symbols", []) if str(item).strip()]
    merged["site_signal_symbols"] = [re.sub(r"[^A-Z0-9*]", "", str(item).upper()) for item in merged.get("site_signal_symbols", []) if str(item).strip()]
    if not merged["symbols"] and signal_source == "analysis":
        merged["symbols"] = list(DEFAULT_CONFIG["symbols"])
    if not merged["intervals"]:
        merged["intervals"] = list(DEFAULT_CONFIG["intervals"])
    merged["scan_every_sec"] = max(15, int(merged.get("scan_every_sec", 60)))
    merged["risk_percent"] = max(0.1, float(merged.get("risk_percent", 1.0)))
    merged["fixed_volume"] = max(0.0, float(merged.get("fixed_volume", 0.0) or 0.0))
    merged["use_equity_for_risk"] = bool(merged.get("use_equity_for_risk", True))
<<<<<<< Updated upstream
    merged["max_risk_usd_per_trade"] = max(0.0, float(merged.get("max_risk_usd_per_trade", 8.0)))
=======
    merged["max_risk_usd_per_trade"] = max(0.0, float(merged.get("max_risk_usd_per_trade", 8.0) or 0.0))
>>>>>>> Stashed changes
    merged["max_risk_percent_of_equity"] = max(0.1, float(merged.get("max_risk_percent_of_equity", 0.8)))
    merged["max_stop_distance_percent"] = max(0.1, float(merged.get("max_stop_distance_percent", 1.2)))
    merged["max_target_distance_percent"] = max(0.1, float(merged.get("max_target_distance_percent", 3.5)))
    merged["min_rr_ratio"] = max(0.1, float(merged.get("min_rr_ratio", 1.1)))
    merged["cooldown_minutes_per_symbol"] = max(0, int(merged.get("cooldown_minutes_per_symbol", 90)))
    merged["max_pending_orders"] = max(0, int(merged.get("max_pending_orders", 0) or 0))
    merged["pending_dedupe_price_tolerance"] = max(
        0.0,
        float(merged.get("pending_dedupe_price_tolerance", 0.0) or 0.0),
    )
    merged["pending_expiry_minutes"] = max(1, int(merged.get("pending_expiry_minutes", 180)))
    merged["market_reprice_entry"] = bool(merged.get("market_reprice_entry", False))
    merged["max_market_entry_drift_percent"] = max(
        0.0,
        float(merged.get("max_market_entry_drift_percent", 0.6) or 0.0),
    )
    merged["max_open_positions"] = max(0, int(merged.get("max_open_positions", 0)))
    merged["dynamic_max_positions_enabled"] = bool(merged.get("dynamic_max_positions_enabled", True))
    merged["max_total_open_risk_percent"] = max(0.1, float(merged.get("max_total_open_risk_percent", 2.1)))
    merged["min_open_positions"] = max(1, int(merged.get("min_open_positions", 3)))
    merged["max_open_positions_cap"] = max(0, int(merged.get("max_open_positions_cap", 24)))
    merged["min_score_gap"] = max(0, int(merged.get("min_score_gap", 18)))
    merged["daily_loss_limit_usd"] = max(0.0, float(merged.get("daily_loss_limit_usd", 25.0)))
<<<<<<< Updated upstream
    merged["daily_loss_limit_follow_risk_percent"] = bool(merged.get("daily_loss_limit_follow_risk_percent", True))
    daily_loss_percent = max(0.0, float(merged.get("daily_loss_limit_percent_of_equity", 0.0)))
    if merged["daily_loss_limit_usd"] <= 0 and merged["daily_loss_limit_follow_risk_percent"]:
        daily_loss_percent = float(merged["risk_percent"])
    merged["daily_loss_limit_percent_of_equity"] = daily_loss_percent
    merged["max_consecutive_losses"] = max(0, int(merged.get("max_consecutive_losses", 3)))
    merged["site_signals_limit"] = max(1, min(200, int(merged.get("site_signals_limit", 30))))
    merged["site_signals_max_age_minutes"] = max(0, int(merged.get("site_signals_max_age_minutes", 180)))
    merged["site_signals_min_quality"] = max(0, min(100, int(merged.get("site_signals_min_quality", 0))))
=======
    merged["daily_loss_limit_percent_of_equity"] = max(0.0, float(merged.get("daily_loss_limit_percent_of_equity", 0.0) or 0.0))
    merged["max_consecutive_losses"] = max(0, int(merged.get("max_consecutive_losses", 3)))
    merged["daily_profit_lock_usd"] = max(0.0, float(merged.get("daily_profit_lock_usd", 0.0)))
    merged["daily_profit_lock_percent_of_equity"] = max(0.0, float(merged.get("daily_profit_lock_percent_of_equity", 0.0) or 0.0))
    merged["ignore_consecutive_losses_if_daily_pnl_above_usd"] = max(
        0.0,
        float(merged.get("ignore_consecutive_losses_if_daily_pnl_above_usd", 0.0)),
    )
    merged["ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity"] = max(
        0.0,
        float(merged.get("ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity", 0.0) or 0.0),
    )
    merged["interval_loss_freeze_enabled"] = bool(merged.get("interval_loss_freeze_enabled", True))
    merged["interval_loss_freeze_after"] = max(0, int(merged.get("interval_loss_freeze_after", 2) or 0))
    merged["interval_loss_freeze_minutes"] = max(0, int(merged.get("interval_loss_freeze_minutes", 180) or 0))
    freeze_scope = str(merged.get("interval_loss_freeze_scope", "interval") or "interval").strip().lower()
    merged["interval_loss_freeze_scope"] = freeze_scope if freeze_scope in {"interval", "symbol", "symbol_interval"} else "interval"
    merged["gold_trend_filter_enabled"] = bool(merged.get("gold_trend_filter_enabled", True))
    merged["gold_trend_min_gap"] = max(0, int(merged.get("gold_trend_min_gap", 20)))
    merged["gold_trend_override_score_gap"] = max(0, int(merged.get("gold_trend_override_score_gap", 75)))
    merged["gold_trend_fail_open"] = bool(merged.get("gold_trend_fail_open", False))
    merged["ema_trend_filter_enabled"] = bool(merged.get("ema_trend_filter_enabled", False))
    ema_trend_interval = str(merged.get("ema_trend_interval", "4h") or "4h").strip().lower()
    merged["ema_trend_interval"] = ema_trend_interval if ema_trend_interval in SUPPORTED_INTERVALS else "4h"
    merged["ema_trend_fast_key"] = str(merged.get("ema_trend_fast_key", "ema50") or "ema50").strip()
    merged["ema_trend_slow_key"] = str(merged.get("ema_trend_slow_key", "ema200") or "ema200").strip()
    merged["ema_trend_require_order"] = bool(merged.get("ema_trend_require_order", True))
    merged["ema_trend_override_score_gap"] = max(0, int(merged.get("ema_trend_override_score_gap", 0) or 0))
    merged["bos_retest_filter_enabled"] = bool(merged.get("bos_retest_filter_enabled", False))
    bos_entry_intervals = merged.get("bos_retest_entry_intervals", ["5m", "15m"])
    if not isinstance(bos_entry_intervals, list):
        bos_entry_intervals = ["5m", "15m"]
    merged["bos_retest_entry_intervals"] = [
        str(item).strip().lower()
        for item in bos_entry_intervals
        if str(item).strip().lower() in SUPPORTED_INTERVALS
    ] or ["5m", "15m"]
    merged["bos_retest_break_buffer_atr"] = max(0.0, float(merged.get("bos_retest_break_buffer_atr", 0.05) or 0.0))
    merged["bos_retest_retest_tolerance_atr"] = max(0.0, float(merged.get("bos_retest_retest_tolerance_atr", 0.35) or 0.0))
    merged["bos_retest_require_candle_confirmation"] = bool(merged.get("bos_retest_require_candle_confirmation", True))
    merged["bos_retest_fail_open"] = bool(merged.get("bos_retest_fail_open", False))
    trend_intervals = merged.get("gold_trend_filter_intervals", ["1h", "4h"])
    if not isinstance(trend_intervals, list):
        trend_intervals = ["1h", "4h"]
    merged["gold_trend_filter_intervals"] = [
        str(item).strip().lower()
        for item in trend_intervals
        if str(item).strip().lower() in SUPPORTED_INTERVALS
    ] or ["1h", "4h"]

    merged["gold_scalping_strategy_enabled"] = bool(merged.get("gold_scalping_strategy_enabled", False))
    entry_intervals = merged.get("gold_scalping_entry_intervals", ["1m", "3m", "5m"])
    if not isinstance(entry_intervals, list):
        entry_intervals = ["1m", "3m", "5m"]
    merged["gold_scalping_entry_intervals"] = [
        str(item).strip().lower()
        for item in entry_intervals
        if str(item).strip().lower() in SUPPORTED_INTERVALS
    ] or ["1m", "3m", "5m"]
    context_intervals = merged.get("gold_scalping_context_intervals", ["15m"])
    if not isinstance(context_intervals, list):
        context_intervals = ["15m"]
    merged["gold_scalping_context_intervals"] = [
        str(item).strip().lower()
        for item in context_intervals
        if str(item).strip().lower() in SUPPORTED_INTERVALS
    ] or ["15m"]
    merged["gold_scalping_min_context_agreement"] = max(0, int(merged.get("gold_scalping_min_context_agreement", 1)))
    merged["gold_scalping_context_min_ema_gap_percent"] = max(0.0, float(merged.get("gold_scalping_context_min_ema_gap_percent", 0.01) or 0.0))
    merged["gold_scalping_min_entry_score_gap"] = max(0, int(merged.get("gold_scalping_min_entry_score_gap", 35) or 35))
    for key in (
        "gold_scalping_rsi_buy_min",
        "gold_scalping_rsi_buy_max",
        "gold_scalping_rsi_sell_min",
        "gold_scalping_rsi_sell_max",
        "gold_scalping_max_entry_distance_atr",
        "gold_scalping_min_volume_ratio",
        "gold_scalping_stop_atr_multiplier",
        "gold_scalping_min_stop_price_distance",
        "gold_scalping_max_stop_price_distance",
        "gold_scalping_tp1_rr",
        "gold_scalping_tp2_rr",
        "gold_scalping_tp3_rr",
        "gold_scalping_max_spread_to_stop",
    ):
        merged[key] = max(0.0, float(merged.get(key, DEFAULT_CONFIG.get(key, 0.0)) or 0.0))
    merged["gold_scalping_require_rsi_momentum"] = bool(merged.get("gold_scalping_require_rsi_momentum", True))
    merged["gold_scalping_skip_bollinger_extreme"] = bool(merged.get("gold_scalping_skip_bollinger_extreme", True))
    atr_reference = str(merged.get("gold_scalping_atr_reference_interval", "5m") or "5m").strip().lower()
    merged["gold_scalping_atr_reference_interval"] = atr_reference if atr_reference in SUPPORTED_INTERVALS else "5m"

    merged["forex_scalping_strategy_enabled"] = bool(merged.get("forex_scalping_strategy_enabled", False))
    forex_entry_intervals = merged.get("forex_scalping_entry_intervals", ["1m", "3m", "5m"])
    if not isinstance(forex_entry_intervals, list):
        forex_entry_intervals = ["1m", "3m", "5m"]
    merged["forex_scalping_entry_intervals"] = [
        str(item).strip().lower()
        for item in forex_entry_intervals
        if str(item).strip().lower() in SUPPORTED_INTERVALS
    ] or ["1m", "3m", "5m"]
    forex_context_intervals = merged.get("forex_scalping_context_intervals", ["15m"])
    if not isinstance(forex_context_intervals, list):
        forex_context_intervals = ["15m"]
    merged["forex_scalping_context_intervals"] = [
        str(item).strip().lower()
        for item in forex_context_intervals
        if str(item).strip().lower() in SUPPORTED_INTERVALS
    ] or ["15m"]
    merged["forex_scalping_min_context_agreement"] = max(1, int(merged.get("forex_scalping_min_context_agreement", 1) or 1))
    merged["forex_scalping_context_min_ema_gap_percent"] = max(0.0, float(merged.get("forex_scalping_context_min_ema_gap_percent", 0.005) or 0.0))
    merged["forex_scalping_min_entry_score_gap"] = max(0, int(merged.get("forex_scalping_min_entry_score_gap", 35) or 35))
    for key in (
        "forex_scalping_rsi_buy_min",
        "forex_scalping_rsi_buy_max",
        "forex_scalping_rsi_sell_min",
        "forex_scalping_rsi_sell_max",
        "forex_scalping_max_entry_distance_atr",
        "forex_scalping_min_volume_ratio",
        "forex_scalping_stop_atr_multiplier",
        "forex_scalping_min_stop_price_distance",
        "forex_scalping_max_stop_price_distance",
        "forex_scalping_tp1_rr",
        "forex_scalping_tp2_rr",
        "forex_scalping_tp3_rr",
        "forex_scalping_max_spread_to_stop",
    ):
        merged[key] = max(0.0, float(merged.get(key, DEFAULT_CONFIG.get(key, 0.0)) or 0.0))
    merged["forex_scalping_require_rsi_momentum"] = bool(merged.get("forex_scalping_require_rsi_momentum", True))
    merged["forex_scalping_skip_bollinger_extreme"] = bool(merged.get("forex_scalping_skip_bollinger_extreme", True))
    forex_atr_reference = str(merged.get("forex_scalping_atr_reference_interval", "5m") or "5m").strip().lower()
    merged["forex_scalping_atr_reference_interval"] = forex_atr_reference if forex_atr_reference in SUPPORTED_INTERVALS else "5m"

    merged["tp_step_guard_enabled"] = bool(merged.get("tp_step_guard_enabled", True))
    merged["tp1_trigger_rr"] = max(0.0, float(merged.get("tp1_trigger_rr", 1.0) or 1.0))
    merged["tp2_trigger_rr"] = max(merged["tp1_trigger_rr"], float(merged.get("tp2_trigger_rr", 2.0) or 2.0))
    merged["tp3_trigger_rr"] = max(merged["tp2_trigger_rr"], float(merged.get("tp3_trigger_rr", 3.0) or 3.0))
    merged["tp1_lock_rr"] = max(0.0, float(merged.get("tp1_lock_rr", 0.5) or 0.5))
    merged["tp2_lock_rr"] = max(merged["tp1_lock_rr"], float(merged.get("tp2_lock_rr", 1.5) or 1.5))
    merged["tp3_lock_rr"] = max(merged["tp2_lock_rr"], float(merged.get("tp3_lock_rr", 2.5) or 2.5))
>>>>>>> Stashed changes

    sessions = merged.get("trading_sessions_utc", DEFAULT_CONFIG["trading_sessions_utc"])
    normalized_sessions = []
    disable_sessions = "trading_sessions_utc" in (user_config or {}) and sessions == []
    if isinstance(sessions, list) and not disable_sessions:
        for one in sessions:
            if not isinstance(one, dict):
                continue
            start = str(one.get("start", "")).strip()
            end = str(one.get("end", "")).strip()
            weekdays = one.get("weekdays", [0, 1, 2, 3, 4])
            if not start or not end:
                continue
            if not isinstance(weekdays, list):
                weekdays = [0, 1, 2, 3, 4]
            safe_weekdays = sorted({int(x) for x in weekdays if str(x).isdigit() and 0 <= int(x) <= 6})
            if not safe_weekdays:
                safe_weekdays = [0, 1, 2, 3, 4]
            normalized_sessions.append({"start": start, "end": end, "weekdays": safe_weekdays})

    merged["trading_sessions_utc"] = [] if disable_sessions else (normalized_sessions if normalized_sessions else list(DEFAULT_CONFIG["trading_sessions_utc"]))
    return merged


def _parse_hhmm(value: str) -> tuple[int, int] | None:
    text = str(value or "").strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2))
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour, minute


def _is_within_utc_sessions(config: dict, now_utc: datetime) -> tuple[bool, str]:
    sessions = config.get("trading_sessions_utc", [])
    if not isinstance(sessions, list) or not sessions:
        return True, "no_sessions_configured"

    weekday = now_utc.weekday()
    now_minutes = now_utc.hour * 60 + now_utc.minute

    for idx, one in enumerate(sessions):
        if not isinstance(one, dict):
            continue

        weekdays = one.get("weekdays", [0, 1, 2, 3, 4])
        if weekday not in weekdays:
            continue

        parsed_start = _parse_hhmm(one.get("start", ""))
        parsed_end = _parse_hhmm(one.get("end", ""))
        if not parsed_start or not parsed_end:
            continue

        start_minutes = parsed_start[0] * 60 + parsed_start[1]
        end_minutes = parsed_end[0] * 60 + parsed_end[1]

        if start_minutes == end_minutes:
            return True, f"session_{idx}_full_day"
        if start_minutes < end_minutes:
            if start_minutes <= now_minutes < end_minutes:
                return True, f"session_{idx}"
        else:
            if now_minutes >= start_minutes or now_minutes < end_minutes:
                return True, f"session_{idx}_overnight"

    return False, "outside_configured_sessions"


def _is_gold_market_open(config: dict, now_utc: datetime) -> tuple[bool, str]:
    """
    Check if gold (XAUUSD) is tradable during current UTC time.
    Gold trades well during London+NY sessions: 08:00-22:00 UTC.
    Skip outside these hours to avoid low-liquidity periods.
    """
    weekday = now_utc.weekday()
    if weekday >= 5:  # Skip weekends
        return False, "gold_weekend"

    if bool(config.get("force_gold_trading_now", False)):
        return True, "gold_forced_trading_enabled"

    if config.get("trading_sessions_utc") == []:
        return True, "gold_time_filter_disabled"
    
    hour = now_utc.hour
    minute = now_utc.minute
    now_minutes = hour * 60 + minute
    
    # Gold active during London (08:00) through NY close (22:00) UTC
    london_start = 8 * 60       # 08:00 UTC
    ny_close = 22 * 60          # 22:00 UTC
    
    if london_start <= now_minutes < ny_close:
        return True, "gold_london_ny_session"
    
    return False, "gold_outside_trading_hours"


def _daily_risk_guard(bridge: MT5Bridge, config: dict, now_utc: datetime) -> dict:
    if mt5 is None:
        return {"success": False, "error": "MetaTrader5 package is not installed"}

    account = mt5.account_info()
    account_balance = float(getattr(account, "balance", 0.0) or 0.0) if account is not None else 0.0
    account_equity = float(getattr(account, "equity", account_balance) or account_balance) if account is not None else account_balance
    use_equity = bool(config.get("use_equity_for_risk", True))
    account_value = account_equity if use_equity else account_balance

    day_start_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    reset_after_utc = day_start_utc
    reset_text = str(config.get("daily_loss_reset_at_utc") or "").strip()
    if reset_text:
        try:
            parsed_reset = datetime.fromisoformat(reset_text.replace("Z", "+00:00"))
            if parsed_reset.tzinfo is None:
                parsed_reset = parsed_reset.replace(tzinfo=timezone.utc)
            parsed_reset = parsed_reset.astimezone(timezone.utc)
            if parsed_reset > reset_after_utc:
                reset_after_utc = parsed_reset
        except ValueError:
            pass

    day_start_local = reset_after_utc.astimezone().replace(tzinfo=None)
    now_local = now_utc.astimezone().replace(tzinfo=None)

    deals = mt5.history_deals_get(day_start_local, now_local) or []
    magic = int(getattr(bridge, "magic", 0) or 0)
    out_entry = int(getattr(mt5, "DEAL_ENTRY_OUT", 1))
    out_by_entry = int(getattr(mt5, "DEAL_ENTRY_OUT_BY", 3))

    by_position = {}
    daily_pnl = 0.0
    interval_positions = {}
    symbol_positions = {}
    symbol_interval_positions = {}

    for deal in deals:
        if int(getattr(deal, "magic", 0) or 0) != magic:
            continue

        entry_type = int(getattr(deal, "entry", -1) or -1)
        if entry_type not in {out_entry, out_by_entry}:
            continue

        profit = float(getattr(deal, "profit", 0.0) or 0.0)
        swap = float(getattr(deal, "swap", 0.0) or 0.0)
        commission = float(getattr(deal, "commission", 0.0) or 0.0)
        pnl = profit + swap + commission
        daily_pnl += pnl

        position_id = int(getattr(deal, "position_id", 0) or 0)
        close_time = int(getattr(deal, "time", 0) or 0)
        key = f"pos:{position_id}" if position_id > 0 else f"deal:{int(getattr(deal, 'ticket', 0) or 0)}"

        row = by_position.setdefault(key, {"pnl": 0.0, "close_time": close_time})
        row["pnl"] += pnl
        row["close_time"] = max(int(row.get("close_time", 0) or 0), close_time)

        symbol = to_base_symbol(getattr(deal, "symbol", ""))
        if symbol:
            srow = symbol_positions.setdefault(symbol, {"pnl": 0.0, "close_time": close_time, "symbol": symbol})
            srow["pnl"] += pnl
            srow["close_time"] = max(int(srow.get("close_time", 0) or 0), close_time)

        interval = _extract_interval_from_comment(getattr(deal, "comment", ""))
        if interval:
            interval_key = f"tf:{interval}"
            irow = interval_positions.setdefault(interval_key, {"pnl": 0.0, "close_time": close_time, "interval": interval})
            irow["pnl"] += pnl
            irow["close_time"] = max(int(irow.get("close_time", 0) or 0), close_time)

            if symbol:
                si_key = f"{symbol}:{interval}"
                sirow = symbol_interval_positions.setdefault(
                    si_key,
                    {"pnl": 0.0, "close_time": close_time, "symbol": symbol, "interval": interval},
                )
                sirow["pnl"] += pnl
                sirow["close_time"] = max(int(sirow.get("close_time", 0) or 0), close_time)

    closed_positions = sorted(by_position.values(), key=lambda x: int(x.get("close_time", 0) or 0), reverse=True)
    consecutive_losses = 0
    for row in closed_positions:
        pnl = float(row.get("pnl", 0.0) or 0.0)
        if pnl < 0:
            consecutive_losses += 1
        else:
            break

<<<<<<< Updated upstream
    account = mt5.account_info()
    account_balance = float(getattr(account, "balance", 0.0) or 0.0) if account is not None else 0.0
    account_equity = float(getattr(account, "equity", account_balance) or account_balance) if account is not None else 0.0

    fixed_loss_limit = max(0.0, float(config.get("daily_loss_limit_usd", 0.0) or 0.0))
    percent_loss_limit = max(0.0, float(config.get("daily_loss_limit_percent_of_equity", 0.0) or 0.0))
    if fixed_loss_limit > 0:
        loss_limit = fixed_loss_limit
        loss_limit_source = "usd"
    elif percent_loss_limit > 0 and account_equity > 0:
        loss_limit = account_equity * (percent_loss_limit / 100.0)
        loss_limit_source = "equity_percent"
    else:
        loss_limit = 0.0
        loss_limit_source = "disabled"
=======
    loss_limit_fixed = max(0.0, float(config.get("daily_loss_limit_usd", 25.0) or 0.0))
    loss_limit_pct = max(0.0, float(config.get("daily_loss_limit_percent_of_equity", 0.0) or 0.0))
    loss_limit_dynamic = (account_value * loss_limit_pct / 100.0) if account_value > 0 and loss_limit_pct > 0 else 0.0
    loss_limit_candidates = [value for value in (loss_limit_fixed, loss_limit_dynamic) if value > 0]
    loss_limit = min(loss_limit_candidates) if loss_limit_candidates else 0.0

>>>>>>> Stashed changes
    max_consecutive_losses = max(0, int(config.get("max_consecutive_losses", 3) or 3))
    profit_lock_fixed = max(0.0, float(config.get("daily_profit_lock_usd", 0.0) or 0.0))
    profit_lock_pct = max(0.0, float(config.get("daily_profit_lock_percent_of_equity", 0.0) or 0.0))
    profit_lock_dynamic = (account_value * profit_lock_pct / 100.0) if account_value > 0 and profit_lock_pct > 0 else 0.0
    profit_lock_candidates = [value for value in (profit_lock_fixed, profit_lock_dynamic) if value > 0]
    profit_lock = min(profit_lock_candidates) if profit_lock_candidates else 0.0

    consecutive_ignore_fixed = max(0.0, float(config.get("ignore_consecutive_losses_if_daily_pnl_above_usd", 0.0) or 0.0))
    consecutive_ignore_pct = max(0.0, float(config.get("ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity", 0.0) or 0.0))
    consecutive_ignore_dynamic = (account_value * consecutive_ignore_pct / 100.0) if account_value > 0 and consecutive_ignore_pct > 0 else 0.0
    consecutive_ignore_candidates = [value for value in (consecutive_ignore_fixed, consecutive_ignore_dynamic) if value > 0]
    consecutive_ignore_floor = min(consecutive_ignore_candidates) if consecutive_ignore_candidates else 0.0
    breached_daily_loss = loss_limit > 0 and daily_pnl <= -loss_limit
    breached_profit_lock = profit_lock > 0 and daily_pnl >= profit_lock
    ignore_consecutive = consecutive_ignore_floor > 0 and daily_pnl >= consecutive_ignore_floor
    breached_consecutive = (
        max_consecutive_losses > 0
        and consecutive_losses >= max_consecutive_losses
        and not ignore_consecutive
    )

    interval_freeze_enabled = bool(config.get("interval_loss_freeze_enabled", True))
    interval_freeze_after = max(0, int(config.get("interval_loss_freeze_after", 2) or 0))
    interval_freeze_minutes = max(0, int(config.get("interval_loss_freeze_minutes", 180) or 0))
    interval_freeze_scope = str(config.get("interval_loss_freeze_scope", "interval") or "interval").strip().lower()
    if interval_freeze_scope not in {"interval", "symbol", "symbol_interval"}:
        interval_freeze_scope = "interval"

    if interval_freeze_scope == "symbol":
        source_rows = symbol_positions
    elif interval_freeze_scope == "symbol_interval":
        source_rows = symbol_interval_positions
    else:
        source_rows = interval_positions
    grouped_rows = {}
    for row in source_rows.values():
        if interval_freeze_scope == "symbol_interval":
            group_key = f"{row.get('symbol')}:{row.get('interval')}"
        elif interval_freeze_scope == "symbol":
            group_key = str(row.get("symbol") or "")
        else:
            group_key = str(row.get("interval") or "")
        if not group_key:
            continue
        grouped_rows.setdefault(group_key, []).append(row)

    interval_freeze_map = {}
    if interval_freeze_enabled and interval_freeze_after > 0 and interval_freeze_minutes > 0:
        now_ts = int(now_utc.timestamp())
        for group_key, rows in grouped_rows.items():
            ordered = sorted(rows, key=lambda x: int(x.get("close_time", 0) or 0), reverse=True)
            streak = 0
            last_loss_time = 0
            for row in ordered:
                row_pnl = float(row.get("pnl", 0.0) or 0.0)
                if row_pnl < 0:
                    streak += 1
                    last_loss_time = max(last_loss_time, int(row.get("close_time", 0) or 0))
                else:
                    break
            if streak >= interval_freeze_after and last_loss_time > 0:
                until_ts = last_loss_time + (interval_freeze_minutes * 60)
                if until_ts > now_ts:
                    interval_freeze_map[group_key] = {
                        "scope": interval_freeze_scope,
                        "streak_losses": streak,
                        "freeze_after_losses": interval_freeze_after,
                        "freeze_minutes": interval_freeze_minutes,
                        "frozen_until_ts": until_ts,
                        "frozen_until_utc": datetime.fromtimestamp(until_ts, tz=timezone.utc).isoformat(timespec="seconds"),
                    }

    return {
        "success": True,
        "account_balance": round(account_balance, 2),
        "account_equity": round(account_equity, 2),
        "account_value_used": round(account_value, 2),
        "risk_basis": "equity" if use_equity else "balance",
        "daily_realized_pnl_usd": round(daily_pnl, 2),
        "daily_loss_limit_usd": round(loss_limit, 2),
<<<<<<< Updated upstream
        "daily_loss_limit_source": loss_limit_source,
        "daily_loss_limit_percent_of_equity": round(percent_loss_limit, 4),
        "daily_loss_limit_follow_risk_percent": bool(config.get("daily_loss_limit_follow_risk_percent", True)),
        "account_equity": round(account_equity, 2),
=======
        "daily_loss_limit_percent_of_equity": round(loss_limit_pct, 3),
>>>>>>> Stashed changes
        "risk_window_start_utc": reset_after_utc.isoformat(timespec="seconds"),
        "consecutive_losses": consecutive_losses,
        "max_consecutive_losses": max_consecutive_losses,
        "closed_positions_today": len(closed_positions),
        "breached_daily_loss_limit": breached_daily_loss,
        "daily_profit_lock_usd": round(profit_lock, 2),
        "daily_profit_lock_percent_of_equity": round(profit_lock_pct, 3),
        "breached_daily_profit_lock": breached_profit_lock,
        "ignore_consecutive_losses_if_daily_pnl_above_usd": round(consecutive_ignore_floor, 2),
        "ignore_consecutive_losses_if_daily_pnl_above_percent_of_equity": round(consecutive_ignore_pct, 3),
        "ignored_consecutive_losses_due_to_daily_pnl": ignore_consecutive,
        "breached_consecutive_losses": breached_consecutive,
        "blocked": breached_daily_loss or breached_profit_lock or breached_consecutive,
        "interval_freeze_enabled": interval_freeze_enabled,
        "interval_freeze_scope": interval_freeze_scope,
        "interval_freeze_after_losses": interval_freeze_after,
        "interval_freeze_minutes": interval_freeze_minutes,
        "interval_freeze_map": interval_freeze_map,
        "interval_freeze_active_count": len(interval_freeze_map),
    }


def gold_trend_alignment(config: dict, candidate: dict) -> dict:
    if not bool(config.get("gold_trend_filter_enabled", True)):
        return {"allowed": True, "reason": "gold_trend_filter_disabled"}

    candidate_side = str(candidate.get("side") or "none")
    interval = str(candidate.get("interval") or "").lower()
    if candidate_side not in {"buy", "sell"}:
        return {"allowed": False, "reason": "candidate_side_missing"}

    trend_intervals = [str(item).lower() for item in config.get("gold_trend_filter_intervals", ["1h", "4h"])]
    min_gap = int(config.get("gold_trend_min_gap", 20) or 20)
    fail_open = bool(config.get("gold_trend_fail_open", False))
    checks = []

    for trend_interval in trend_intervals:
        if trend_interval == interval:
            continue
        trend_analysis = perform_full_analysis("XAUUSD", trend_interval)
        if not trend_analysis.get("success"):
            checks.append({"interval": trend_interval, "success": False, "error": trend_analysis.get("error")})
            if not fail_open:
                return {
                    "allowed": False,
                    "reason": "gold_trend_analysis_unavailable",
                    "trend_interval": trend_interval,
                    "error": trend_analysis.get("error"),
                    "checks": checks,
                }
            continue

        trend_buy = int(trend_analysis.get("buy_score") or 0)
        trend_sell = int(trend_analysis.get("sell_score") or 0)
        trend_side = "buy" if trend_buy > trend_sell else "sell"
        trend_gap = abs(trend_buy - trend_sell)
        checks.append(
            {
                "interval": trend_interval,
                "success": True,
                "side": trend_side,
                "gap": trend_gap,
            }
        )

        if trend_gap >= min_gap and candidate_side != trend_side:
            score_gap = int(candidate.get("score_gap") or 0)
            override_gap = int(config.get("gold_trend_override_score_gap", 75) or 75)
            if score_gap >= override_gap:
                return {
                    "allowed": True,
                    "reason": "gold_counter_trend_override_strong_signal",
                    "entry_side": candidate_side,
                    "entry_interval": interval,
                    "trend_interval": trend_interval,
                    "trend_side": trend_side,
                    "trend_gap": trend_gap,
                    "min_gap": min_gap,
                    "override_score_gap": override_gap,
                    "score_gap": score_gap,
                    "checks": checks,
                }
            return {
                "allowed": False,
                "reason": "gold_counter_trend",
                "entry_side": candidate_side,
                "entry_interval": interval,
                "trend_interval": trend_interval,
                "trend_side": trend_side,
                "trend_gap": trend_gap,
                "min_gap": min_gap,
                "score_gap": score_gap,
                "checks": checks,
            }

    if checks and not any(bool(one.get("success")) for one in checks) and not fail_open:
        return {"allowed": False, "reason": "gold_trend_all_intervals_unavailable", "checks": checks}

    return {"allowed": True, "reason": "gold_trend_aligned", "checks": checks}


def ema_trend_alignment(config: dict, candidate: dict, analyses_by_key: dict[tuple[str, str], dict]) -> dict:
    if not bool(config.get("ema_trend_filter_enabled", False)):
        return {"allowed": True, "reason": "ema_trend_filter_disabled"}

    symbol = str(candidate.get("symbol") or "").upper()
    side = str(candidate.get("side") or "none")
    trend_interval = str(config.get("ema_trend_interval", "4h") or "4h").strip().lower()
    if side not in {"buy", "sell"}:
        return {"allowed": False, "reason": "ema_trend_side_missing", "symbol": symbol, "interval": trend_interval}

    key = (symbol, trend_interval)
    trend_analysis = analyses_by_key.get(key)
    if not isinstance(trend_analysis, dict):
        trend_analysis = perform_full_analysis(symbol, trend_interval)
    if not trend_analysis or not trend_analysis.get("success"):
        return {
            "allowed": False,
            "reason": "ema_trend_analysis_unavailable",
            "symbol": symbol,
            "interval": trend_interval,
            "error": (trend_analysis or {}).get("error"),
        }

    technical = trend_analysis.get("technical") if isinstance(trend_analysis.get("technical"), dict) else {}
    fast_key = str(config.get("ema_trend_fast_key", "ema50") or "ema50")
    slow_key = str(config.get("ema_trend_slow_key", "ema200") or "ema200")
    require_order = bool(config.get("ema_trend_require_order", True))

    try:
        fast = float(technical.get(fast_key) or technical.get("sma50") or 0.0)
        slow = float(technical.get(slow_key) or 0.0)
        price = float(trend_analysis.get("entry_point") or 0.0)
    except (TypeError, ValueError):
        return {
            "allowed": False,
            "reason": "ema_trend_values_invalid",
            "symbol": symbol,
            "interval": trend_interval,
        }

    if fast <= 0 or slow <= 0 or price <= 0:
        return {
            "allowed": False,
            "reason": "ema_trend_values_missing",
            "symbol": symbol,
            "interval": trend_interval,
            "price": price,
            "fast": fast,
            "slow": slow,
        }

    if side == "buy":
        aligned = price > fast and price > slow and (not require_order or fast > slow)
    else:
        aligned = price < fast and price < slow and (not require_order or fast < slow)

    score_gap = int(candidate.get("score_gap") or 0)
    override_gap = max(0, int(config.get("ema_trend_override_score_gap", 0) or 0))
    if not aligned and override_gap > 0 and score_gap >= override_gap:
        return {
            "allowed": True,
            "reason": "ema_trend_override_strong_signal",
            "symbol": symbol,
            "interval": trend_interval,
            "side": side,
            "price": round(price, 5),
            "fast": round(fast, 5),
            "slow": round(slow, 5),
            "require_order": require_order,
            "fast_key": fast_key,
            "slow_key": slow_key,
            "score_gap": score_gap,
            "override_score_gap": override_gap,
        }

    return {
        "allowed": bool(aligned),
        "reason": "ema_trend_aligned" if aligned else "ema_trend_not_aligned",
        "symbol": symbol,
        "interval": trend_interval,
        "side": side,
        "price": round(price, 5),
        "fast": round(fast, 5),
        "slow": round(slow, 5),
        "require_order": require_order,
        "fast_key": fast_key,
        "slow_key": slow_key,
        "score_gap": score_gap,
        "override_score_gap": override_gap,
    }


def bos_retest_alignment(config: dict, candidate: dict) -> dict:
    if not bool(config.get("bos_retest_filter_enabled", False)):
        return {"allowed": True, "reason": "bos_retest_filter_disabled"}

    interval = str(candidate.get("interval") or "").lower()
    entry_intervals = {str(x).lower() for x in config.get("bos_retest_entry_intervals", ["5m", "15m"])}
    if interval not in entry_intervals:
        return {
            "allowed": False,
            "reason": "bos_retest_interval_not_enabled",
            "interval": interval,
            "entry_intervals": sorted(entry_intervals),
        }

    side = str(candidate.get("side") or "none").lower()
    if side not in {"buy", "sell"}:
        return {"allowed": False, "reason": "bos_retest_missing_side", "side": side}

    analysis = candidate.get("analysis") if isinstance(candidate.get("analysis"), dict) else {}
    scenario = analysis.get("scenario") if isinstance(analysis.get("scenario"), dict) else {}
    levels = scenario.get("levels") if isinstance(scenario.get("levels"), dict) else {}
    technical = analysis.get("technical") if isinstance(analysis.get("technical"), dict) else {}
    fail_open = bool(config.get("bos_retest_fail_open", False))

    try:
        support = float(levels.get("support") or 0.0)
        resistance = float(levels.get("resistance") or 0.0)
        entry = float(candidate.get("entry") or analysis.get("entry_point") or 0.0)
        atr = float(technical.get("atr14") or 0.0)
        last_open = float(technical.get("last_open") or 0.0)
        last_close = float(technical.get("last_close") or 0.0)
        last_high = float(technical.get("last_high") or 0.0)
        last_low = float(technical.get("last_low") or 0.0)
        prev_open = float(technical.get("prev_open") or 0.0)
        prev_close = float(technical.get("prev_close") or 0.0)
    except (TypeError, ValueError):
        return {"allowed": fail_open, "reason": "bos_retest_parse_error", "fail_open": fail_open}

    if support <= 0 or resistance <= 0 or entry <= 0 or atr <= 0:
        return {
            "allowed": fail_open,
            "reason": "bos_retest_missing_levels_or_atr",
            "fail_open": fail_open,
            "support": support,
            "resistance": resistance,
            "entry": entry,
            "atr": atr,
        }

    break_buffer = max(0.0, float(config.get("bos_retest_break_buffer_atr", 0.05) or 0.0)) * atr
    retest_tolerance = max(0.0, float(config.get("bos_retest_retest_tolerance_atr", 0.35) or 0.0)) * atr

    bullish_candle = last_close > last_open
    bearish_candle = last_close < last_open
    bullish_engulfing = bullish_candle and last_close >= prev_open and last_open <= prev_close
    bearish_engulfing = bearish_candle and last_close <= prev_open and last_open >= prev_close
    require_candle = bool(config.get("bos_retest_require_candle_confirmation", True))

    if side == "buy":
        bos_level = resistance
        break_confirmed = last_high >= (bos_level + break_buffer)
        retest_confirmed = (last_low <= (bos_level + retest_tolerance)) and (entry >= bos_level)
        candle_ok = (bullish_candle or bullish_engulfing)
    else:
        bos_level = support
        break_confirmed = last_low <= (bos_level - break_buffer)
        retest_confirmed = (last_high >= (bos_level - retest_tolerance)) and (entry <= bos_level)
        candle_ok = (bearish_candle or bearish_engulfing)

    if not break_confirmed:
        return {
            "allowed": False,
            "reason": "bos_not_confirmed",
            "side": side,
            "bos_level": round(bos_level, 5),
            "break_buffer": round(break_buffer, 5),
            "last_high": round(last_high, 5),
            "last_low": round(last_low, 5),
        }

    if not retest_confirmed:
        return {
            "allowed": False,
            "reason": "retest_not_confirmed",
            "side": side,
            "bos_level": round(bos_level, 5),
            "entry": round(entry, 5),
            "retest_tolerance": round(retest_tolerance, 5),
            "last_high": round(last_high, 5),
            "last_low": round(last_low, 5),
        }

    if require_candle and not candle_ok:
        return {
            "allowed": False,
            "reason": "candle_confirmation_missing",
            "side": side,
            "last_open": round(last_open, 5),
            "last_close": round(last_close, 5),
            "prev_open": round(prev_open, 5),
            "prev_close": round(prev_close, 5),
        }

    return {
        "allowed": True,
        "reason": "bos_retest_confirmed",
        "side": side,
        "bos_level": round(bos_level, 5),
        "entry": round(entry, 5),
        "break_buffer": round(break_buffer, 5),
        "retest_tolerance": round(retest_tolerance, 5),
        "candle_confirmation": candle_ok,
    }


def _analysis_technical_value(analysis: dict, key: str, default: float = 0.0) -> float:
    try:
        technical = analysis.get("technical", {}) if isinstance(analysis, dict) else {}
        return float(technical.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _gold_scalping_analysis(symbol: str, interval: str, analyses_by_key: dict[tuple[str, str], dict]) -> dict:
    key = (str(symbol).upper(), str(interval).lower())
    cached = analyses_by_key.get(key)
    if isinstance(cached, dict):
        return cached
    analysis = perform_full_analysis(key[0], key[1])
    if analysis.get("success"):
        analyses_by_key[key] = analysis
    return analysis


def _gold_scalping_ema_side(analysis: dict, min_gap_pct: float) -> dict:
    if not analysis.get("success", True):
        return {"side": "none", "gap_pct": 0.0, "reason": analysis.get("error") or "analysis_unavailable"}
    ema_fast = _analysis_technical_value(analysis, "ema9")
    ema_slow = _analysis_technical_value(analysis, "ema34")
    if ema_fast <= 0 or ema_slow <= 0:
        return {"side": "none", "gap_pct": 0.0, "reason": "ema_missing"}
    gap_pct = abs(ema_fast - ema_slow) / ema_slow * 100.0
    if gap_pct < max(0.0, float(min_gap_pct or 0.0)):
        return {"side": "neutral", "gap_pct": round(gap_pct, 4), "ema9": ema_fast, "ema34": ema_slow}
    return {
        "side": "buy" if ema_fast > ema_slow else "sell",
        "gap_pct": round(gap_pct, 4),
        "ema9": ema_fast,
        "ema34": ema_slow,
    }


def gold_scalping_quality_gate(config: dict, candidate: dict, analyses_by_key: dict[tuple[str, str], dict]) -> dict:
    if not bool(config.get("gold_scalping_strategy_enabled", False)):
        return {"allowed": True, "reason": "gold_scalping_disabled"}

    symbol = str(candidate.get("symbol") or "").upper()
    if to_base_symbol(symbol) != "XAUUSD":
        return {"allowed": True, "reason": "not_gold"}

    interval = str(candidate.get("interval") or "").lower()
    entry_intervals = {str(item).lower() for item in config.get("gold_scalping_entry_intervals", ["1m", "3m", "5m"])}
    if interval not in entry_intervals:
        return {
            "allowed": False,
            "reason": "gold_scalping_context_interval_not_entry",
            "entry_intervals": sorted(entry_intervals),
        }

    side = str(candidate.get("side") or "none")
    if side not in {"buy", "sell"}:
        return {"allowed": False, "reason": "gold_scalping_no_side"}

    min_entry_gap = int(config.get("gold_scalping_min_entry_score_gap", 35) or 35)
    score_gap = int(candidate.get("score_gap") or 0)
    if score_gap < min_entry_gap:
        return {"allowed": False, "reason": "gold_scalping_score_gap_low", "score_gap": score_gap, "min_score_gap": min_entry_gap}

    context_checks = []
    min_context_gap = float(config.get("gold_scalping_context_min_ema_gap_percent", 0.01) or 0.0)
    for context_interval in config.get("gold_scalping_context_intervals", ["15m"]):
        analysis = _gold_scalping_analysis(symbol, str(context_interval).lower(), analyses_by_key)
        side_check = _gold_scalping_ema_side(analysis, min_context_gap)
        context_checks.append({"interval": str(context_interval).lower(), **side_check})

    aligned = [row for row in context_checks if row.get("side") == side]
    min_agreement = max(0, int(config.get("gold_scalping_min_context_agreement", 1)))
    if len(aligned) < min_agreement:
        return {
            "allowed": False,
            "reason": "gold_scalping_context_not_aligned",
            "entry_side": side,
            "min_context_agreement": min_agreement,
            "context_checks": context_checks,
        }

    analysis = candidate.get("analysis") if isinstance(candidate.get("analysis"), dict) else {}
    entry_price = float(candidate.get("entry") or analysis.get("entry_point") or 0.0)
    atr = _analysis_technical_value(analysis, "atr14")
    ema9 = _analysis_technical_value(analysis, "ema9")
    ema34 = _analysis_technical_value(analysis, "ema34")
    bb_middle = _analysis_technical_value(analysis, "bb_middle")
    bb_upper = _analysis_technical_value(analysis, "bb_upper")
    bb_lower = _analysis_technical_value(analysis, "bb_lower")
    rsi9 = _analysis_technical_value(analysis, "rsi9", 50.0)
    rsi9_previous = _analysis_technical_value(analysis, "rsi9_previous", rsi9)
    volume_ratio = _analysis_technical_value(analysis, "volume_ratio")

    if side == "buy":
        rsi_min = float(config.get("gold_scalping_rsi_buy_min", 38.0))
        rsi_max = float(config.get("gold_scalping_rsi_buy_max", 68.0))
        if not (rsi_min <= rsi9 <= rsi_max):
            return {"allowed": False, "reason": "gold_scalping_rsi_out_of_range", "side": side, "rsi9": rsi9, "min": rsi_min, "max": rsi_max}
        if bool(config.get("gold_scalping_require_rsi_momentum", True)) and rsi9 < rsi9_previous:
            return {"allowed": False, "reason": "gold_scalping_rsi_not_recovering", "side": side, "rsi9": rsi9, "previous": rsi9_previous}
    else:
        rsi_min = float(config.get("gold_scalping_rsi_sell_min", 32.0))
        rsi_max = float(config.get("gold_scalping_rsi_sell_max", 62.0))
        if not (rsi_min <= rsi9 <= rsi_max):
            return {"allowed": False, "reason": "gold_scalping_rsi_out_of_range", "side": side, "rsi9": rsi9, "min": rsi_min, "max": rsi_max}
        if bool(config.get("gold_scalping_require_rsi_momentum", True)) and rsi9 > rsi9_previous:
            return {"allowed": False, "reason": "gold_scalping_rsi_not_falling", "side": side, "rsi9": rsi9, "previous": rsi9_previous}

    reference_prices = [value for value in (ema9, ema34, bb_middle) if value > 0]
    max_distance_atr = float(config.get("gold_scalping_max_entry_distance_atr", 1.4) or 0.0)
    if entry_price > 0 and atr > 0 and reference_prices and max_distance_atr > 0:
        nearest_distance = min(abs(entry_price - value) for value in reference_prices)
        if nearest_distance > atr * max_distance_atr:
            return {
                "allowed": False,
                "reason": "gold_scalping_entry_too_extended",
                "entry": round(entry_price, 5),
                "atr": round(atr, 5),
                "nearest_reference_distance": round(nearest_distance, 5),
                "max_distance_atr": round(max_distance_atr, 3),
            }

    min_volume_ratio = float(config.get("gold_scalping_min_volume_ratio", 0.8) or 0.0)
    if min_volume_ratio > 0 and volume_ratio > 0 and volume_ratio < min_volume_ratio:
        return {
            "allowed": False,
            "reason": "gold_scalping_volume_weak",
            "volume_ratio": round(volume_ratio, 3),
            "min_volume_ratio": round(min_volume_ratio, 3),
        }

    if bool(config.get("gold_scalping_skip_bollinger_extreme", True)) and entry_price > 0:
        strong_volume = volume_ratio >= max(1.2, min_volume_ratio)
        if side == "buy" and bb_upper > 0 and entry_price > bb_upper and not strong_volume:
            return {"allowed": False, "reason": "gold_scalping_buy_above_bollinger_without_volume", "entry": round(entry_price, 5), "bb_upper": round(bb_upper, 5), "volume_ratio": round(volume_ratio, 3)}
        if side == "sell" and bb_lower > 0 and entry_price < bb_lower and not strong_volume:
            return {"allowed": False, "reason": "gold_scalping_sell_below_bollinger_without_volume", "entry": round(entry_price, 5), "bb_lower": round(bb_lower, 5), "volume_ratio": round(volume_ratio, 3)}

    return {
        "allowed": True,
        "reason": "gold_scalping_filter_passed",
        "entry_side": side,
        "context_checks": context_checks,
        "rsi9": rsi9,
        "rsi9_previous": rsi9_previous,
        "volume_ratio": round(volume_ratio, 3),
    }


def apply_gold_scalping_atr_levels(
    config: dict,
    bridge: MT5Bridge,
    candidate: dict,
    entry_price: float,
    stop_price: float,
    tp1_price: float,
    tp2_price: float,
    tp3_price: float,
    analyses_by_key: dict[tuple[str, str], dict],
) -> tuple[float, float, float, float, dict | None]:
    if not bool(config.get("gold_scalping_strategy_enabled", False)):
        return stop_price, tp1_price, tp2_price, tp3_price, None

    symbol = str(candidate.get("symbol") or "").upper()
    if to_base_symbol(symbol) != "XAUUSD":
        return stop_price, tp1_price, tp2_price, tp3_price, None

    reference_interval = str(config.get("gold_scalping_atr_reference_interval", "5m") or "5m").lower()
    reference_analysis = _gold_scalping_analysis(symbol, reference_interval, analyses_by_key)
    if not reference_analysis.get("success"):
        reference_analysis = candidate.get("analysis") if isinstance(candidate.get("analysis"), dict) else {}

    atr = _analysis_technical_value(reference_analysis, "atr14")
    if atr <= 0:
        return stop_price, tp1_price, tp2_price, tp3_price, None

    multiplier = float(config.get("gold_scalping_stop_atr_multiplier", 1.0) or 1.0)
    stop_distance = atr * multiplier
    min_distance = float(config.get("gold_scalping_min_stop_price_distance", 0.0) or 0.0)
    max_distance = float(config.get("gold_scalping_max_stop_price_distance", 0.0) or 0.0)
    if min_distance > 0:
        stop_distance = max(stop_distance, min_distance)
    if max_distance > 0:
        stop_distance = min(stop_distance, max_distance)

    tp1_rr = max(0.1, float(config.get("gold_scalping_tp1_rr", 1.0) or 1.0))
    tp2_rr = max(tp1_rr, float(config.get("gold_scalping_tp2_rr", 1.5) or 1.5))
    tp3_rr = max(tp2_rr, float(config.get("gold_scalping_tp3_rr", 2.0) or 2.0))
    side = str(candidate.get("side") or "")

    if side == "buy":
        stop_price = round_broker_price(bridge, symbol, entry_price - stop_distance)
        tp1_price = round_broker_price(bridge, symbol, entry_price + (stop_distance * tp1_rr))
        tp2_price = round_broker_price(bridge, symbol, entry_price + (stop_distance * tp2_rr))
        tp3_price = round_broker_price(bridge, symbol, entry_price + (stop_distance * tp3_rr))
    elif side == "sell":
        stop_price = round_broker_price(bridge, symbol, entry_price + stop_distance)
        tp1_price = round_broker_price(bridge, symbol, entry_price - (stop_distance * tp1_rr))
        tp2_price = round_broker_price(bridge, symbol, entry_price - (stop_distance * tp2_rr))
        tp3_price = round_broker_price(bridge, symbol, entry_price - (stop_distance * tp3_rr))
    else:
        return stop_price, tp1_price, tp2_price, tp3_price, None

    return stop_price, tp1_price, tp2_price, tp3_price, {
        "reference_interval": reference_interval,
        "atr": round(atr, 5),
        "stop_distance": round(stop_distance, 5),
        "tp_rr": [round(tp1_rr, 3), round(tp2_rr, 3), round(tp3_rr, 3)],
    }


def gold_scalping_spread_check(bridge: MT5Bridge, config: dict, symbol: str, risk_distance: float) -> dict:
    if not bool(config.get("gold_scalping_strategy_enabled", False)) or to_base_symbol(symbol) != "XAUUSD":
        return {"allowed": True, "reason": "gold_scalping_spread_check_disabled"}
    max_ratio = float(config.get("gold_scalping_max_spread_to_stop", 0.18) or 0.0)
    if max_ratio <= 0 or risk_distance <= 0:
        return {"allowed": True, "reason": "gold_scalping_spread_limit_disabled"}
    resolved = bridge._resolve_symbol_name(symbol)
    tick = bridge._get_tick(resolved) if resolved else None
    if tick is None:
        return {"allowed": True, "reason": "gold_scalping_tick_unavailable"}
    spread = abs(float(tick.ask) - float(tick.bid))
    ratio = spread / risk_distance if risk_distance > 0 else 0.0
    if ratio > max_ratio:
        return {
            "allowed": False,
            "reason": "gold_scalping_spread_too_wide",
            "spread": round(spread, 5),
            "risk_distance": round(risk_distance, 5),
            "spread_to_stop": round(ratio, 3),
            "max_spread_to_stop": round(max_ratio, 3),
        }
    return {
        "allowed": True,
        "reason": "gold_scalping_spread_ok",
        "spread": round(spread, 5),
        "risk_distance": round(risk_distance, 5),
        "spread_to_stop": round(ratio, 3),
    }


def apply_gold_fixed_tp_after_spread(
    bridge: MT5Bridge,
    config: dict,
    symbol: str,
    side: str,
    entry_price: float,
    tp1_price: float,
    tp2_price: float,
    tp3_price: float,
) -> tuple[float, float, float, dict | None]:
    if to_base_symbol(symbol) != "XAUUSD":
        return tp1_price, tp2_price, tp3_price, None

    connection_error = bridge._ensure_connection()
    if connection_error:
        return tp1_price, tp2_price, tp3_price, None

    points = float(config.get("gold_fixed_tp_after_spread_points", 0.0) or 0.0)
    if points <= 0:
        return tp1_price, tp2_price, tp3_price, None

    resolved_symbol = bridge._resolve_symbol_name(symbol)
    tick = bridge._get_tick(resolved_symbol) if resolved_symbol else None
    info = mt5.symbol_info(resolved_symbol) if (mt5 is not None and resolved_symbol) else None
    point = float(getattr(info, "point", 0.0) or 0.0)
    if tick is None or point <= 0:
        return tp1_price, tp2_price, tp3_price, None

    spread = abs(float(tick.ask) - float(tick.bid))
    target_distance = spread + (points * point)
    if target_distance <= 0:
        return tp1_price, tp2_price, tp3_price, None

    side = str(side or "").lower().strip()
    if side == "buy":
        target_price = round_broker_price(bridge, symbol, entry_price + target_distance)
    elif side == "sell":
        target_price = round_broker_price(bridge, symbol, entry_price - target_distance)
    else:
        return tp1_price, tp2_price, tp3_price, None

    return target_price, target_price, target_price, {
        "mode": "gold_fixed_tp_after_spread",
        "spread": round(spread, 5),
        "point": round(point, 6),
        "tp_points": round(points, 2),
        "target_distance": round(target_distance, 5),
    }


def tick_confirmation_check(
    bridge: MT5Bridge,
    config: dict,
    symbol: str,
    side: str,
    risk_distance: float,
) -> dict:
    if not bool(config.get("tick_confirmation_enabled", False)):
        return {"allowed": True, "reason": "tick_confirmation_disabled"}

    side = str(side or "").lower().strip()
    if side not in {"buy", "sell"}:
        return {"allowed": False, "reason": "tick_confirmation_invalid_side", "side": side}

    connection_error = bridge._ensure_connection()
    if connection_error:
        return {"allowed": False, "reason": "tick_confirmation_connection_error", "error": connection_error.get("error")}

    resolved = bridge._resolve_symbol_name(symbol)
    if not resolved:
        return {"allowed": False, "reason": "tick_confirmation_symbol_unavailable", "symbol": symbol}

    info = mt5.symbol_info(resolved) if mt5 is not None else None
    point = float(getattr(info, "point", 0.0) or 0.0)
    min_move = max(0.0, float(config.get("tick_confirmation_min_move_points", 1.0) or 0.0)) * max(point, 0.0)
    samples_count = max(1, min(6, int(config.get("tick_confirmation_samples", 3) or 3)))
    delay_sec = max(0.0, min(1.0, float(config.get("tick_confirmation_sample_delay_ms", 250) or 0.0) / 1000.0))
    max_tick_age_sec = max(0.0, float(config.get("tick_confirmation_max_tick_age_sec", 5.0) or 0.0))
    max_spread_ratio = max(0.0, float(config.get("tick_confirmation_max_spread_to_stop", 0.18) or 0.0))
    require_direction = bool(config.get("tick_confirmation_require_direction", True))

    mids = []
    spreads = []
    tick_times = []
    for idx in range(samples_count):
        tick = bridge._get_tick(resolved)
        if tick is None:
            return {"allowed": False, "reason": "tick_confirmation_tick_unavailable", "symbol": symbol}
        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
        if bid <= 0 or ask <= 0 or ask < bid:
            return {"allowed": False, "reason": "tick_confirmation_invalid_tick", "bid": bid, "ask": ask}
        mids.append((bid + ask) / 2.0)
        spreads.append(ask - bid)
        tick_times.append(int(getattr(tick, "time", 0) or 0))
        if idx < samples_count - 1 and delay_sec > 0:
            time.sleep(delay_sec)

    latest_tick_time = tick_times[-1] if tick_times else 0
    tick_age_sec = max(0.0, time.time() - latest_tick_time) if latest_tick_time > 0 else 0.0
    if max_tick_age_sec > 0 and latest_tick_time > 0 and tick_age_sec > max_tick_age_sec:
        return {
            "allowed": False,
            "reason": "tick_confirmation_stale_tick",
            "tick_age_sec": round(tick_age_sec, 3),
            "max_tick_age_sec": round(max_tick_age_sec, 3),
        }

    latest_spread = spreads[-1] if spreads else 0.0
    spread_ratio = (latest_spread / risk_distance) if risk_distance > 0 else 0.0
    if max_spread_ratio > 0 and risk_distance > 0 and spread_ratio > max_spread_ratio:
        return {
            "allowed": False,
            "reason": "tick_confirmation_spread_too_wide",
            "spread": round(latest_spread, 5),
            "risk_distance": round(risk_distance, 5),
            "spread_to_stop": round(spread_ratio, 3),
            "max_spread_to_stop": round(max_spread_ratio, 3),
        }

    move = (mids[-1] - mids[0]) if len(mids) >= 2 else 0.0
    if require_direction:
        if side == "buy" and move < min_move:
            return {
                "allowed": False,
                "reason": "tick_confirmation_buy_not_rising",
                "tick_move": round(move, 5),
                "min_move": round(min_move, 5),
                "samples": samples_count,
            }
        if side == "sell" and move > -min_move:
            return {
                "allowed": False,
                "reason": "tick_confirmation_sell_not_falling",
                "tick_move": round(move, 5),
                "min_move": round(min_move, 5),
                "samples": samples_count,
            }
    else:
        if side == "buy" and move < -min_move:
            return {"allowed": False, "reason": "tick_confirmation_buy_reversing", "tick_move": round(move, 5)}
        if side == "sell" and move > min_move:
            return {"allowed": False, "reason": "tick_confirmation_sell_reversing", "tick_move": round(move, 5)}

    return {
        "allowed": True,
        "reason": "tick_confirmation_ok",
        "tick_move": round(move, 5),
        "spread": round(latest_spread, 5),
        "spread_to_stop": round(spread_ratio, 3) if risk_distance > 0 else None,
        "samples": samples_count,
    }


def forex_scalping_quality_gate(config: dict, candidate: dict, analyses_by_key: dict[tuple[str, str], dict]) -> dict:
    if not bool(config.get("forex_scalping_strategy_enabled", False)):
        return {"allowed": True, "reason": "forex_scalping_disabled"}

    symbol = str(candidate.get("symbol") or "").upper()
    if to_base_symbol(symbol) == "XAUUSD":
        return {"allowed": True, "reason": "gold_uses_gold_scalping_filter"}

    interval = str(candidate.get("interval") or "").lower()
    entry_intervals = {str(item).lower() for item in config.get("forex_scalping_entry_intervals", ["1m", "3m", "5m"])}
    if interval not in entry_intervals:
        return {
            "allowed": False,
            "reason": "forex_scalping_context_interval_not_entry",
            "entry_intervals": sorted(entry_intervals),
        }

    side = str(candidate.get("side") or "none")
    if side not in {"buy", "sell"}:
        return {"allowed": False, "reason": "forex_scalping_no_side"}

    min_entry_gap = int(config.get("forex_scalping_min_entry_score_gap", 35) or 35)
    score_gap = int(candidate.get("score_gap") or 0)
    if score_gap < min_entry_gap:
        return {"allowed": False, "reason": "forex_scalping_score_gap_low", "score_gap": score_gap, "min_score_gap": min_entry_gap}

    context_checks = []
    min_context_gap = float(config.get("forex_scalping_context_min_ema_gap_percent", 0.005) or 0.0)
    for context_interval in config.get("forex_scalping_context_intervals", ["15m"]):
        analysis = _gold_scalping_analysis(symbol, str(context_interval).lower(), analyses_by_key)
        side_check = _gold_scalping_ema_side(analysis, min_context_gap)
        context_checks.append({"interval": str(context_interval).lower(), **side_check})

    aligned = [row for row in context_checks if row.get("side") == side]
    min_agreement = int(config.get("forex_scalping_min_context_agreement", 1) or 1)
    if len(aligned) < min_agreement:
        return {
            "allowed": False,
            "reason": "forex_scalping_context_not_aligned",
            "entry_side": side,
            "min_context_agreement": min_agreement,
            "context_checks": context_checks,
        }

    analysis = candidate.get("analysis") if isinstance(candidate.get("analysis"), dict) else {}
    entry_price = float(candidate.get("entry") or analysis.get("entry_point") or 0.0)
    atr = _analysis_technical_value(analysis, "atr14")
    ema9 = _analysis_technical_value(analysis, "ema9")
    ema34 = _analysis_technical_value(analysis, "ema34")
    bb_middle = _analysis_technical_value(analysis, "bb_middle")
    bb_upper = _analysis_technical_value(analysis, "bb_upper")
    bb_lower = _analysis_technical_value(analysis, "bb_lower")
    rsi9 = _analysis_technical_value(analysis, "rsi9", 50.0)
    rsi9_previous = _analysis_technical_value(analysis, "rsi9_previous", rsi9)
    volume_ratio = _analysis_technical_value(analysis, "volume_ratio")

    if side == "buy":
        rsi_min = float(config.get("forex_scalping_rsi_buy_min", 38.0) or 38.0)
        rsi_max = float(config.get("forex_scalping_rsi_buy_max", 68.0) or 68.0)
        if not (rsi_min <= rsi9 <= rsi_max):
            return {"allowed": False, "reason": "forex_scalping_rsi_out_of_range", "side": side, "rsi9": rsi9, "min": rsi_min, "max": rsi_max}
        if bool(config.get("forex_scalping_require_rsi_momentum", True)) and rsi9 < rsi9_previous:
            return {"allowed": False, "reason": "forex_scalping_rsi_not_recovering", "side": side, "rsi9": rsi9, "previous": rsi9_previous}
    else:
        rsi_min = float(config.get("forex_scalping_rsi_sell_min", 32.0) or 32.0)
        rsi_max = float(config.get("forex_scalping_rsi_sell_max", 62.0) or 62.0)
        if not (rsi_min <= rsi9 <= rsi_max):
            return {"allowed": False, "reason": "forex_scalping_rsi_out_of_range", "side": side, "rsi9": rsi9, "min": rsi_min, "max": rsi_max}
        if bool(config.get("forex_scalping_require_rsi_momentum", True)) and rsi9 > rsi9_previous:
            return {"allowed": False, "reason": "forex_scalping_rsi_not_falling", "side": side, "rsi9": rsi9, "previous": rsi9_previous}

    reference_prices = [value for value in (ema9, ema34, bb_middle) if value > 0]
    max_distance_atr = float(config.get("forex_scalping_max_entry_distance_atr", 1.6) or 0.0)
    if entry_price > 0 and atr > 0 and reference_prices and max_distance_atr > 0:
        nearest_distance = min(abs(entry_price - value) for value in reference_prices)
        if nearest_distance > atr * max_distance_atr:
            return {
                "allowed": False,
                "reason": "forex_scalping_entry_too_extended",
                "entry": round(entry_price, 5),
                "atr": round(atr, 5),
                "nearest_reference_distance": round(nearest_distance, 5),
                "max_distance_atr": round(max_distance_atr, 3),
            }

    min_volume_ratio = float(config.get("forex_scalping_min_volume_ratio", 0.0) or 0.0)
    if min_volume_ratio > 0 and volume_ratio > 0 and volume_ratio < min_volume_ratio:
        return {
            "allowed": False,
            "reason": "forex_scalping_volume_weak",
            "volume_ratio": round(volume_ratio, 3),
            "min_volume_ratio": round(min_volume_ratio, 3),
        }

    if bool(config.get("forex_scalping_skip_bollinger_extreme", True)) and entry_price > 0:
        strong_volume = volume_ratio >= max(1.2, min_volume_ratio)
        if side == "buy" and bb_upper > 0 and entry_price > bb_upper and not strong_volume:
            return {"allowed": False, "reason": "forex_scalping_buy_above_bollinger_without_volume", "entry": round(entry_price, 5), "bb_upper": round(bb_upper, 5), "volume_ratio": round(volume_ratio, 3)}
        if side == "sell" and bb_lower > 0 and entry_price < bb_lower and not strong_volume:
            return {"allowed": False, "reason": "forex_scalping_sell_below_bollinger_without_volume", "entry": round(entry_price, 5), "bb_lower": round(bb_lower, 5), "volume_ratio": round(volume_ratio, 3)}

    return {
        "allowed": True,
        "reason": "forex_scalping_filter_passed",
        "entry_side": side,
        "context_checks": context_checks,
        "rsi9": rsi9,
        "rsi9_previous": rsi9_previous,
        "volume_ratio": round(volume_ratio, 3),
    }


def apply_forex_scalping_atr_levels(
    config: dict,
    bridge: MT5Bridge,
    candidate: dict,
    entry_price: float,
    stop_price: float,
    tp1_price: float,
    tp2_price: float,
    tp3_price: float,
    analyses_by_key: dict[tuple[str, str], dict],
) -> tuple[float, float, float, float, dict | None]:
    if not bool(config.get("forex_scalping_strategy_enabled", False)):
        return stop_price, tp1_price, tp2_price, tp3_price, None

    symbol = str(candidate.get("symbol") or "").upper()
    if to_base_symbol(symbol) == "XAUUSD":
        return stop_price, tp1_price, tp2_price, tp3_price, None

    reference_interval = str(config.get("forex_scalping_atr_reference_interval", "5m") or "5m").lower()
    reference_analysis = _gold_scalping_analysis(symbol, reference_interval, analyses_by_key)
    if not reference_analysis.get("success"):
        reference_analysis = candidate.get("analysis") if isinstance(candidate.get("analysis"), dict) else {}

    atr = _analysis_technical_value(reference_analysis, "atr14")
    if atr <= 0:
        return stop_price, tp1_price, tp2_price, tp3_price, None

    multiplier = float(config.get("forex_scalping_stop_atr_multiplier", 0.9) or 0.9)
    stop_distance = atr * multiplier
    min_distance = float(config.get("forex_scalping_min_stop_price_distance", 0.0) or 0.0)
    max_distance = float(config.get("forex_scalping_max_stop_price_distance", 0.0) or 0.0)
    if min_distance > 0:
        stop_distance = max(stop_distance, min_distance)
    if max_distance > 0:
        stop_distance = min(stop_distance, max_distance)

    tp1_rr = max(0.1, float(config.get("forex_scalping_tp1_rr", 1.0) or 1.0))
    tp2_rr = max(tp1_rr, float(config.get("forex_scalping_tp2_rr", 1.5) or 1.5))
    tp3_rr = max(tp2_rr, float(config.get("forex_scalping_tp3_rr", 2.0) or 2.0))
    side = str(candidate.get("side") or "")

    if side == "buy":
        stop_price = round_broker_price(bridge, symbol, entry_price - stop_distance)
        tp1_price = round_broker_price(bridge, symbol, entry_price + (stop_distance * tp1_rr))
        tp2_price = round_broker_price(bridge, symbol, entry_price + (stop_distance * tp2_rr))
        tp3_price = round_broker_price(bridge, symbol, entry_price + (stop_distance * tp3_rr))
    elif side == "sell":
        stop_price = round_broker_price(bridge, symbol, entry_price + stop_distance)
        tp1_price = round_broker_price(bridge, symbol, entry_price - (stop_distance * tp1_rr))
        tp2_price = round_broker_price(bridge, symbol, entry_price - (stop_distance * tp2_rr))
        tp3_price = round_broker_price(bridge, symbol, entry_price - (stop_distance * tp3_rr))
    else:
        return stop_price, tp1_price, tp2_price, tp3_price, None

    return stop_price, tp1_price, tp2_price, tp3_price, {
        "reference_interval": reference_interval,
        "atr": round(atr, 6),
        "stop_distance": round(stop_distance, 6),
        "tp_rr": [round(tp1_rr, 3), round(tp2_rr, 3), round(tp3_rr, 3)],
    }


def forex_scalping_spread_check(bridge: MT5Bridge, config: dict, symbol: str, risk_distance: float) -> dict:
    if not bool(config.get("forex_scalping_strategy_enabled", False)) or to_base_symbol(symbol) == "XAUUSD":
        return {"allowed": True, "reason": "forex_scalping_spread_check_disabled"}
    max_ratio = float(config.get("forex_scalping_max_spread_to_stop", 0.18) or 0.0)
    if max_ratio <= 0 or risk_distance <= 0:
        return {"allowed": True, "reason": "forex_scalping_spread_limit_disabled"}
    resolved = bridge._resolve_symbol_name(symbol)
    tick = bridge._get_tick(resolved) if resolved else None
    if tick is None:
        return {"allowed": True, "reason": "forex_scalping_tick_unavailable"}
    spread = abs(float(tick.ask) - float(tick.bid))
    ratio = spread / risk_distance if risk_distance > 0 else 0.0
    if ratio > max_ratio:
        return {
            "allowed": False,
            "reason": "forex_scalping_spread_too_wide",
            "spread": round(spread, 6),
            "risk_distance": round(risk_distance, 6),
            "spread_to_stop": round(ratio, 3),
            "max_spread_to_stop": round(max_ratio, 3),
        }
    return {
        "allowed": True,
        "reason": "forex_scalping_spread_ok",
        "spread": round(spread, 6),
        "risk_distance": round(risk_distance, 6),
        "spread_to_stop": round(ratio, 3),
    }


def resolve_effective_max_open_positions(config: dict) -> dict:
    static_max = int(config.get("max_open_positions", 0))
    dynamic_enabled = bool(config.get("dynamic_max_positions_enabled", False))
    risk_per_trade = max(0.1, float(config.get("risk_percent", 1.0) or 1.0))
    max_total_risk = max(risk_per_trade, float(config.get("max_total_open_risk_percent", 2.1) or 2.1))
    min_open = int(config.get("min_open_positions", 1) or 1)
    cap = int(config.get("max_open_positions_cap", 0) or 0)

    if not dynamic_enabled:
        return {
            "effective_max_open_positions": static_max,
            "source": "static",
            "risk_per_trade": risk_per_trade,
            "max_total_risk": max_total_risk,
            "min_open": min_open,
            "cap": cap,
        }

    dynamic_max = int(math.floor(max_total_risk / risk_per_trade))
    dynamic_max = max(min_open, dynamic_max)

    if cap > 0:
        dynamic_max = min(dynamic_max, cap)

    if static_max > 0:
        dynamic_max = min(dynamic_max, static_max)

    return {
        "effective_max_open_positions": dynamic_max,
        "source": "dynamic_risk_percent",
        "risk_per_trade": round(risk_per_trade, 4),
        "max_total_risk": round(max_total_risk, 4),
        "min_open": min_open,
        "cap": cap,
    }


def list_pending_orders_by_magic(magic: int) -> list[dict]:
    if mt5 is None:
        return []
    rows = mt5.orders_get() or []
    out = []
    for row in rows:
        if int(getattr(row, "magic", 0) or 0) != int(magic):
            continue
        out.append(row._asdict())
    return out


def list_pending_order_tickets_by_magic(magic: int) -> set[int]:
    if mt5 is None:
        return set()
    tickets = set()
    for row in list_pending_orders_by_magic(magic):
        tickets.add(int(row.get("ticket", 0) or 0))
    return tickets


def extract_pending_order_tickets(execution: dict) -> list[int]:
    tickets = []
    if not execution:
        return tickets

    orders = execution.get("orders")
    if isinstance(orders, list):
        for one in orders:
            result = one.get("result") if isinstance(one, dict) else None
            if isinstance(result, dict):
                ticket = int(result.get("order", 0) or 0)
                if ticket > 0:
                    tickets.append(ticket)
    else:
        result = execution.get("result") if isinstance(execution, dict) else None
        if isinstance(result, dict):
            ticket = int(result.get("order", 0) or 0)
            if ticket > 0:
                tickets.append(ticket)
    return tickets


def apply_trailing_stop(bridge: MT5Bridge, open_positions: list[dict], config: dict) -> list[dict]:
    """Move SL to lock in profit once a position reaches the configured profit threshold.

    Config keys:
        trailing_stop_enabled       (bool, default False)
        trailing_stop_breakeven_trigger_rr (float, default 0.15) – move SL to entry after small profit
        trailing_stop_breakeven_buffer_rr  (float, default 0.0)  – optional profit buffer beyond entry
        trailing_stop_trigger_rr    (float, default 1.0)  – activate when profit ≥ 1×SL-distance
        trailing_stop_lock_rr       (float, default 0.5)  – lock in this fraction of profit as new SL
        trailing_stop_breakeven     (bool, default True)   – move SL to entry (breakeven) first
    """
    actions = []
    if not bool(config.get("trailing_stop_enabled", False)):
        return actions

    dry_run = bool(config.get("dry_run", True))
    trigger_rr = float(config.get("trailing_stop_trigger_rr", 1.0))
    lock_rr = float(config.get("trailing_stop_lock_rr", 0.5))
    breakeven = bool(config.get("trailing_stop_breakeven", True))
    breakeven_trigger_rr = max(0.0, float(config.get("trailing_stop_breakeven_trigger_rr", 0.15)))
    breakeven_buffer_rr = max(0.0, float(config.get("trailing_stop_breakeven_buffer_rr", 0.0)))
    no_loss_enabled = bool(config.get("no_loss_after_profit_enabled", True))
    no_loss_trigger_rr = max(0.0, float(config.get("no_loss_after_profit_trigger_rr", 0.05)))
    no_loss_buffer_rr = max(0.0, float(config.get("no_loss_after_profit_buffer_rr", 0.02)))
    tp_step_guard_enabled = bool(config.get("tp_step_guard_enabled", True))
    tp1_trigger_rr = max(0.0, float(config.get("tp1_trigger_rr", 1.0) or 1.0))
    tp2_trigger_rr = max(tp1_trigger_rr, float(config.get("tp2_trigger_rr", 2.0) or 2.0))
    tp3_trigger_rr = max(tp2_trigger_rr, float(config.get("tp3_trigger_rr", 3.0) or 3.0))
    tp1_lock_rr = max(0.0, float(config.get("tp1_lock_rr", 0.5) or 0.5))
    tp2_lock_rr = max(tp1_lock_rr, float(config.get("tp2_lock_rr", 1.5) or 1.5))
    tp3_lock_rr = max(tp2_lock_rr, float(config.get("tp3_lock_rr", 2.5) or 2.5))

    for pos in open_positions:
        try:
            ticket = int(pos.get("ticket") or pos.get("identifier") or 0)
            if ticket <= 0:
                continue

            entry = float(pos.get("price_open") or 0.0)
            current_sl = float(pos.get("sl") or 0.0)
            current_price = float(pos.get("price_current") or 0.0)
            pos_type = int(pos.get("type") or 0)  # 0=BUY, 1=SELL

            if entry <= 0 or current_sl <= 0 or current_price <= 0:
                continue

            sl_distance = abs(entry - current_sl)
            if sl_distance <= 0:
                continue

            if pos_type == 0:  # BUY
                profit_distance = current_price - entry
                if tp_step_guard_enabled:
                    step_target_rr = None
                    step_trigger_rr = None
                    step_name = ""
                    if profit_distance >= tp3_trigger_rr * sl_distance:
                        step_target_rr = min(tp3_lock_rr, tp3_trigger_rr)
                        step_trigger_rr = tp3_trigger_rr
                        step_name = "tp3"
                    elif profit_distance >= tp2_trigger_rr * sl_distance:
                        step_target_rr = min(tp2_lock_rr, tp2_trigger_rr)
                        step_trigger_rr = tp2_trigger_rr
                        step_name = "tp2"
                    elif profit_distance >= tp1_trigger_rr * sl_distance:
                        step_target_rr = min(tp1_lock_rr, tp1_trigger_rr)
                        step_trigger_rr = tp1_trigger_rr
                        step_name = "tp1"

                    if step_target_rr is not None:
                        step_sl = entry + (step_target_rr * sl_distance)
                        if step_sl > current_sl:
                            result = bridge.modify_position_sl_tp(ticket=ticket, sl=step_sl, dry_run=dry_run)
                            actions.append({
                                "event": "tp_step_guard_lock",
                                "stage": step_name,
                                "ticket": ticket,
                                "symbol": pos.get("symbol"),
                                "old_sl": round(current_sl, 5),
                                "new_sl": round(step_sl, 5),
                                "profit_distance": round(profit_distance, 5),
                                "trigger_rr": round(step_trigger_rr or 0.0, 3),
                                "lock_rr": round(step_target_rr, 3),
                                "success": result.get("success"),
                                "error": result.get("error"),
                                "dry_run": dry_run,
                            })
                            continue

                if no_loss_enabled and profit_distance >= no_loss_trigger_rr * sl_distance:
                    no_loss_sl = entry + (no_loss_buffer_rr * sl_distance)
                    if no_loss_sl > current_sl:
                        result = bridge.modify_position_sl_tp(ticket=ticket, sl=no_loss_sl, dry_run=dry_run)
                        actions.append({
                            "event": "no_loss_after_profit_lock",
                            "ticket": ticket,
                            "symbol": pos.get("symbol"),
                            "old_sl": round(current_sl, 5),
                            "new_sl": round(no_loss_sl, 5),
                            "profit_distance": round(profit_distance, 5),
                            "trigger_rr": round(no_loss_trigger_rr, 3),
                            "buffer_rr": round(no_loss_buffer_rr, 3),
                            "success": result.get("success"),
                            "error": result.get("error"),
                            "dry_run": dry_run,
                        })
                        continue
                if breakeven and current_sl < entry and profit_distance >= breakeven_trigger_rr * sl_distance:
                    new_sl = entry + (breakeven_buffer_rr * sl_distance)
                    result = bridge.modify_position_sl_tp(ticket=ticket, sl=new_sl, dry_run=dry_run)
                    actions.append({
                        "event": "trailing_stop_breakeven",
                        "ticket": ticket,
                        "symbol": pos.get("symbol"),
                        "old_sl": round(current_sl, 5),
                        "new_sl": round(new_sl, 5),
                        "profit_distance": round(profit_distance, 5),
                        "success": result.get("success"),
                        "error": result.get("error"),
                        "dry_run": dry_run,
                    })
                    continue
                # trigger: profit ≥ trigger_rr × SL-distance
                if profit_distance < trigger_rr * sl_distance:
                    continue
                # new SL = entry + lock_rr × profit_distance (lock in portion)
                new_sl_candidate = entry + lock_rr * profit_distance
                # also ensure breakeven at minimum
                if breakeven:
                    new_sl_candidate = max(new_sl_candidate, entry)
                # only move SL forward (never back)
                if new_sl_candidate <= current_sl:
                    continue
                new_sl = new_sl_candidate

            else:  # SELL
                profit_distance = entry - current_price
                if tp_step_guard_enabled:
                    step_target_rr = None
                    step_trigger_rr = None
                    step_name = ""
                    if profit_distance >= tp3_trigger_rr * sl_distance:
                        step_target_rr = min(tp3_lock_rr, tp3_trigger_rr)
                        step_trigger_rr = tp3_trigger_rr
                        step_name = "tp3"
                    elif profit_distance >= tp2_trigger_rr * sl_distance:
                        step_target_rr = min(tp2_lock_rr, tp2_trigger_rr)
                        step_trigger_rr = tp2_trigger_rr
                        step_name = "tp2"
                    elif profit_distance >= tp1_trigger_rr * sl_distance:
                        step_target_rr = min(tp1_lock_rr, tp1_trigger_rr)
                        step_trigger_rr = tp1_trigger_rr
                        step_name = "tp1"

                    if step_target_rr is not None:
                        step_sl = entry - (step_target_rr * sl_distance)
                        if step_sl < current_sl:
                            result = bridge.modify_position_sl_tp(ticket=ticket, sl=step_sl, dry_run=dry_run)
                            actions.append({
                                "event": "tp_step_guard_lock",
                                "stage": step_name,
                                "ticket": ticket,
                                "symbol": pos.get("symbol"),
                                "old_sl": round(current_sl, 5),
                                "new_sl": round(step_sl, 5),
                                "profit_distance": round(profit_distance, 5),
                                "trigger_rr": round(step_trigger_rr or 0.0, 3),
                                "lock_rr": round(step_target_rr, 3),
                                "success": result.get("success"),
                                "error": result.get("error"),
                                "dry_run": dry_run,
                            })
                            continue

                if no_loss_enabled and profit_distance >= no_loss_trigger_rr * sl_distance:
                    no_loss_sl = entry - (no_loss_buffer_rr * sl_distance)
                    if no_loss_sl < current_sl:
                        result = bridge.modify_position_sl_tp(ticket=ticket, sl=no_loss_sl, dry_run=dry_run)
                        actions.append({
                            "event": "no_loss_after_profit_lock",
                            "ticket": ticket,
                            "symbol": pos.get("symbol"),
                            "old_sl": round(current_sl, 5),
                            "new_sl": round(no_loss_sl, 5),
                            "profit_distance": round(profit_distance, 5),
                            "trigger_rr": round(no_loss_trigger_rr, 3),
                            "buffer_rr": round(no_loss_buffer_rr, 3),
                            "success": result.get("success"),
                            "error": result.get("error"),
                            "dry_run": dry_run,
                        })
                        continue
                if breakeven and (current_sl <= 0 or current_sl > entry) and profit_distance >= breakeven_trigger_rr * sl_distance:
                    new_sl = entry - (breakeven_buffer_rr * sl_distance)
                    result = bridge.modify_position_sl_tp(ticket=ticket, sl=new_sl, dry_run=dry_run)
                    actions.append({
                        "event": "trailing_stop_breakeven",
                        "ticket": ticket,
                        "symbol": pos.get("symbol"),
                        "old_sl": round(current_sl, 5),
                        "new_sl": round(new_sl, 5),
                        "profit_distance": round(profit_distance, 5),
                        "success": result.get("success"),
                        "error": result.get("error"),
                        "dry_run": dry_run,
                    })
                    continue
                if profit_distance < trigger_rr * sl_distance:
                    continue
                new_sl_candidate = entry - lock_rr * profit_distance
                if breakeven:
                    new_sl_candidate = min(new_sl_candidate, entry)
                if new_sl_candidate >= current_sl:
                    continue
                new_sl = new_sl_candidate

            result = bridge.modify_position_sl_tp(ticket=ticket, sl=new_sl, dry_run=dry_run)
            actions.append({
                "event": "trailing_stop_updated",
                "ticket": ticket,
                "symbol": pos.get("symbol"),
                "old_sl": round(current_sl, 5),
                "new_sl": round(new_sl, 5),
                "profit_distance": round(profit_distance, 5),
                "success": result.get("success"),
                "error": result.get("error"),
                "dry_run": dry_run,
            })
        except Exception as e:
            actions.append({"event": "trailing_stop_error", "ticket": ticket, "error": str(e)})

    return actions


def cleanup_expired_pending_orders(bridge: MT5Bridge, state: dict, now_ts: int) -> list[dict]:
    actions = []
    pending_state = state.setdefault("pending_orders", {})
    if not isinstance(pending_state, dict):
        state["pending_orders"] = {}
        pending_state = state["pending_orders"]

    live_tickets = list_pending_order_tickets_by_magic(bridge.magic)
    remove_keys = []

    for ticket_str, meta in pending_state.items():
        ticket = int(ticket_str)
        expires_at = int((meta or {}).get("expires_at", 0) or 0)

        if ticket not in live_tickets:
            remove_keys.append(ticket_str)
            actions.append({"event": "pending_state_pruned", "ticket": ticket})
            continue

        if expires_at > 0 and now_ts >= expires_at:
            res = bridge.cancel_pending_order(ticket=ticket, dry_run=False)
            ok = bool(res.get("success"))
            actions.append(
                {
                    "event": "pending_expired_cancel",
                    "ticket": ticket,
                    "success": ok,
                    "error": res.get("error"),
                    "retcode": res.get("retcode"),
                }
            )
            if ok:
                remove_keys.append(ticket_str)

    for key in remove_keys:
        pending_state.pop(key, None)

    return actions


def should_keep_pending_order(meta: dict, analysis: dict, config: dict) -> tuple[bool, str]:
    if not analysis.get("success"):
        return True, "analysis_unavailable"

    recommendation = str(analysis.get("recommendation") or "")
    side_now = recommendation_side(recommendation)
    score_gap = abs(int(analysis.get("buy_score") or 0) - int(analysis.get("sell_score") or 0))

    if side_now == "none":
        return False, "no_trade_recommendation"

    side_expected = str((meta or {}).get("side") or "").strip().lower()
    if side_expected and side_now != side_expected:
        return False, "direction_changed"

    if bool(config.get("strong_pending_only", False)) and recommendation not in {"شراء قوي", "بيع قوي"}:
        return False, "not_strong_anymore"

    if score_gap < int(config.get("min_score_gap", 18)):
        return False, "score_gap_weakened"

    return True, "still_valid"


def cleanup_invalidated_pending_orders(bridge: MT5Bridge, state: dict, config: dict) -> list[dict]:
    actions = []
    pending_state = state.setdefault("pending_orders", {})
    if not isinstance(pending_state, dict):
        state["pending_orders"] = {}
        pending_state = state["pending_orders"]

    live_tickets = list_pending_order_tickets_by_magic(bridge.magic)
    remove_keys = []
    analysis_cache = {}

    for ticket_str, meta in pending_state.items():
        ticket = int(ticket_str)
        if ticket not in live_tickets:
            remove_keys.append(ticket_str)
            actions.append({"event": "pending_state_pruned", "ticket": ticket})
            continue

        symbol = str((meta or {}).get("symbol") or "").strip().upper()
        interval = str((meta or {}).get("interval") or "1h").strip().lower()
        cache_key = f"{symbol}:{interval}"
        analysis = analysis_cache.get(cache_key)
        if analysis is None:
            analysis = perform_full_analysis(symbol, interval)
            analysis_cache[cache_key] = analysis

        keep, reason = should_keep_pending_order(meta=meta, analysis=analysis, config=config)
        if keep:
            continue

        res = bridge.cancel_pending_order(ticket=ticket, dry_run=False)
        ok = bool(res.get("success"))
        actions.append(
            {
                "event": "pending_market_invalidated_cancel",
                "ticket": ticket,
                "symbol": symbol,
                "interval": interval,
                "reason": reason,
                "success": ok,
                "error": res.get("error"),
                "retcode": res.get("retcode"),
            }
        )
        if ok:
            remove_keys.append(ticket_str)

    for key in remove_keys:
        pending_state.pop(key, None)

    return actions


def interactive_setup(config_path: Path) -> None:
    print("=" * 72)
    print("Continuous Auto Trader Setup")
    print("=" * 72)

    print("\nAvailable symbols:")
    print(", ".join(sorted(SUPPORTED_SYMBOLS.keys())))
    symbols_raw = input("\nEnter symbols (comma separated): ").strip()
    symbols = [part.strip().upper() for part in symbols_raw.split(",") if part.strip()]

    print("\nAvailable intervals:")
    print(", ".join(sorted(SUPPORTED_INTERVALS.keys())))
    intervals_raw = input("\nEnter intervals (comma separated): ").strip()
    intervals = [part.strip().lower() for part in intervals_raw.split(",") if part.strip()]

    risk_percent = float(input("Risk percent per trade (default 1.0): ").strip() or "1.0")
    scan_every_sec = int(input("Scan every seconds (default 60): ").strip() or "60")
    min_score_gap = int(input("Min score gap (default 18): ").strip() or "18")

    dry_run_input = (input("Dry run mode? (y/n, default y): ").strip().lower() or "y")
    dry_run = dry_run_input in {"y", "yes", "1", "true"}

    new_cfg = merge_config(
        {
            "symbols": symbols,
            "intervals": intervals,
            "risk_percent": risk_percent,
            "scan_every_sec": scan_every_sec,
            "min_score_gap": min_score_gap,
            "dry_run": dry_run,
            "enabled": True,
        }
    )
    save_json(config_path, new_cfg)
    print("\nSaved config:")
    print(json.dumps(new_cfg, ensure_ascii=False, indent=2))


def has_symbol_position(positions: list[dict], base_symbol: str) -> bool:
    for pos in positions:
        if to_base_symbol(pos.get("symbol")) == base_symbol:
            return True
    return False


def has_symbol_pending_order(state: dict, base_symbol: str) -> bool:
    pending_state = state.get("pending_orders", {})
    if not isinstance(pending_state, dict):
        return False
    for meta in pending_state.values():
        if to_base_symbol((meta or {}).get("symbol")) == base_symbol:
            return True
    return False


def pending_order_side(order_type: int | None) -> str:
    buy_types = {
        getattr(mt5, "ORDER_TYPE_BUY_LIMIT", None),
        getattr(mt5, "ORDER_TYPE_BUY_STOP", None),
        getattr(mt5, "ORDER_TYPE_BUY_STOP_LIMIT", None),
    }
    sell_types = {
        getattr(mt5, "ORDER_TYPE_SELL_LIMIT", None),
        getattr(mt5, "ORDER_TYPE_SELL_STOP", None),
        getattr(mt5, "ORDER_TYPE_SELL_STOP_LIMIT", None),
    }
    if order_type in buy_types:
        return "buy"
    if order_type in sell_types:
        return "sell"
    return ""


def count_trade_slots_with_pending(
    open_positions: list[dict],
    pending_orders: list[dict],
    one_position_per_symbol: bool,
) -> int:
    if not one_position_per_symbol:
        return len(open_positions) + len(pending_orders)
    occupied = {to_base_symbol(pos.get("symbol")) for pos in open_positions}
    occupied.update(to_base_symbol(order.get("symbol")) for order in pending_orders)
    occupied.discard("")
    return len(occupied)


def has_matching_pending_order(
    pending_orders: list[dict],
    symbol: str,
    side: str,
    entry_price: float,
    price_tolerance: float,
) -> bool:
    base_symbol = to_base_symbol(symbol)
    normalized_side = str(side or "").strip().lower()
    tolerance = max(0.0, float(price_tolerance or 0.0))

    for order in pending_orders:
        if to_base_symbol(order.get("symbol")) != base_symbol:
            continue
        order_side = str(order.get("side") or "").strip().lower()
        if not order_side:
            order_side = pending_order_side(int(order.get("type", -1) or -1))
        if order_side and normalized_side and order_side != normalized_side:
            continue
        try:
            order_price = float(order.get("price_open") or order.get("price") or 0.0)
        except (TypeError, ValueError):
            continue
        if order_price <= 0:
            continue
        if abs(order_price - float(entry_price)) <= tolerance:
            return True
    return False


def count_open_trade_slots(open_positions: list[dict], one_position_per_symbol: bool) -> int:
    if not one_position_per_symbol:
        return len(open_positions)
    occupied = {to_base_symbol(pos.get("symbol")) for pos in open_positions}
    return len(occupied)


def count_symbol_trade_slots(open_positions: list[dict], pending_orders: list[dict], symbol: str) -> int:
    base_symbol = to_base_symbol(symbol)
    if not base_symbol:
        return 0
    count = 0
    for pos in open_positions:
        if to_base_symbol(pos.get("symbol")) == base_symbol:
            count += 1
    for order in pending_orders:
        if to_base_symbol(order.get("symbol")) == base_symbol:
            count += 1
    return count


def count_symbol_interval_trade_slots(
    open_positions: list[dict],
    pending_orders: list[dict],
    symbol: str,
    interval: str,
) -> int:
    base_symbol = to_base_symbol(symbol)
    normalized_interval = str(interval or "").strip().lower()
    if not base_symbol or not normalized_interval:
        return 0

    count = 0
    for pos in open_positions:
        if to_base_symbol(pos.get("symbol")) != base_symbol:
            continue
        pos_interval = _extract_interval_from_comment(str(pos.get("comment") or "")).lower()
        if pos_interval == normalized_interval:
            count += 1

    for order in pending_orders:
        if to_base_symbol(order.get("symbol")) != base_symbol:
            continue
        order_interval = _extract_interval_from_comment(str(order.get("comment") or "")).lower()
        if order_interval == normalized_interval:
            count += 1

    return count


def build_candidate(symbol: str, interval: str, analysis: dict) -> dict:
    buy_score = int(analysis.get("buy_score") or 0)
    sell_score = int(analysis.get("sell_score") or 0)
    score_gap = abs(buy_score - sell_score)
    recommendation = str(analysis.get("recommendation") or "")
    strength_bonus = 20 if recommendation in {"شراء قوي", "بيع قوي"} else 0
    rank_score = score_gap + strength_bonus

    return {
        "symbol": symbol,
        "interval": interval,
        "recommendation": recommendation,
        "side": recommendation_side(recommendation),
        "confidence": analysis.get("confidence"),
        "buy_score": buy_score,
        "sell_score": sell_score,
        "score_gap": score_gap,
        "rank_score": rank_score,
        "entry": analysis.get("entry_point"),
        "stop_loss": analysis.get("stop_loss"),
        "tp1": analysis.get("take_profit1"),
        "tp2": analysis.get("take_profit2"),
        "tp3": analysis.get("take_profit3"),
        "market_regime": analysis.get("market_regime"),
        "risk_reward_ratio": analysis.get("risk_reward_ratio"),
        "analysis_source": TRADE_ANALYSIS_SOURCE,
        "analysis_engine": TRADE_ANALYSIS_ENGINE,
        "market_data_source": analysis.get("data_source") or analysis.get("market_data_source"),
        "analysis": analysis,
    }


def _site_db_path(config: dict) -> Path:
    raw_path = str(config.get("site_signals_db_path") or DEFAULT_CONFIG["site_signals_db_path"]).strip()
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _clean_symbol(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _site_signal_side(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"buy", "long", "شراء"} or "شراء" in text:
        return "buy"
    if text in {"sell", "short", "بيع"} or "بيع" in text:
        return "sell"
    return "none"


def _site_recommendation(side: str) -> str:
    if side == "buy":
        return "شراء"
    if side == "sell":
        return "بيع"
    return ""


def _float_or_none(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        out = float(value)
        if not math.isfinite(out) or out <= 0:
            return None
        return out
    except Exception:
        return None


def _signal_created_timestamp(row: dict) -> float | None:
    raw = row.get("created_at") or row.get("timestamp")
    if raw in (None, ""):
        return None
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.timestamp()


def _valid_site_levels(side: str, entry: float, stop_loss: float, targets: list[float]) -> bool:
    if side == "buy":
        return stop_loss < entry and all(tp > entry for tp in targets)
    if side == "sell":
        return stop_loss > entry and all(tp < entry for tp in targets)
    return False


def load_site_signal_candidates(config: dict, now_ts: int | None = None) -> tuple[list[dict], dict]:
    db_path = _site_db_path(config)
    stats = {
        "source": "site_db",
        "db_path": str(db_path),
        "loaded": 0,
        "accepted": 0,
        "skipped": {},
    }

    def skip(reason: str) -> None:
        skipped = stats.setdefault("skipped", {})
        skipped[reason] = int(skipped.get(reason, 0) or 0) + 1

    if not db_path.exists():
        stats["error"] = "site signals database not found"
        return [], stats

    selected_symbols = list(config.get("site_signal_symbols") or config.get("symbols") or [])
    allowed_symbols = set(selected_symbols)
    allow_all_symbols = "*" in allowed_symbols
    blocked_symbols = set(config.get("blocked_symbols") or [])
    max_age_minutes = int(config.get("site_signals_max_age_minutes", 180) or 0)
    min_quality = int(config.get("site_signals_min_quality", 0) or 0)
    now_ts = int(now_ts or time.time())

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(signals)").fetchall()}
        where_sql = "WHERE lower(coalesce(status, 'active')) = 'active'" if "status" in columns else ""
        order_columns = [name for name in ["created_at", "timestamp", "id", "signal_id"] if name in columns]
        order_sql = "ORDER BY " + ", ".join(f"{name} DESC" for name in order_columns) if order_columns else ""
        rows = conn.execute(
            f"SELECT * FROM signals {where_sql} {order_sql} LIMIT ?",
            (int(config.get("site_signals_limit", 30)),),
        ).fetchall()
        conn.close()
    except Exception as exc:
        stats["error"] = str(exc)
        return [], stats

    stats["loaded"] = len(rows)
    candidates = []
    for row_obj in rows:
        row = dict(row_obj)
        symbol = _clean_symbol(row.get("symbol") or row.get("pair"))
        base_symbol = to_base_symbol(symbol)
        if not allowed_symbols:
            skip("no_user_selected_symbols")
            continue
        if not symbol:
            skip("missing_symbol")
            continue
        if blocked_symbols and (symbol in blocked_symbols or base_symbol in blocked_symbols):
            skip("blocked_symbol")
            continue
        if allowed_symbols and not allow_all_symbols and symbol not in allowed_symbols and base_symbol not in allowed_symbols:
            skip("symbol_not_allowed")
            continue

        created_ts = _signal_created_timestamp(row)
        if max_age_minutes > 0 and created_ts is not None and (now_ts - int(created_ts)) > (max_age_minutes * 60):
            skip("stale")
            continue

        quality_score = int(float(row.get("quality_score") or 0))
        if quality_score < min_quality:
            skip("quality_below_min")
            continue

        side = _site_signal_side(row.get("signal_type") or row.get("signal") or row.get("recommendation"))
        entry = _float_or_none(row.get("entry_price") if row.get("entry_price") is not None else row.get("entry"))
        stop_loss = _float_or_none(row.get("stop_loss") if row.get("stop_loss") is not None else row.get("sl"))
        tp1 = _float_or_none(row.get("take_profit_1") if row.get("take_profit_1") is not None else row.get("tp1"))
        tp2 = _float_or_none(row.get("take_profit_2") if row.get("take_profit_2") is not None else row.get("tp2")) or tp1
        tp3 = _float_or_none(row.get("take_profit_3") if row.get("take_profit_3") is not None else row.get("tp3")) or tp2
        if side == "none" or entry is None or stop_loss is None or tp1 is None or tp2 is None or tp3 is None:
            skip("incomplete_levels")
            continue
        if not _valid_site_levels(side, entry, stop_loss, [tp1, tp2, tp3]):
            skip("invalid_levels_for_side")
            continue

        risk_distance = abs(entry - stop_loss)
        reward_distance = abs(tp1 - entry)
        rr_ratio = (reward_distance / risk_distance) if risk_distance > 0 else 0.0
        timeframe = str(row.get("timeframe") or row.get("tf") or "5m").strip().lower() or "5m"
        signal_id = str(row.get("signal_id") or row.get("id") or "").strip()
        site_row_id = row.get("id")
        rank_score = quality_score or 1
        candidates.append(
            {
                "symbol": symbol,
                "interval": timeframe,
                "recommendation": _site_recommendation(side),
                "side": side,
                "confidence": quality_score,
                "buy_score": quality_score if side == "buy" else 0,
                "sell_score": quality_score if side == "sell" else 0,
                "score_gap": quality_score,
                "rank_score": rank_score,
                "entry": entry,
                "stop_loss": stop_loss,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "market_regime": "site_signal",
                "risk_reward_ratio": rr_ratio,
                "analysis": row,
                "source": "site_db",
                "signal_id": signal_id,
                "site_row_id": site_row_id,
                "created_at": row.get("created_at") or row.get("timestamp"),
            }
        )

    stats["accepted"] = len(candidates)
    return candidates, stats


def mark_site_signal_activated(config: dict, candidate: dict) -> dict:
    if str(candidate.get("source") or "") != "site_db":
        return {"success": True, "skipped": True}

    db_path = _site_db_path(config)
    if not db_path.exists():
        return {"success": False, "error": "site signals database not found"}

    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(signals)").fetchall()}
        if "activated" not in columns:
            conn.close()
            return {"success": True, "skipped": True, "reason": "activated column not found"}

        row_id = candidate.get("site_row_id")
        signal_id = str(candidate.get("signal_id") or "").strip()
        if row_id is not None and "id" in columns:
            cur = conn.execute("UPDATE signals SET activated = 1 WHERE id = ?", (row_id,))
        elif signal_id and "signal_id" in columns:
            cur = conn.execute("UPDATE signals SET activated = 1 WHERE signal_id = ?", (signal_id,))
        else:
            conn.close()
            return {"success": False, "error": "missing signal id column"}

        conn.commit()
        changed = int(cur.rowcount or 0)
        conn.close()
        return {"success": True, "updated": changed}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def select_best_candidate(config: dict, analyses: list[dict]) -> dict | None:
    filtered = []
    for item in analyses:
        recommendation = str(item.get("recommendation") or "")
        if not is_recommendation_allowed(
            recommendation,
            allow_normal=bool(config.get("allow_normal_signals", True)),
            allow_strong=bool(config.get("allow_strong_signals", True)),
        ):
            continue
        if bool(config.get("strong_pending_only", False)) and recommendation not in {"شراء قوي", "بيع قوي"}:
            continue
        if int(item.get("score_gap") or 0) < int(config.get("min_score_gap", 18)):
            continue
        if str(item.get("side") or "none") == "none":
            continue
        filtered.append(item)

    if not filtered:
        return None

    filtered.sort(key=lambda row: (row["rank_score"], row["score_gap"]), reverse=True)
    return filtered[0]


def select_ranked_candidates(config: dict, analyses: list[dict]) -> list[dict]:
    filtered = []
    for item in analyses:
        recommendation = str(item.get("recommendation") or "")
        if not is_recommendation_allowed(
            recommendation,
            allow_normal=bool(config.get("allow_normal_signals", True)),
            allow_strong=bool(config.get("allow_strong_signals", True)),
        ):
            continue
        if bool(config.get("strong_pending_only", False)) and recommendation not in {"شراء قوي", "بيع قوي"}:
            continue
        if int(item.get("score_gap") or 0) < int(config.get("min_score_gap", 18)):
            continue
        if str(item.get("side") or "none") == "none":
            continue
        filtered.append(item)

    filtered.sort(key=lambda row: (row["rank_score"], row["score_gap"]), reverse=True)
    return filtered


def apply_position_protection_maintenance(
    bridge: MT5Bridge,
    config: dict,
    state: dict,
    state_path: Path,
    now_ts: int,
) -> dict:
    actions = []
    open_rows = bridge.has_open_positions(magic=bridge.magic)
    if not open_rows.get("success"):
        return {
            "success": False,
            "error": open_rows.get("error"),
            "open_positions": 0,
            "maintenance_actions": actions,
        }

    open_positions = open_rows.get("positions") or []

    if bool(config.get("cancel_expired_pending", True)):
        actions.extend(cleanup_expired_pending_orders(bridge=bridge, state=state, now_ts=now_ts))

    if open_positions:
        actions.extend(apply_trailing_stop(bridge=bridge, open_positions=open_positions, config=config))

    if actions:
        save_json(state_path, state)

    return {
        "success": True,
        "open_positions": len(open_positions),
        "maintenance_actions": actions,
    }


def run_loop(config_path: Path, state_path: Path, once: bool) -> int:
    bridge = MT5Bridge()
    conn = bridge.connect()
    if not conn.get("success"):
        print(json.dumps({"success": False, "error": conn.get("error"), "status": conn.get("status")}, ensure_ascii=False))
        return 1

    state = load_json(state_path, {"last_trade_at": {}, "last_signature": {}, "pending_orders": {}})

    while True:
        config = merge_config(load_json(config_path, {}))

        # Re-apply execution flags every cycle to avoid external config drift
        # that can silently disable MT5 execution while the trader is running.
        bridge.configure(
            {
                "allow_trading": not bool(config.get("dry_run", True)),
                "auto_execution_enabled": not bool(config.get("dry_run", True)),
                "auto_execution_symbols": list(config.get("symbols") or []),
            }
        )

        if not config.get("enabled", True):
            print(json.dumps({"event": "disabled", "time": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False))
            if once:
                return 0
            time.sleep(config["scan_every_sec"])
            continue

        now_utc = datetime.now(timezone.utc)
        now_ts = int(time.time())
        in_session, session_reason = _is_within_utc_sessions(config, now_utc)
        if not in_session:
            protection = apply_position_protection_maintenance(
                bridge=bridge,
                config=config,
                state=state,
                state_path=state_path,
                now_ts=now_ts,
            )
            print(
                json.dumps(
                    {
                        "event": "outside_trading_session",
                        "time_utc": now_utc.isoformat(timespec="seconds"),
                        "analysis_source": config.get("analysis_source"),
                        "analysis_engine": config.get("analysis_engine"),
                        "reason": session_reason,
                        "sessions_utc": config.get("trading_sessions_utc", []),
                        "open_positions": protection.get("open_positions"),
                        "maintenance_actions": protection.get("maintenance_actions", []),
                        "maintenance_error": protection.get("error"),
                    },
                    ensure_ascii=False,
                )
            )
            if once:
                return 0
            time.sleep(config["scan_every_sec"])
            continue

        risk_guard = _daily_risk_guard(bridge, config, now_utc)
        if not risk_guard.get("success"):
            print(json.dumps({"event": "risk_guard_error", "error": risk_guard.get("error")}, ensure_ascii=False))
            if once:
                return 1
            time.sleep(config["scan_every_sec"])
            continue

        if risk_guard.get("blocked"):
            print(
                json.dumps(
                    {
                        "event": "risk_guard_blocked",
                        "time_utc": now_utc.isoformat(timespec="seconds"),
                        "daily_realized_pnl_usd": risk_guard.get("daily_realized_pnl_usd"),
                        "daily_loss_limit_usd": risk_guard.get("daily_loss_limit_usd"),
<<<<<<< Updated upstream
                        "daily_loss_limit_source": risk_guard.get("daily_loss_limit_source"),
                        "daily_loss_limit_percent_of_equity": risk_guard.get("daily_loss_limit_percent_of_equity"),
                        "account_equity": risk_guard.get("account_equity"),
=======
                        "daily_profit_lock_usd": risk_guard.get("daily_profit_lock_usd"),
>>>>>>> Stashed changes
                        "consecutive_losses": risk_guard.get("consecutive_losses"),
                        "max_consecutive_losses": risk_guard.get("max_consecutive_losses"),
                        "breached_daily_loss_limit": risk_guard.get("breached_daily_loss_limit"),
                        "breached_daily_profit_lock": risk_guard.get("breached_daily_profit_lock"),
                        "breached_consecutive_losses": risk_guard.get("breached_consecutive_losses"),
                        "ignored_consecutive_losses_due_to_daily_pnl": risk_guard.get("ignored_consecutive_losses_due_to_daily_pnl"),
                    },
                    ensure_ascii=False,
                )
            )
            if once:
                return 0
            time.sleep(config["scan_every_sec"])
            continue

        open_rows = bridge.has_open_positions(magic=bridge.magic)
        if not open_rows.get("success"):
            print(json.dumps({"event": "open_positions_error", "error": open_rows.get("error")}, ensure_ascii=False))
            if once:
                return 1
            time.sleep(config["scan_every_sec"])
            continue

        open_positions = open_rows.get("positions") or []

        maintenance_actions = []
        if bool(config.get("cancel_expired_pending", True)):
            maintenance_actions.extend(cleanup_expired_pending_orders(bridge=bridge, state=state, now_ts=now_ts))

        if bool(config.get("cancel_on_market_invalidation", True)):
            maintenance_actions.extend(cleanup_invalidated_pending_orders(bridge=bridge, state=state, config=config))

        if open_positions:
            maintenance_actions.extend(apply_trailing_stop(bridge=bridge, open_positions=open_positions, config=config))

        if maintenance_actions:
            save_json(state_path, state)

        live_pending_orders = list_pending_orders_by_magic(bridge.magic)
        max_cfg = resolve_effective_max_open_positions(config)
        max_open_positions = int(max_cfg.get("effective_max_open_positions", 0) or 0)
        one_position_per_symbol = bool(config.get("one_position_per_symbol", True))
        raw_open_trade_slots = count_open_trade_slots(open_positions, one_position_per_symbol=one_position_per_symbol)
        pending_trade_slots = count_open_trade_slots(live_pending_orders, one_position_per_symbol=one_position_per_symbol)
        open_trade_slots = count_trade_slots_with_pending(
            open_positions=open_positions,
            pending_orders=live_pending_orders,
            one_position_per_symbol=one_position_per_symbol,
        )

        if max_open_positions > 0 and open_trade_slots >= max_open_positions:
            print(
                json.dumps(
                    {
                        "event": "max_open_positions_reached",
                        "count": open_trade_slots,
                        "open_positions_count": raw_open_trade_slots,
                        "pending_orders_count": pending_trade_slots,
                        "count_basis": "symbols" if one_position_per_symbol else "positions",
                        "raw_open_positions": len(open_positions),
                        "max_open_positions": max_open_positions,
                        "max_open_positions_source": max_cfg.get("source"),
                        "risk_budget": {
                            "risk_percent_per_trade": max_cfg.get("risk_per_trade"),
                            "max_total_open_risk_percent": max_cfg.get("max_total_risk"),
                            "min_open_positions": max_cfg.get("min_open"),
                            "max_open_positions_cap": max_cfg.get("cap"),
                        },
                        "maintenance_actions": maintenance_actions,
                    },
                    ensure_ascii=False,
                )
            )
            if once:
                return 0
            time.sleep(config["scan_every_sec"])
            continue

        analyses = []
        site_signal_stats = None
        signal_source = str(config.get("signal_source") or "analysis").strip().lower()
        if signal_source in {"site_db", "both"}:
            site_candidates, site_signal_stats = load_site_signal_candidates(config, now_ts=now_ts)
            analyses.extend(site_candidates)

        if signal_source in {"analysis", "both"}:
            for symbol in config["symbols"]:
                for interval in config["intervals"]:
                    result = perform_full_analysis(symbol, interval)
                    if not result.get("success"):
                        continue
                    analyses.append(build_candidate(symbol, interval, result))

        analyses_by_key = {
            (str(item.get("symbol") or "").upper(), str(item.get("interval") or "").lower()): item.get("analysis")
            for item in analyses
            if isinstance(item.get("analysis"), dict)
        }
        ranked_candidates = select_ranked_candidates(config, analyses)
        best = ranked_candidates[0] if ranked_candidates else None
        heartbeat = {
            "event": "scan",
            "time": datetime.now().isoformat(timespec="seconds"),
            "time_utc": now_utc.isoformat(timespec="seconds"),
            "analysis_source": config.get("analysis_source"),
            "analysis_engine": config.get("analysis_engine"),
            "symbols": config["symbols"],
            "blocked_symbols": config.get("blocked_symbols", []),
            "intervals": config["intervals"],
            "signal_source": signal_source,
            "site_signals": site_signal_stats,
            "session_match": session_reason,
            "risk_guard": {
                "daily_realized_pnl_usd": risk_guard.get("daily_realized_pnl_usd"),
                "daily_loss_limit_usd": risk_guard.get("daily_loss_limit_usd"),
<<<<<<< Updated upstream
                "daily_loss_limit_source": risk_guard.get("daily_loss_limit_source"),
                "daily_loss_limit_percent_of_equity": risk_guard.get("daily_loss_limit_percent_of_equity"),
                "account_equity": risk_guard.get("account_equity"),
=======
                "daily_profit_lock_usd": risk_guard.get("daily_profit_lock_usd"),
>>>>>>> Stashed changes
                "consecutive_losses": risk_guard.get("consecutive_losses"),
                "max_consecutive_losses": risk_guard.get("max_consecutive_losses"),
                "closed_positions_today": risk_guard.get("closed_positions_today"),
                "breached_daily_profit_lock": risk_guard.get("breached_daily_profit_lock"),
                "ignored_consecutive_losses_due_to_daily_pnl": risk_guard.get("ignored_consecutive_losses_due_to_daily_pnl"),
                "interval_freeze_active_count": risk_guard.get("interval_freeze_active_count"),
            },
            "candidates": len(analyses),
            "open_positions": len(open_positions),
            "open_trade_slots": open_trade_slots,
            "open_positions_slots": raw_open_trade_slots,
            "pending_order_slots": pending_trade_slots,
            "open_trade_slots_basis": "symbols" if one_position_per_symbol else "positions",
            "max_open_positions": max_open_positions,
            "max_open_positions_source": max_cfg.get("source"),
            "risk_budget": {
                "risk_percent_per_trade": max_cfg.get("risk_per_trade"),
                "max_total_open_risk_percent": max_cfg.get("max_total_risk"),
                "min_open_positions": max_cfg.get("min_open"),
                "max_open_positions_cap": max_cfg.get("cap"),
            },
            "maintenance_actions": maintenance_actions,
            "best": {
                "symbol": best.get("symbol"),
                "interval": best.get("interval"),
                "source": best.get("source", "analysis"),
                "signal_id": best.get("signal_id"),
                "recommendation": best.get("recommendation"),
                "score_gap": best.get("score_gap"),
                "rank_score": best.get("rank_score"),
                "analysis_source": best.get("analysis_source"),
                "market_data_source": best.get("market_data_source"),
            } if best else None,
            "actions": [],
        }

        if ranked_candidates:
            max_trades_per_cycle = max(1, int(config.get("max_trades_per_cycle", 3)))
            executed_this_cycle = 0
            occupied_symbols = {to_base_symbol(pos.get("symbol")) for pos in open_positions}
            occupied_symbols.update(to_base_symbol(order.get("symbol")) for order in live_pending_orders)
            occupied_symbols.discard("")
            current_open_count = open_trade_slots
            current_pending_count = len(live_pending_orders)

            for candidate in ranked_candidates:
                if executed_this_cycle >= max_trades_per_cycle:
                    heartbeat["actions"].append(
                        {
                            "event": "cycle_trade_limit_reached",
                            "max_trades_per_cycle": max_trades_per_cycle,
                        }
                    )
                    break

                symbol = str(candidate["symbol"])
                interval = str(candidate["interval"])

<<<<<<< Updated upstream
=======
                ema_trend_check = ema_trend_alignment(config=config, candidate=candidate, analyses_by_key=analyses_by_key)
                if not ema_trend_check.get("allowed"):
                    heartbeat["actions"].append(
                        {
                            "event": "skip_ema_trend_filter",
                            "symbol": symbol,
                            "interval": interval,
                            **ema_trend_check,
                        }
                    )
                    continue

                bos_retest_check = bos_retest_alignment(config=config, candidate=candidate)
                if not bos_retest_check.get("allowed"):
                    heartbeat["actions"].append(
                        {
                            "event": "skip_bos_retest_filter",
                            "symbol": symbol,
                            "interval": interval,
                            **bos_retest_check,
                        }
                    )
                    continue

                interval_freeze_map = risk_guard.get("interval_freeze_map") or {}
                freeze_scope = str(risk_guard.get("interval_freeze_scope") or "interval")
                if freeze_scope == "symbol_interval":
                    freeze_key = f"{to_base_symbol(symbol)}:{interval}"
                elif freeze_scope == "symbol":
                    freeze_key = to_base_symbol(symbol)
                else:
                    freeze_key = interval
                freeze_meta = interval_freeze_map.get(freeze_key)
                if isinstance(freeze_meta, dict):
                    heartbeat["actions"].append(
                        {
                            "event": "skip_interval_temporarily_frozen",
                            "symbol": symbol,
                            "interval": interval,
                            "freeze_scope": freeze_scope,
                            "frozen_until_utc": freeze_meta.get("frozen_until_utc"),
                            "streak_losses": freeze_meta.get("streak_losses"),
                            "freeze_after_losses": freeze_meta.get("freeze_after_losses"),
                        }
                    )
                    continue
                
                # Gold-specific: skip XAUUSD during low-liquidity hours
>>>>>>> Stashed changes
                base_sym = to_base_symbol(symbol)
                market_ok, market_reason = _is_market_open_for_execution(base_sym, now_utc)
                if not market_ok:
                    heartbeat["actions"].append({
                        "event": "skip_market_closed",
                        "symbol": symbol,
                        "interval": interval,
                        "reason": market_reason,
                    })
                    continue

                # Gold-specific: skip XAUUSD during low-liquidity hours
                if base_sym == "XAUUSD":
                    gold_ok, gold_reason = _is_gold_market_open(config, now_utc)
                    if not gold_ok:
                        heartbeat["actions"].append({
                            "event": "skip_gold_market_closed",
                            "symbol": symbol,
                            "interval": interval,
                            "reason": gold_reason,
                        })
                        continue
                    
                    # Gold requires higher confidence: min score_gap of 25 (vs default 18)
                    score_gap = int(candidate.get("score_gap") or 0)
                    gold_min_score = 25
                    if score_gap < gold_min_score:
                        heartbeat["actions"].append({
                            "event": "skip_gold_low_confidence",
                            "symbol": symbol,
                            "interval": interval,
                            "score_gap": score_gap,
                            "gold_min_score": gold_min_score,
                        })
                        continue

                    trend_check = gold_trend_alignment(config, candidate)
                    if not trend_check.get("allowed"):
                        heartbeat["actions"].append({
                            "event": "skip_gold_counter_trend",
                            "symbol": symbol,
                            "interval": interval,
                            **trend_check,
                        })
                        continue

                    scalping_check = gold_scalping_quality_gate(config, candidate, analyses_by_key)
                    if not scalping_check.get("allowed"):
                        heartbeat["actions"].append({
                            "event": "skip_gold_scalping_filter",
                            "symbol": symbol,
                            "interval": interval,
                            **scalping_check,
                        })
                        continue

                if base_sym != "XAUUSD":
                    scalping_check = forex_scalping_quality_gate(config, candidate, analyses_by_key)
                    if not scalping_check.get("allowed"):
                        heartbeat["actions"].append({
                            "event": "skip_forex_scalping_filter",
                            "symbol": symbol,
                            "interval": interval,
                            **scalping_check,
                        })
                        continue
                
                try:
                    entry_price = float(candidate["entry"])
                    stop_price = float(candidate["stop_loss"])
                    tp1_price = float(candidate["tp1"])
                    tp2_price = float(candidate.get("tp2") or candidate["tp1"])
                    tp3_price = float(candidate.get("tp3") or candidate["tp1"])
                except (TypeError, ValueError, KeyError):
                    heartbeat["actions"].append(
                        {
                            "event": "skip_invalid_price_levels",
                            "symbol": symbol,
                            "interval": interval,
                        }
                    )
                    continue

                if not all(math.isfinite(v) and v > 0 for v in (entry_price, stop_price, tp1_price, tp2_price, tp3_price)):
                    heartbeat["actions"].append(
                        {
                            "event": "skip_non_finite_price_levels",
                            "symbol": symbol,
                            "interval": interval,
                        }
                    )
                    continue

                pending_entry = bool(config.get("pending_entry", False))
                market_repriced = False
                market_drift_pct = None
                gold_scalping_levels = None
                if not pending_entry:
                    resolved_symbol = bridge._resolve_symbol_name(symbol)
                    tick = bridge._get_tick(resolved_symbol) if resolved_symbol else None
                    side = str(candidate.get("side") or "")
                    if tick is not None and side in {"buy", "sell"}:
                        market_price = float(tick.ask if side == "buy" else tick.bid)
                        market_drift_pct = distance_percent(entry_price, market_price)
                        max_market_drift_pct = float(config.get("max_market_entry_drift_percent", 0.6) or 0.0)
                        if max_market_drift_pct > 0 and market_drift_pct > max_market_drift_pct:
                            heartbeat["actions"].append(
                                {
                                    "event": "skip_market_entry_drift_too_far",
                                    "symbol": symbol,
                                    "interval": interval,
                                    "market_price": round(market_price, 5),
                                    "signal_entry": round(entry_price, 5),
                                    "drift_percent": round(market_drift_pct, 3),
                                    "max_market_entry_drift_percent": round(max_market_drift_pct, 3),
                                }
                            )
                            continue

                        if bool(config.get("market_reprice_entry", False)):
                            original_entry = entry_price
                            risk_distance = abs(original_entry - stop_price)
                            tp1_distance = abs(tp1_price - original_entry)
                            tp2_distance = abs(tp2_price - original_entry)
                            tp3_distance = abs(tp3_price - original_entry)
                            entry_price = round_broker_price(bridge, symbol, market_price)
                            if side == "buy":
                                stop_price = round_broker_price(bridge, symbol, entry_price - risk_distance)
                                tp1_price = round_broker_price(bridge, symbol, entry_price + tp1_distance)
                                tp2_price = round_broker_price(bridge, symbol, entry_price + tp2_distance)
                                tp3_price = round_broker_price(bridge, symbol, entry_price + tp3_distance)
                            else:
                                stop_price = round_broker_price(bridge, symbol, entry_price + risk_distance)
                                tp1_price = round_broker_price(bridge, symbol, entry_price - tp1_distance)
                                tp2_price = round_broker_price(bridge, symbol, entry_price - tp2_distance)
                                tp3_price = round_broker_price(bridge, symbol, entry_price - tp3_distance)
                            market_repriced = True

                stop_price, tp1_price, tp2_price, tp3_price, gold_scalping_levels = apply_gold_scalping_atr_levels(
                    config=config,
                    bridge=bridge,
                    candidate=candidate,
                    entry_price=entry_price,
                    stop_price=stop_price,
                    tp1_price=tp1_price,
                    tp2_price=tp2_price,
                    tp3_price=tp3_price,
                    analyses_by_key=analyses_by_key,
                )
                forex_scalping_levels = None
                if gold_scalping_levels is None:
                    stop_price, tp1_price, tp2_price, tp3_price, forex_scalping_levels = apply_forex_scalping_atr_levels(
                        config=config,
                        bridge=bridge,
                        candidate=candidate,
                        entry_price=entry_price,
                        stop_price=stop_price,
                        tp1_price=tp1_price,
                        tp2_price=tp2_price,
                        tp3_price=tp3_price,
                        analyses_by_key=analyses_by_key,
                    )

                fixed_tp_meta = None
                tp1_price, tp2_price, tp3_price, fixed_tp_meta = apply_gold_fixed_tp_after_spread(
                    bridge=bridge,
                    config=config,
                    symbol=symbol,
                    side=str(candidate.get("side") or ""),
                    entry_price=entry_price,
                    tp1_price=tp1_price,
                    tp2_price=tp2_price,
                    tp3_price=tp3_price,
                )

                stop_distance_pct = distance_percent(entry_price, stop_price)
                max_stop_distance_pct = float(config.get("max_stop_distance_percent", 1.2))
                if stop_distance_pct > max_stop_distance_pct:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_stop_too_far",
                            "symbol": symbol,
                            "interval": interval,
                            "stop_distance_percent": round(stop_distance_pct, 3),
                            "max_stop_distance_percent": round(max_stop_distance_pct, 3),
                        }
                    )
                    continue

                max_target_distance_pct = float(config.get("max_target_distance_percent", 3.5))
                target_distance_pct = max(
                    distance_percent(entry_price, tp1_price),
                    distance_percent(entry_price, tp2_price),
                    distance_percent(entry_price, tp3_price),
                )
                if target_distance_pct > max_target_distance_pct:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_target_too_far",
                            "symbol": symbol,
                            "interval": interval,
                            "target_distance_percent": round(target_distance_pct, 3),
                            "max_target_distance_percent": round(max_target_distance_pct, 3),
                        }
                    )
                    continue

                risk_distance = abs(entry_price - stop_price)
                if risk_distance <= 0:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_zero_risk_distance",
                            "symbol": symbol,
                            "interval": interval,
                        }
                    )
                    continue
                reward_distance = abs(tp1_price - entry_price)
                rr_ratio = (reward_distance / risk_distance) if risk_distance > 0 else 0.0
                min_rr_ratio = float(config.get("min_rr_ratio", 1.1))
                if fixed_tp_meta is not None:
                    min_rr_ratio = float(config.get("min_rr_ratio_fixed_tp", 0.0) or 0.0)
                if rr_ratio < min_rr_ratio:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_low_rr",
                            "symbol": symbol,
                            "interval": interval,
                            "rr_ratio": round(rr_ratio, 3),
                            "min_rr_ratio": round(min_rr_ratio, 3),
                        }
                    )
                    continue

                spread_check = gold_scalping_spread_check(bridge, config, symbol, risk_distance)
                if not spread_check.get("allowed"):
                    heartbeat["actions"].append({
                        "event": "skip_gold_scalping_spread",
                        "symbol": symbol,
                        "interval": interval,
                        **spread_check,
                    })
                    continue
                spread_check = forex_scalping_spread_check(bridge, config, symbol, risk_distance)
                if not spread_check.get("allowed"):
                    heartbeat["actions"].append({
                        "event": "skip_forex_scalping_spread",
                        "symbol": symbol,
                        "interval": interval,
                        **spread_check,
                    })
                    continue

                if max_open_positions > 0 and current_open_count >= max_open_positions:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_max_open_positions_during_cycle",
                            "count": current_open_count,
                            "count_basis": "symbols" if one_position_per_symbol else "positions",
                            "max_open_positions": max_open_positions,
                        }
                    )
                    break

                if one_position_per_symbol and (
                    symbol in occupied_symbols or has_symbol_pending_order(state, symbol)
                ):
                    heartbeat["actions"].append({"event": "skip_existing_symbol_position", "symbol": symbol})
                    continue

                max_positions_per_symbol = max(0, int(config.get("max_positions_per_symbol", 0) or 0))
                if max_positions_per_symbol > 0:
                    symbol_slots = count_symbol_trade_slots(
                        open_positions=open_positions,
                        pending_orders=live_pending_orders,
                        symbol=symbol,
                    )
                    if symbol_slots >= max_positions_per_symbol:
                        heartbeat["actions"].append(
                            {
                                "event": "skip_max_positions_per_symbol",
                                "symbol": symbol,
                                "symbol_slots": symbol_slots,
                                "max_positions_per_symbol": max_positions_per_symbol,
                            }
                        )
                        continue

                one_position_per_symbol_interval = bool(config.get("one_position_per_symbol_interval", False))
                if one_position_per_symbol_interval:
                    symbol_interval_slots = count_symbol_interval_trade_slots(
                        open_positions=open_positions,
                        pending_orders=live_pending_orders,
                        symbol=symbol,
                        interval=interval,
                    )
                    if symbol_interval_slots >= 1:
                        heartbeat["actions"].append(
                            {
                                "event": "skip_existing_symbol_interval_position",
                                "symbol": symbol,
                                "interval": interval,
                            }
                        )
                        continue

                cooldown_minutes = int(config.get("cooldown_minutes_per_symbol", 90))
                last_trade_map = state.get("last_trade_at", {})
                key = f"{symbol}:{interval}"
                last_ts = int(last_trade_map.get(key, 0) or 0)
                in_cooldown = cooldown_minutes > 0 and (now_ts - last_ts) < (cooldown_minutes * 60)

<<<<<<< Updated upstream
                signature = f"{candidate.get('source', 'analysis')}|{candidate.get('signal_id', '')}|{symbol}|{interval}|{candidate['recommendation']}|{candidate['entry']}|{candidate['stop_loss']}|{candidate['tp1']}"
=======
                split_tp = bool(config.get("split_tp", True))
                tp_execution_mode = str(config.get("tp_execution_mode") or ("split" if split_tp else "single")).strip().lower()
                signature_target = tp1_price
                if tp_execution_mode in {"tp2", "tp2_only", "target2_only"}:
                    signature_target = tp2_price
                elif tp_execution_mode in {"tp3", "tp3_only", "target3_only"}:
                    signature_target = tp3_price

                signature = f"{symbol}|{interval}|{candidate['recommendation']}|{round(entry_price, 5)}|{round(stop_price, 5)}|{round(signature_target, 5)}|{tp_execution_mode}"
>>>>>>> Stashed changes
                last_sig_map = state.get("last_signature", {})
                same_signature = str(last_sig_map.get(key, "")) == signature
                # Prevent immediate re-fire of identical setup but avoid permanent blocks
                # when market stays structurally similar for long periods.
                duplicate_block_minutes = max(cooldown_minutes, 5)
                in_duplicate_block_window = (
                    same_signature
                    and last_ts > 0
                    and (now_ts - last_ts) < (duplicate_block_minutes * 60)
                )

                if in_cooldown:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_cooldown",
                            "symbol": symbol,
                            "interval": interval,
                            "cooldown_minutes": cooldown_minutes,
                        }
                    )
                    continue

                if in_duplicate_block_window:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_duplicate_signature",
                            "symbol": symbol,
                            "interval": interval,
                            "duplicate_block_minutes": duplicate_block_minutes,
                        }
                    )
                    continue

<<<<<<< Updated upstream
                risk_percent_per_trade = float(config["risk_percent"])
=======
                fixed_volume = max(0.0, float(config.get("fixed_volume", 0.0) or 0.0))

                if pending_entry:
                    max_pending_orders = int(config.get("max_pending_orders", 0) or 0)
                    if max_pending_orders > 0 and current_pending_count >= max_pending_orders:
                        heartbeat["actions"].append(
                            {
                                "event": "skip_max_pending_orders",
                                "symbol": symbol,
                                "interval": interval,
                                "pending_orders": current_pending_count,
                                "max_pending_orders": max_pending_orders,
                            }
                        )
                        continue

                    pending_tolerance = float(config.get("pending_dedupe_price_tolerance", 0.0) or 0.0)
                    if has_matching_pending_order(
                        pending_orders=live_pending_orders,
                        symbol=symbol,
                        side=str(candidate.get("side") or ""),
                        entry_price=entry_price,
                        price_tolerance=pending_tolerance,
                    ):
                        heartbeat["actions"].append(
                            {
                                "event": "skip_duplicate_pending_order",
                                "symbol": symbol,
                                "interval": interval,
                                "entry": round(entry_price, 5),
                                "price_tolerance": round(pending_tolerance, 5),
                            }
                        )
                        continue

                if not pending_entry:
                    resolved_symbol = bridge._resolve_symbol_name(symbol)
                    tick = bridge._get_tick(resolved_symbol) if resolved_symbol else None
                    if tick is not None:
                        side = str(candidate.get("side") or "")
                        market_price = float(tick.ask if side == "buy" else tick.bid)
                        stale_reason = ""
                        if side == "buy":
                            if stop_price >= market_price:
                                stale_reason = "buy_stop_not_below_market"
                            elif tp1_price <= market_price:
                                stale_reason = "buy_tp_not_above_market"
                        elif side == "sell":
                            if stop_price <= market_price:
                                stale_reason = "sell_stop_not_above_market"
                            elif tp1_price >= market_price:
                                stale_reason = "sell_tp_not_below_market"

                        if stale_reason:
                            heartbeat["actions"].append(
                                {
                                    "event": "skip_stale_market_levels",
                                    "symbol": symbol,
                                    "interval": interval,
                                    "reason": stale_reason,
                                    "market_price": round(market_price, 5),
                                    "entry": round(entry_price, 5),
                                    "stop_loss": round(stop_price, 5),
                                    "tp1": round(tp1_price, 5),
                                }
                            )
                            state.setdefault("last_trade_at", {})[key] = now_ts
                            state.setdefault("last_signature", {})[key] = signature
                            save_json(state_path, state)
                            continue

>>>>>>> Stashed changes
                sizing = calc_risk_volume(
                    bridge,
                    symbol=symbol,
                    entry=entry_price,
                    stop_loss=stop_price,
<<<<<<< Updated upstream
                    risk_percent=risk_percent_per_trade,
=======
                    risk_percent=float(config["risk_percent"]),
                    use_equity=bool(config.get("use_equity_for_risk", True)),
>>>>>>> Stashed changes
                )

                if fixed_volume > 0.0:
                    effective_volume = fixed_volume
                    if not sizing.get("success"):
                        sizing = {
                            "success": False,
                            "loss_per_lot": 0.0,
                            "equity": 0.0,
                        }
                else:
                    if not sizing.get("success"):
                        heartbeat["actions"].append({"event": "skip_sizing_error", "symbol": symbol, "error": sizing.get("error")})
                        continue
                    effective_volume = float(sizing["volume"])

                # Keep broker-valid volume. MT5 bridge handles TP splitting internally;
                # dividing here can push volume below broker minimum and reject the order.
                volume_rules = bridge.get_symbol_volume_rules(symbol)
                if bool(volume_rules.get("success")):
                    vol_min = float(volume_rules.get("volume_min") or 0.01)
                    vol_step = float(volume_rules.get("volume_step") or 0.01)
                    vol_max = float(volume_rules.get("volume_max") or 100.0)
                    effective_volume = normalize_volume(effective_volume, vol_min, vol_step, vol_max)

                estimated_loss_usd = float(sizing.get("loss_per_lot", 0.0)) * effective_volume
                account_equity = float(sizing.get("equity", 0.0) or 0.0)
                actual_risk_percent = (estimated_loss_usd / account_equity * 100.0) if account_equity > 0 else 0.0
                max_risk_usd_cap = float(config.get("max_risk_usd_per_trade", 8.0) or 0.0)
                max_risk_pct_equity = float(config.get("max_risk_percent_of_equity", 0.8))
<<<<<<< Updated upstream
                configured_risk_cap = (account_equity * risk_percent_per_trade / 100.0) if account_equity > 0 else 0.0
                equity_risk_cap = (account_equity * max_risk_pct_equity / 100.0) if account_equity > 0 else 0.0
                positive_risk_caps = [x for x in (configured_risk_cap, equity_risk_cap, max_risk_usd_cap) if x > 0]
                effective_risk_cap = min(positive_risk_caps) if positive_risk_caps else 0.0
                if effective_volume <= 0 or estimated_loss_usd <= 0:
=======
                equity_risk_cap = (account_equity * max_risk_pct_equity / 100.0) if account_equity > 0 else max_risk_usd_cap
                effective_risk_cap = min(max_risk_usd_cap, equity_risk_cap) if max_risk_usd_cap > 0 else equity_risk_cap
                if estimated_loss_usd > effective_risk_cap:
>>>>>>> Stashed changes
                    heartbeat["actions"].append(
                        {
                            "event": "skip_invalid_order_size",
                            "symbol": symbol,
                            "interval": interval,
                            "volume": effective_volume,
                            "estimated_loss_usd": round(estimated_loss_usd, 2),
                            "loss_per_lot": sizing.get("loss_per_lot"),
                        }
                    )
                    continue

                if effective_risk_cap > 0 and estimated_loss_usd > effective_risk_cap:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_order_size_above_risk",
                            "symbol": symbol,
                            "interval": interval,
                            "estimated_loss_usd": round(estimated_loss_usd, 2),
                            "risk_cap_usd": round(effective_risk_cap, 2),
                            "configured_risk_cap_usd": round(configured_risk_cap, 2),
                            "actual_risk_percent": round(actual_risk_percent, 4),
                            "risk_percent_per_trade": round(risk_percent_per_trade, 4),
                            "account_equity": round(account_equity, 2),
                            "max_risk_usd_per_trade": round(max_risk_usd_cap, 2),
                            "max_risk_percent_of_equity": round(max_risk_pct_equity, 3),
<<<<<<< Updated upstream
                            "raw_volume": sizing.get("raw_volume"),
                            "volume": effective_volume,
                            "volume_min": sizing.get("volume_min"),
=======
                            "risk_basis": sizing.get("risk_basis"),
                            "account_value_used": sizing.get("account_value_used"),
                            "calculated_risk_amount": sizing.get("risk_amount"),
>>>>>>> Stashed changes
                        }
                    )
                    continue

                payload = {
                    "symbol": symbol,
                    "interval": interval,
                    "signal_type": candidate["side"],
                    "entry": entry_price,
                    "stop_loss": stop_price,
                    "take_profit_1": tp1_price,
                    "take_profit_2": tp2_price,
                    "take_profit_3": tp3_price,
                    "volume": effective_volume,
                    "split_tp": split_tp,
                    "tp_execution_mode": tp_execution_mode,
                    "split_tp_volume_mode": config.get("split_tp_volume_mode", "weighted"),
                    "comment_interval_tag_enabled": config.get("comment_interval_tag_enabled", True),
                    "pending_entry": pending_entry,
                    "dry_run": bool(config.get("dry_run", True)),
                    "source": candidate.get("source", "analysis"),
                    "source_signal_id": candidate.get("signal_id"),
                }
                if not pending_entry:
                    tick_confirmation = tick_confirmation_check(
                        bridge=bridge,
                        config=config,
                        symbol=symbol,
                        side=str(candidate.get("side") or ""),
                        risk_distance=risk_distance,
                    )
                    if not tick_confirmation.get("allowed"):
                        heartbeat["actions"].append(
                            {
                                "event": "skip_tick_confirmation",
                                "symbol": symbol,
                                "interval": interval,
                                **tick_confirmation,
                            }
                        )
                        continue
                execution = bridge.execute_signal(payload)
                ok = bool(execution.get("success"))
                exec_error = execution.get("error")
                if (not exec_error) and isinstance(execution.get("orders"), list):
                    for order_row in execution.get("orders"):
                        if isinstance(order_row, dict) and order_row.get("error"):
                            exec_error = order_row.get("error")
                            break

                # Some brokers reject pending entries for distance/filling constraints.
                # Retry once as a market order to avoid dropping a valid high-confidence signal.
                if (not ok) and pending_entry and bool(config.get("pending_fallback_to_market", True)):
                    market_payload = dict(payload)
                    market_payload["pending_entry"] = False
                    fallback_execution = bridge.execute_signal(market_payload)
                    fallback_ok = bool(fallback_execution.get("success"))
                    fallback_error = fallback_execution.get("error")
                    if (not fallback_error) and isinstance(fallback_execution.get("orders"), list):
                        for order_row in fallback_execution.get("orders"):
                            if isinstance(order_row, dict) and order_row.get("error"):
                                fallback_error = order_row.get("error")
                                break

                    heartbeat["actions"].append(
                        {
                            "event": "pending_to_market_fallback",
                            "symbol": symbol,
                            "interval": interval,
                            "success": fallback_ok,
                            "error": fallback_error,
                        }
                    )

                    if fallback_ok:
                        execution = fallback_execution
                        ok = True
                        exec_error = None
                        pending_entry = False

                heartbeat["actions"].append(
                    {
                        "event": "execute_signal",
                        "symbol": symbol,
                        "interval": interval,
                        "source": candidate.get("source", "analysis"),
                        "signal_id": candidate.get("signal_id"),
                        "recommendation": candidate["recommendation"],
                        "analysis_source": candidate.get("analysis_source"),
                        "market_data_source": candidate.get("market_data_source"),
                        "dry_run": bool(config.get("dry_run", True)),
                        "success": ok,
                        "error": exec_error,
                        "volume": effective_volume,
                        "raw_volume": sizing.get("raw_volume"),
                        "estimated_loss_usd": round(estimated_loss_usd, 2),
<<<<<<< Updated upstream
                        "actual_risk_percent": round(actual_risk_percent, 4),
                        "risk_cap_usd": round(effective_risk_cap, 2),
=======
                        "risk_basis": sizing.get("risk_basis"),
                        "account_value_used": sizing.get("account_value_used"),
                        "calculated_risk_amount": sizing.get("risk_amount"),
                        "loss_per_lot": sizing.get("loss_per_lot"),
>>>>>>> Stashed changes
                        "rr_ratio": round(rr_ratio, 3),
                        "stop_distance_percent": round(stop_distance_pct, 3),
                        "pending_entry": pending_entry,
                        "tp_execution_mode": tp_execution_mode,
                        "market_repriced": market_repriced,
                        "market_drift_percent": round(market_drift_pct, 3) if market_drift_pct is not None else None,
                        "gold_scalping_levels": gold_scalping_levels,
                        "fixed_tp_mode": fixed_tp_meta,
                        "forex_scalping_levels": forex_scalping_levels,
                    }
                )

                # Always save signature after attempt to prevent stale-signal retry loops.
                # A failed order due to invalid SL/TP means the signal price is stale;
                # retrying every scan cycle wastes resources and distorts loss counters.
                is_stale_rejection = (not ok) and exec_error and (
                    "وقف خسارة" in str(exec_error)
                    or "هدف غير صالح" in str(exec_error)
                    or "invalid" in str(exec_error).lower()
                    or "10016" in str(exec_error)  # MT5 TRADE_RETCODE_INVALID_STOPS
                    or "10015" in str(exec_error)  # MT5 TRADE_RETCODE_INVALID_PRICE
                )
                if is_stale_rejection:
                    # Block this stale signal for one cooldown window then allow retry
                    state.setdefault("last_trade_at", {})[key] = now_ts
                    state.setdefault("last_signature", {})[key] = signature
                    save_json(state_path, state)

                if ok:
                    executed_this_cycle += 1
                    occupied_symbols.add(symbol)
                    current_open_count += 1

                    state.setdefault("last_trade_at", {})[key] = now_ts
                    state.setdefault("last_signature", {})[key] = signature

                    site_activation = mark_site_signal_activated(config, candidate)
                    if not site_activation.get("skipped"):
                        heartbeat["actions"].append(
                            {
                                "event": "site_signal_mark_activated",
                                "symbol": symbol,
                                "signal_id": candidate.get("signal_id"),
                                "success": bool(site_activation.get("success")),
                                "updated": site_activation.get("updated"),
                                "error": site_activation.get("error"),
                            }
                        )

                    if pending_entry and not bool(config.get("dry_run", True)):
                        pending_expiry_minutes = max(1, int(config.get("pending_expiry_minutes", 180) or 180))
                        expires_at = now_ts + (pending_expiry_minutes * 60)
                        pending_tickets = extract_pending_order_tickets(execution)
                        current_pending_count += max(1, len(pending_tickets))
                        for ticket in pending_tickets:
                            live_pending_orders.append(
                                {
                                    "ticket": ticket,
                                    "symbol": symbol,
                                    "side": str(candidate["side"]),
                                    "price": entry_price,
                                    "price_open": entry_price,
                                }
                            )
                            state.setdefault("pending_orders", {})[str(ticket)] = {
                                "symbol": symbol,
                                "interval": interval,
                                "side": str(candidate["side"]),
                                "created_at": now_ts,
                                "expires_at": expires_at,
                                "signature": signature,
                                "source": candidate.get("source", "analysis"),
                                "signal_id": candidate.get("signal_id"),
                            }

                    save_json(state_path, state)

        print(json.dumps(heartbeat, ensure_ascii=False))

        if once:
            return 0
        time.sleep(config["scan_every_sec"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Continuous auto trader with user-selected symbols and intervals")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "auto_trading_user_config.json"), help="Path to config JSON file")
    parser.add_argument("--state", default=str(PROJECT_ROOT / "auto_trading_runtime_state.json"), help="Path to runtime state file")
    parser.add_argument("--wallet-config", default="", help="Path to MT5 wallet config JSON (login/server/path) for this account")
    parser.add_argument("--account-id", default="", help="Unique id for this account/wallet (namespaces the single-instance lock)")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup and save config")
    parser.add_argument("--once", action="store_true", help="Run one scan cycle only")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

<<<<<<< Updated upstream
=======
    # Pin this process to a specific wallet/account BEFORE locking or connecting,
    # so the lock is namespaced per account and MT5Bridge loads the right wallet.
>>>>>>> Stashed changes
    if str(getattr(args, "account_id", "") or "").strip():
        os.environ["AUTO_TRADER_ACCOUNT_ID"] = str(args.account_id).strip()
    if str(getattr(args, "wallet_config", "") or "").strip():
        os.environ["MT5_WALLET_CONFIG"] = str(Path(args.wallet_config).expanduser())

    if not acquire_single_instance_lock():
        print(json.dumps({"event": "already_running", "message": "Trader instance already active"}, ensure_ascii=False))
        raise SystemExit(0)

    config_path = Path(args.config)
    state_path = Path(args.state)

    if args.setup:
        interactive_setup(config_path)
        raise SystemExit(0)

    if not config_path.exists():
        save_json(config_path, merge_config({}))

    if bool(args.once):
        raise SystemExit(run_loop(config_path=config_path, state_path=state_path, once=True))

    # Keep process alive even if an unexpected exception bubbles up from run_loop.
    while True:
        try:
            code = run_loop(config_path=config_path, state_path=state_path, once=False)
            if int(code) == 0:
                raise SystemExit(0)
            print(json.dumps({"event": "run_loop_exit", "code": int(code)}, ensure_ascii=False))
        except KeyboardInterrupt:
            raise
        except BaseException as exc:
            print(
                json.dumps(
                    {
                        "event": "runtime_exception",
                        "error": str(exc),
                        "type": type(exc).__name__,
                        "traceback": traceback.format_exc(limit=8),
                    },
                    ensure_ascii=False,
                )
            )
        time.sleep(5)

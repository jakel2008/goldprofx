import argparse
import atexit
import json
import math
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
APP_ROOT = PROJECT_ROOT / "my-forex-app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from services.advanced_analyzer_engine import SUPPORTED_INTERVALS, SUPPORTED_SYMBOLS, perform_full_analysis
from mt5_bridge import MT5Bridge, mt5


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


DEFAULT_CONFIG = {
    "enabled": True,
    "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"],
    "intervals": ["1h", "4h"],
    "risk_percent": 1.0,
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
    "cancel_expired_pending": True,
    "cancel_on_market_invalidation": True,
    "split_tp": True,
    "trading_sessions_utc": [{"start": "06:00", "end": "22:00", "weekdays": [0, 1, 2, 3, 4]}],
    "daily_loss_limit_usd": 25.0,
    "daily_loss_limit_percent_of_equity": 0.0,
    "daily_loss_limit_follow_risk_percent": True,
    "max_consecutive_losses": 3,
    "dry_run": True,
    "signal_source": "analysis",
    "site_signals_db_path": "vip_signals.db",
    "site_signals_limit": 30,
    "site_signals_max_age_minutes": 1,
    "site_signals_min_quality": 0,
    "site_signal_symbols": [],
}


def recommendation_side(recommendation: str) -> str:
    text = str(recommendation or "").strip()
    if "شراء" in text:
        return "buy"
    if "بيع" in text:
        return "sell"
    return "none"


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
    use_equity = bool(bridge.config.get("use_equity_for_risk", True)) if hasattr(bridge, "config") and isinstance(bridge.config, dict) else True
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
    merged["intervals"] = [str(item).strip().lower() for item in merged.get("intervals", []) if str(item).strip().lower() in SUPPORTED_INTERVALS]
    merged["blocked_symbols"] = [re.sub(r"[^A-Z0-9]", "", str(item).upper()) for item in merged.get("blocked_symbols", []) if str(item).strip()]
    merged["site_signal_symbols"] = [re.sub(r"[^A-Z0-9*]", "", str(item).upper()) for item in merged.get("site_signal_symbols", []) if str(item).strip()]
    if not merged["symbols"] and signal_source == "analysis":
        merged["symbols"] = list(DEFAULT_CONFIG["symbols"])
    if not merged["intervals"]:
        merged["intervals"] = list(DEFAULT_CONFIG["intervals"])
    merged["scan_every_sec"] = max(15, int(merged.get("scan_every_sec", 60)))
    merged["risk_percent"] = max(0.1, float(merged.get("risk_percent", 1.0)))
    merged["use_equity_for_risk"] = bool(merged.get("use_equity_for_risk", True))
    merged["max_risk_usd_per_trade"] = max(0.0, float(merged.get("max_risk_usd_per_trade", 8.0)))
    merged["max_risk_percent_of_equity"] = max(0.1, float(merged.get("max_risk_percent_of_equity", 0.8)))
    merged["max_stop_distance_percent"] = max(0.1, float(merged.get("max_stop_distance_percent", 1.2)))
    merged["max_target_distance_percent"] = max(0.1, float(merged.get("max_target_distance_percent", 3.5)))
    merged["min_rr_ratio"] = max(0.1, float(merged.get("min_rr_ratio", 1.1)))
    merged["cooldown_minutes_per_symbol"] = max(0, int(merged.get("cooldown_minutes_per_symbol", 90)))
    merged["max_open_positions"] = max(0, int(merged.get("max_open_positions", 0)))
    merged["dynamic_max_positions_enabled"] = bool(merged.get("dynamic_max_positions_enabled", True))
    merged["max_total_open_risk_percent"] = max(0.1, float(merged.get("max_total_open_risk_percent", 2.1)))
    merged["min_open_positions"] = max(1, int(merged.get("min_open_positions", 3)))
    merged["max_open_positions_cap"] = max(0, int(merged.get("max_open_positions_cap", 24)))
    merged["min_score_gap"] = max(0, int(merged.get("min_score_gap", 18)))
    merged["daily_loss_limit_usd"] = max(0.0, float(merged.get("daily_loss_limit_usd", 25.0)))
    merged["daily_loss_limit_follow_risk_percent"] = bool(merged.get("daily_loss_limit_follow_risk_percent", True))
    daily_loss_percent = max(0.0, float(merged.get("daily_loss_limit_percent_of_equity", 0.0)))
    if merged["daily_loss_limit_usd"] <= 0 and merged["daily_loss_limit_follow_risk_percent"]:
        daily_loss_percent = float(merged["risk_percent"])
    merged["daily_loss_limit_percent_of_equity"] = daily_loss_percent
    merged["max_consecutive_losses"] = max(0, int(merged.get("max_consecutive_losses", 3)))
    merged["site_signals_limit"] = max(1, min(200, int(merged.get("site_signals_limit", 30))))
    merged["site_signals_max_age_minutes"] = max(0, int(merged.get("site_signals_max_age_minutes", 180)))
    merged["site_signals_min_quality"] = max(0, min(100, int(merged.get("site_signals_min_quality", 0))))

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

    closed_positions = sorted(by_position.values(), key=lambda x: int(x.get("close_time", 0) or 0), reverse=True)
    consecutive_losses = 0
    for row in closed_positions:
        pnl = float(row.get("pnl", 0.0) or 0.0)
        if pnl < 0:
            consecutive_losses += 1
        else:
            break

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
    max_consecutive_losses = max(0, int(config.get("max_consecutive_losses", 3) or 3))
    breached_daily_loss = loss_limit > 0 and daily_pnl <= -loss_limit
    breached_consecutive = max_consecutive_losses > 0 and consecutive_losses >= max_consecutive_losses

    return {
        "success": True,
        "daily_realized_pnl_usd": round(daily_pnl, 2),
        "daily_loss_limit_usd": round(loss_limit, 2),
        "daily_loss_limit_source": loss_limit_source,
        "daily_loss_limit_percent_of_equity": round(percent_loss_limit, 4),
        "daily_loss_limit_follow_risk_percent": bool(config.get("daily_loss_limit_follow_risk_percent", True)),
        "account_equity": round(account_equity, 2),
        "risk_window_start_utc": reset_after_utc.isoformat(timespec="seconds"),
        "consecutive_losses": consecutive_losses,
        "max_consecutive_losses": max_consecutive_losses,
        "closed_positions_today": len(closed_positions),
        "breached_daily_loss_limit": breached_daily_loss,
        "breached_consecutive_losses": breached_consecutive,
        "blocked": breached_daily_loss or breached_consecutive,
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


def list_pending_order_tickets_by_magic(magic: int) -> set[int]:
    if mt5 is None:
        return set()
    rows = mt5.orders_get() or []
    tickets = set()
    for row in rows:
        if int(getattr(row, "magic", 0) or 0) == int(magic):
            tickets.add(int(getattr(row, "ticket", 0) or 0))
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


def count_open_trade_slots(open_positions: list[dict], one_position_per_symbol: bool) -> int:
    if not one_position_per_symbol:
        return len(open_positions)
    occupied = {to_base_symbol(pos.get("symbol")) for pos in open_positions}
    return len(occupied)


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
        in_session, session_reason = _is_within_utc_sessions(config, now_utc)
        if not in_session:
            print(
                json.dumps(
                    {
                        "event": "outside_trading_session",
                        "time_utc": now_utc.isoformat(timespec="seconds"),
                        "reason": session_reason,
                        "sessions_utc": config.get("trading_sessions_utc", []),
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
                        "daily_loss_limit_source": risk_guard.get("daily_loss_limit_source"),
                        "daily_loss_limit_percent_of_equity": risk_guard.get("daily_loss_limit_percent_of_equity"),
                        "account_equity": risk_guard.get("account_equity"),
                        "consecutive_losses": risk_guard.get("consecutive_losses"),
                        "max_consecutive_losses": risk_guard.get("max_consecutive_losses"),
                        "breached_daily_loss_limit": risk_guard.get("breached_daily_loss_limit"),
                        "breached_consecutive_losses": risk_guard.get("breached_consecutive_losses"),
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
        now_ts = int(time.time())

        maintenance_actions = []
        if bool(config.get("cancel_expired_pending", True)):
            maintenance_actions.extend(cleanup_expired_pending_orders(bridge=bridge, state=state, now_ts=now_ts))

        if bool(config.get("cancel_on_market_invalidation", True)):
            maintenance_actions.extend(cleanup_invalidated_pending_orders(bridge=bridge, state=state, config=config))

        if maintenance_actions:
            save_json(state_path, state)

        max_cfg = resolve_effective_max_open_positions(config)
        max_open_positions = int(max_cfg.get("effective_max_open_positions", 0) or 0)
        one_position_per_symbol = bool(config.get("one_position_per_symbol", True))
        open_trade_slots = count_open_trade_slots(open_positions, one_position_per_symbol=one_position_per_symbol)

        if max_open_positions > 0 and open_trade_slots >= max_open_positions:
            print(
                json.dumps(
                    {
                        "event": "max_open_positions_reached",
                        "count": open_trade_slots,
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

        ranked_candidates = select_ranked_candidates(config, analyses)
        best = ranked_candidates[0] if ranked_candidates else None
        heartbeat = {
            "event": "scan",
            "time": datetime.now().isoformat(timespec="seconds"),
            "time_utc": now_utc.isoformat(timespec="seconds"),
            "symbols": config["symbols"],
            "intervals": config["intervals"],
            "signal_source": signal_source,
            "site_signals": site_signal_stats,
            "session_match": session_reason,
            "risk_guard": {
                "daily_realized_pnl_usd": risk_guard.get("daily_realized_pnl_usd"),
                "daily_loss_limit_usd": risk_guard.get("daily_loss_limit_usd"),
                "daily_loss_limit_source": risk_guard.get("daily_loss_limit_source"),
                "daily_loss_limit_percent_of_equity": risk_guard.get("daily_loss_limit_percent_of_equity"),
                "account_equity": risk_guard.get("account_equity"),
                "consecutive_losses": risk_guard.get("consecutive_losses"),
                "max_consecutive_losses": risk_guard.get("max_consecutive_losses"),
                "closed_positions_today": risk_guard.get("closed_positions_today"),
            },
            "candidates": len(analyses),
            "open_positions": len(open_positions),
            "open_trade_slots": open_trade_slots,
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
            } if best else None,
            "actions": [],
        }

        if ranked_candidates:
            max_trades_per_cycle = max(1, int(config.get("max_trades_per_cycle", 3)))
            executed_this_cycle = 0
            occupied_symbols = {to_base_symbol(pos.get("symbol")) for pos in open_positions}
            current_open_count = open_trade_slots

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
                
                entry_price = float(candidate["entry"])
                stop_price = float(candidate["stop_loss"])
                tp1_price = float(candidate["tp1"])
                tp2_price = float(candidate.get("tp2") or candidate["tp1"])
                tp3_price = float(candidate.get("tp3") or candidate["tp1"])

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
                reward_distance = abs(tp1_price - entry_price)
                rr_ratio = (reward_distance / risk_distance) if risk_distance > 0 else 0.0
                min_rr_ratio = float(config.get("min_rr_ratio", 1.1))
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

                cooldown_minutes = int(config.get("cooldown_minutes_per_symbol", 90))
                last_trade_map = state.get("last_trade_at", {})
                key = f"{symbol}:{interval}"
                last_ts = int(last_trade_map.get(key, 0) or 0)
                in_cooldown = cooldown_minutes > 0 and (now_ts - last_ts) < (cooldown_minutes * 60)

                signature = f"{candidate.get('source', 'analysis')}|{candidate.get('signal_id', '')}|{symbol}|{interval}|{candidate['recommendation']}|{candidate['entry']}|{candidate['stop_loss']}|{candidate['tp1']}"
                last_sig_map = state.get("last_signature", {})
                same_signature = str(last_sig_map.get(key, "")) == signature

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

                if same_signature:
                    heartbeat["actions"].append(
                        {
                            "event": "skip_duplicate_signature",
                            "symbol": symbol,
                            "interval": interval,
                        }
                    )
                    continue

                risk_percent_per_trade = float(config["risk_percent"])
                sizing = calc_risk_volume(
                    bridge,
                    symbol=symbol,
                    entry=entry_price,
                    stop_loss=stop_price,
                    risk_percent=risk_percent_per_trade,
                )
                if not sizing.get("success"):
                    heartbeat["actions"].append({"event": "skip_sizing_error", "symbol": symbol, "error": sizing.get("error")})
                    continue

                pending_entry = bool(config.get("pending_entry", False))
                split_tp = bool(config.get("split_tp", True))
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
                configured_risk_cap = (account_equity * risk_percent_per_trade / 100.0) if account_equity > 0 else 0.0
                equity_risk_cap = (account_equity * max_risk_pct_equity / 100.0) if account_equity > 0 else 0.0
                positive_risk_caps = [x for x in (configured_risk_cap, equity_risk_cap, max_risk_usd_cap) if x > 0]
                effective_risk_cap = min(positive_risk_caps) if positive_risk_caps else 0.0
                if effective_volume <= 0 or estimated_loss_usd <= 0:
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
                            "raw_volume": sizing.get("raw_volume"),
                            "volume": effective_volume,
                            "volume_min": sizing.get("volume_min"),
                        }
                    )
                    continue

                payload = {
                    "symbol": symbol,
                    "signal_type": candidate["side"],
                    "entry": candidate["entry"],
                    "stop_loss": candidate["stop_loss"],
                    "take_profit_1": candidate["tp1"],
                    "take_profit_2": candidate["tp2"],
                    "take_profit_3": candidate["tp3"],
                    "volume": effective_volume,
                    "split_tp": split_tp,
                    "pending_entry": pending_entry,
                    "dry_run": bool(config.get("dry_run", True)),
                    "source": candidate.get("source", "analysis"),
                    "source_signal_id": candidate.get("signal_id"),
                }
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
                if (not ok) and pending_entry:
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
                        "dry_run": bool(config.get("dry_run", True)),
                        "success": ok,
                        "error": exec_error,
                        "volume": effective_volume,
                        "raw_volume": sizing.get("raw_volume"),
                        "estimated_loss_usd": round(estimated_loss_usd, 2),
                        "actual_risk_percent": round(actual_risk_percent, 4),
                        "risk_cap_usd": round(effective_risk_cap, 2),
                        "rr_ratio": round(rr_ratio, 3),
                        "stop_distance_percent": round(stop_distance_pct, 3),
                        "pending_entry": pending_entry,
                    }
                )

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
                        pending_tickets = extract_pending_order_tickets(execution)
                        for ticket in pending_tickets:
                            state.setdefault("pending_orders", {})[str(ticket)] = {
                                "symbol": symbol,
                                "interval": interval,
                                "side": str(candidate["side"]),
                                "created_at": now_ts,
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

    raise SystemExit(run_loop(config_path=config_path, state_path=state_path, once=bool(args.once)))

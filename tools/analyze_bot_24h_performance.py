import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import MetaTrader5 as mt5

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mt5_bridge import MT5Bridge
ENTRY_OUT_VALUES = {1, 2, 3}
ENTRY_IN_VALUES = {0, 2}

ACCOUNTS = [
    {
        "id": "account1_gold",
        "wallet": PROJECT_ROOT / "accounts" / "account1_gold" / "wallet.json",
        "config": PROJECT_ROOT / "accounts" / "account1_gold" / "config.json",
        "log": PROJECT_ROOT / "accounts" / "account1_gold" / "trader.out.log",
    },
    {
        "id": "account2_bitcoin",
        "wallet": PROJECT_ROOT / "accounts" / "account2_bitcoin" / "wallet.json",
        "config": PROJECT_ROOT / "accounts" / "account2_bitcoin" / "config.json",
        "log": PROJECT_ROOT / "accounts" / "account2_bitcoin" / "trader.out.log",
    },
]


def round2(value):
    return round(float(value or 0.0), 2)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig") or "{}")
    except Exception as exc:
        return {"_error": str(exc)}


def namedtuple_to_dict(item) -> dict:
    return item._asdict() if hasattr(item, "_asdict") else {}


def iso_time(timestamp) -> str | None:
    try:
        raw = int(timestamp or 0)
    except Exception:
        raw = 0
    if not raw:
        return None
    return datetime.fromtimestamp(raw, timezone.utc).isoformat(timespec="seconds")


def summarize_deals(deals: list, magic: int) -> dict:
    all_deals = [namedtuple_to_dict(deal) for deal in deals]
    bot_deals = [deal for deal in all_deals if int(deal.get("magic") or 0) == int(magic)]
    fallback_symbol_filter_used = False
    if not bot_deals:
        bot_deals = [deal for deal in all_deals if str(deal.get("symbol") or "").upper().startswith("XAU")]
        fallback_symbol_filter_used = True

    exit_deals = [deal for deal in bot_deals if int(deal.get("entry") or 0) in ENTRY_OUT_VALUES]
    entry_deals = [deal for deal in bot_deals if int(deal.get("entry") or 0) in ENTRY_IN_VALUES]

    by_position = defaultdict(list)
    for deal in bot_deals:
        position_id = str(deal.get("position_id") or deal.get("order") or "")
        by_position[position_id].append(deal)

    closed_trades = []
    for position_id, rows in by_position.items():
        exits = [deal for deal in rows if int(deal.get("entry") or 0) in ENTRY_OUT_VALUES]
        if not exits:
            continue

        rows_sorted = sorted(rows, key=lambda item: int(item.get("time") or 0))
        first = rows_sorted[0]
        last = rows_sorted[-1]
        pnl = sum(
            float(deal.get("profit") or 0.0)
            + float(deal.get("commission") or 0.0)
            + float(deal.get("swap") or 0.0)
            for deal in exits
        )
        volume_out = sum(float(deal.get("volume") or 0.0) for deal in exits)
        first_type = int(first.get("type") or -1)
        direction = "BUY" if first_type == 0 else "SELL" if first_type == 1 else "unknown"
        closed_trades.append(
            {
                "position_id": position_id,
                "symbol": str(first.get("symbol") or last.get("symbol") or ""),
                "direction": direction,
                "open_time_utc": iso_time(first.get("time")),
                "close_time_utc": iso_time(last.get("time")),
                "volume_closed": round(float(volume_out), 3),
                "pnl": round2(pnl),
                "exit_count": len(exits),
                "comment": str(last.get("comment") or ""),
            }
        )

    closed_trades.sort(key=lambda item: item.get("close_time_utc") or "")
    wins = [trade for trade in closed_trades if trade["pnl"] > 0]
    losses = [trade for trade in closed_trades if trade["pnl"] < 0]
    flats = [trade for trade in closed_trades if trade["pnl"] == 0]
    gross_profit = sum(trade["pnl"] for trade in wins)
    gross_loss = sum(trade["pnl"] for trade in losses)
    net_pnl = gross_profit + gross_loss
    return {
        "fallback_symbol_filter_used": fallback_symbol_filter_used,
        "deal_count": len(bot_deals),
        "entry_deal_count": len(entry_deals),
        "exit_deal_count": len(exit_deals),
        "closed_trade_count": len(closed_trades),
        "wins": len(wins),
        "losses": len(losses),
        "flats": len(flats),
        "win_rate_percent": round((len(wins) / len(closed_trades) * 100), 1) if closed_trades else 0.0,
        "gross_profit": round2(gross_profit),
        "gross_loss": round2(gross_loss),
        "net_pnl": round2(net_pnl),
        "profit_factor": None if gross_loss == 0 else round(abs(gross_profit / gross_loss), 3),
        "avg_win": round2(gross_profit / len(wins)) if wins else 0.0,
        "avg_loss": round2(gross_loss / len(losses)) if losses else 0.0,
        "best_trade": max([trade["pnl"] for trade in closed_trades], default=0.0),
        "worst_trade": min([trade["pnl"] for trade in closed_trades], default=0.0),
        "closed_trades": closed_trades,
    }


def summarize_log(path: Path, start: datetime) -> dict:
    summary = {
        "exists": path.exists(),
        "execute_signal_events": 0,
        "skip_gold_market_closed": 0,
        "risk_guard_blocked": 0,
        "max_open_positions_reached": 0,
        "skip_existing_symbol_position": 0,
        "last_events": [],
    }
    if not path.exists():
        return summary

    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as exc:
        summary["error"] = str(exc)
        return summary

    for line in lines[-3000:]:
        if "execute_signal" in line:
            summary["execute_signal_events"] += 1
        if "skip_gold_market_closed" in line:
            summary["skip_gold_market_closed"] += 1
        if "risk_guard_blocked" in line:
            summary["risk_guard_blocked"] += 1
        if "max_open_positions_reached" in line:
            summary["max_open_positions_reached"] += 1
        if "skip_existing_symbol_position" in line:
            summary["skip_existing_symbol_position"] += 1
        if any(token in line for token in ("execute_signal", "risk_guard_blocked", "skip_gold_market_closed", "max_open_positions_reached")):
            summary["last_events"].append(line[-500:])

    summary["last_events"] = summary["last_events"][-10:]
    return summary


def account_report(account: dict, start: datetime, end: datetime) -> dict:
    os.environ["MT5_WALLET_CONFIG"] = str(account["wallet"])
    cfg = load_json(account["config"])
    bridge = MT5Bridge()
    item = {"id": account["id"], "wallet": str(account["wallet"]), "magic": int(bridge.magic)}
    try:
        connection = bridge.connect()
        item["connect"] = bool(connection.get("success"))
        item["connect_error"] = connection.get("error")
        account_info = mt5.account_info()
        item["account"] = None if account_info is None else {
            "login": int(account_info.login),
            "server": str(account_info.server),
            "balance": round2(account_info.balance),
            "equity": round2(account_info.equity),
            "floating_profit": round2(account_info.profit),
        }
        item["magic"] = int(bridge.magic)
        deals = list(mt5.history_deals_get(start, end) or [])
        item["history"] = summarize_deals(deals, int(bridge.magic))
        positions = [
            position._asdict()
            for position in list(mt5.positions_get() or [])
            if int(getattr(position, "magic", 0) or 0) == int(bridge.magic)
        ]
        orders = [
            order._asdict()
            for order in list(mt5.orders_get() or [])
            if int(getattr(order, "magic", 0) or 0) == int(bridge.magic)
        ]
        item["open_positions"] = [
            {
                "ticket": int(position.get("ticket") or 0),
                "symbol": str(position.get("symbol") or ""),
                "side": "BUY" if int(position.get("type") or 0) == 0 else "SELL",
                "volume": float(position.get("volume") or 0.0),
                "open_price": round(float(position.get("price_open") or 0.0), 3),
                "sl": round(float(position.get("sl") or 0.0), 3),
                "tp": round(float(position.get("tp") or 0.0), 3),
                "profit": round2(position.get("profit") or 0.0),
            }
            for position in positions
        ]
        item["pending_orders"] = len(orders)
    except Exception as exc:
        item["error"] = str(exc)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass

    item["config"] = {
        key: cfg.get(key)
        for key in [
            "enabled",
            "dry_run",
            "symbols",
            "max_open_positions",
            "one_position_per_symbol",
            "gold_scalping_entry_intervals",
            "gold_scalping_context_intervals",
            "gold_scalping_min_context_agreement",
            "gold_scalping_require_rsi_momentum",
            "daily_loss_limit_usd",
            "daily_loss_reset_at_utc",
            "force_gold_trading_now",
        ]
    }
    item["log_summary"] = summarize_log(account["log"], start)
    return item


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze MT5 bot performance for the active wallets.")
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=max(1.0, float(args.hours)))
    report = {
        "window_utc": {"start": start.isoformat(timespec="seconds"), "end": end.isoformat(timespec="seconds")},
        "accounts": [account_report(account, start, end) for account in ACCOUNTS],
    }
    if args.summary_only:
        for account in report["accounts"]:
            history = account.get("history") or {}
            closed_trades = list(history.pop("closed_trades", []) or [])
            history["first_trade"] = closed_trades[0] if closed_trades else None
            history["last_trade"] = closed_trades[-1] if closed_trades else None
            buckets = defaultdict(lambda: {"count": 0, "pnl": 0.0, "wins": 0, "losses": 0})
            max_loss_streak = 0
            current_loss_streak = 0
            for trade in closed_trades:
                close_time = str(trade.get("close_time_utc") or "")
                hour_key = close_time[:13] if len(close_time) >= 13 else "unknown"
                bucket = buckets[hour_key]
                bucket["count"] += 1
                bucket["pnl"] += float(trade.get("pnl") or 0.0)
                if float(trade.get("pnl") or 0.0) > 0:
                    bucket["wins"] += 1
                    current_loss_streak = 0
                elif float(trade.get("pnl") or 0.0) < 0:
                    bucket["losses"] += 1
                    current_loss_streak += 1
                    max_loss_streak = max(max_loss_streak, current_loss_streak)
            history["max_loss_streak"] = max_loss_streak
            history["trades_by_hour_utc"] = [
                {
                    "hour": key,
                    "count": value["count"],
                    "wins": value["wins"],
                    "losses": value["losses"],
                    "pnl": round2(value["pnl"]),
                }
                for key, value in sorted(buckets.items())
            ]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
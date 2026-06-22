import argparse
import json
import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
APP_ROOT = PROJECT_ROOT / "my-forex-app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from services.advanced_analyzer_engine import perform_full_analysis
from mt5_bridge import MT5Bridge, mt5


ACTION_MAP = {
    "شراء": "buy",
    "شراء قوي": "buy",
    "بيع": "sell",
    "بيع قوي": "sell",
}


def normalize_volume(value: float, vol_min: float, vol_step: float, vol_max: float) -> float:
    if vol_step <= 0:
        vol_step = 0.01
    stepped = math.floor(value / vol_step) * vol_step
    bounded = max(vol_min, min(vol_max, stepped))
    return round(bounded, 6)


def calc_risk_volume(bridge: MT5Bridge, symbol: str, entry: float, stop_loss: float, risk_percent: float) -> dict:
    resolved = bridge._resolve_symbol_name(symbol)  # Uses broker symbol mapping rules already in bridge.
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

    risk_amount = float(account.balance) * (risk_percent / 100.0)
    loss_per_lot = (distance / tick_size) * tick_value
    raw_volume = risk_amount / loss_per_lot
    volume = normalize_volume(raw_volume, vol_min, vol_step, vol_max)

    return {
        "success": True,
        "resolved_symbol": resolved,
        "balance": float(account.balance),
        "risk_amount": round(risk_amount, 2),
        "loss_per_lot": round(loss_per_lot, 2),
        "volume": volume,
        "volume_min": vol_min,
        "volume_step": vol_step,
        "volume_max": vol_max,
    }


def build_signal_payload(analysis: dict, volume: float, dry_run: bool, pending_entry: bool) -> dict:
    return {
        "symbol": analysis["symbol"],
        "signal_type": ACTION_MAP.get(analysis["recommendation"], ""),
        "entry": analysis["entry_point"],
        "stop_loss": analysis["stop_loss"],
        "take_profit_1": analysis["take_profit1"],
        "take_profit_2": analysis["take_profit2"],
        "take_profit_3": analysis["take_profit3"],
        "volume": volume,
        "split_tp": True,
        "pending_entry": bool(pending_entry),
        "dry_run": bool(dry_run),
    }


def execute_plan(symbols: list[str], interval: str, risk_percent: float, execute_live: bool, pending_entry: bool) -> dict:
    bridge = MT5Bridge()
    conn = bridge.connect()
    if not conn.get("success"):
        return {"success": False, "error": conn.get("error"), "status": conn.get("status")}

    outputs = []
    for symbol in symbols:
        analysis = perform_full_analysis(symbol, interval)
        if not analysis.get("success"):
            outputs.append({"symbol": symbol, "success": False, "error": analysis.get("error")})
            continue

        recommendation = analysis.get("recommendation")
        side = ACTION_MAP.get(str(recommendation or ""))
        if not side:
            outputs.append(
                {
                    "symbol": symbol,
                    "success": False,
                    "skipped": True,
                    "reason": f"Recommendation is not tradable: {recommendation}",
                }
            )
            continue

        sizing = calc_risk_volume(
            bridge,
            symbol,
            float(analysis["entry_point"]),
            float(analysis["stop_loss"]),
            risk_percent,
        )
        if not sizing.get("success"):
            outputs.append({"symbol": symbol, "success": False, "error": sizing.get("error"), "sizing": sizing})
            continue

        payload = build_signal_payload(
            analysis,
            volume=float(sizing["volume"]),
            dry_run=not execute_live,
            pending_entry=pending_entry,
        )
        exec_result = bridge.execute_signal(payload)

        outputs.append(
            {
                "symbol": symbol,
                "success": bool(exec_result.get("success")),
                "recommendation": recommendation,
                "confidence": analysis.get("confidence"),
                "risk_reward_ratio": analysis.get("risk_reward_ratio"),
                "market_regime": analysis.get("market_regime"),
                "quality_notes": analysis.get("quality_notes"),
                "entry": analysis.get("entry_point"),
                "stop_loss": analysis.get("stop_loss"),
                "tp1": analysis.get("take_profit1"),
                "tp2": analysis.get("take_profit2"),
                "tp3": analysis.get("take_profit3"),
                "sizing": sizing,
                "payload": payload,
                "execution": exec_result,
            }
        )

    return {
        "success": True,
        "mode": "live" if execute_live else "dry_run",
        "interval": interval,
        "risk_percent": risk_percent,
        "pending_entry": pending_entry,
        "results": outputs,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute professional MT5 plans from analyzer signals")
    parser.add_argument("--symbols", default="BTCUSD,GBPUSD,USDJPY", help="Comma-separated symbols")
    parser.add_argument("--interval", default="1h", help="Analysis interval, e.g. 1h,4h,1d")
    parser.add_argument("--risk", type=float, default=1.0, help="Risk per trade in percent of balance")
    parser.add_argument("--live", action="store_true", help="Send live orders (default is dry-run)")
    parser.add_argument("--pending", action="store_true", help="Use pending entry at analysis entry price")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    symbols = [part.strip().upper() for part in str(args.symbols).split(",") if part.strip()]
    report = execute_plan(
        symbols=symbols,
        interval=str(args.interval).strip().lower(),
        risk_percent=float(args.risk),
        execute_live=bool(args.live),
        pending_entry=bool(args.pending),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())

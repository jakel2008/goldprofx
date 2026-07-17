import argparse
import json
import math
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from mt5_bridge import MT5Bridge, mt5

PROJECT_ROOT = Path(__file__).resolve().parent


def load_json(path: Path, fallback: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig") or "{}")
    except Exception:
        pass
    return fallback


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ema(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    alpha = 2.0 / (period + 1.0)
    out = float(values[0])
    for value in values[1:]:
        out = (float(value) * alpha) + (out * (1.0 - alpha))
    return out


def normalize_price(bridge: MT5Bridge, symbol: str, price: float) -> float:
    resolved = bridge._resolve_symbol_name(symbol)
    if mt5 is not None and resolved:
        info = mt5.symbol_info(resolved)
        if info is not None:
            digits = int(getattr(info, "digits", 5) or 5)
            return round(float(price), max(0, digits))
    return round(float(price), 5)


def broker_point(bridge: MT5Bridge, symbol: str) -> float:
    resolved = bridge._resolve_symbol_name(symbol)
    if mt5 is not None and resolved:
        info = mt5.symbol_info(resolved)
        if info is not None:
            point = float(getattr(info, "point", 0.0) or 0.0)
            tick_size = float(getattr(info, "trade_tick_size", 0.0) or 0.0)
            if point > 0:
                return point
            if tick_size > 0:
                return tick_size
    return 0.01


def current_tick(bridge: MT5Bridge, symbol: str) -> dict:
    ticks = bridge.get_live_ticks([symbol])
    rows = ticks.get("ticks") or []
    if not rows:
        return {"success": False, "error": ticks.get("errors") or "tick unavailable"}
    row = rows[0]
    bid = float(row.get("bid") or 0.0)
    ask = float(row.get("ask") or 0.0)
    if bid <= 0 or ask <= 0:
        return {"success": False, "error": "invalid bid/ask", "tick": row}
    return {
        "success": True,
        "symbol": row.get("symbol"),
        "requested_symbol": row.get("requested_symbol"),
        "bid": bid,
        "ask": ask,
        "mid": (bid + ask) / 2.0,
        "spread": abs(ask - bid),
    }


def get_bars(bridge: MT5Bridge, symbol: str, timeframe: str, count: int) -> list[dict]:
    result = bridge.get_rates(symbol, timeframe, max(60, int(count or 144)))
    if not result.get("success"):
        raise RuntimeError(str(result.get("error") or "rates unavailable"))
    bars = result.get("bars") or []
    if len(bars) < 30:
        raise RuntimeError(f"not enough bars: {len(bars)}")
    return bars


def determine_direction(bars: list[dict]) -> dict:
    closes = [float(row.get("close") or 0.0) for row in bars if float(row.get("close") or 0.0) > 0]
    if len(closes) < 34:
        return {"side": "buy", "reason": "fallback_not_enough_closes"}

    ema9 = ema(closes[-80:], 9)
    ema34 = ema(closes[-120:], 34)
    last = closes[-1]
    previous = closes[-13] if len(closes) >= 13 else closes[0]
    momentum = last - previous

    if ema9 > ema34 and momentum >= 0:
        side = "buy"
    elif ema9 < ema34 and momentum <= 0:
        side = "sell"
    else:
        side = "buy" if last >= ema34 else "sell"

    return {
        "side": side,
        "reason": "ema9_ema34_momentum",
        "ema9": round(ema9, 5),
        "ema34": round(ema34, 5),
        "last_close": round(last, 5),
        "momentum_12_bars": round(momentum, 5),
    }


def fib_price(level: float, low: float, high: float, direction: str) -> float:
    span = abs(high - low)
    fraction = float(level) / 100.0
    if direction == "buy":
        return low + (span * fraction)
    return high - (span * fraction)


def generate_price_ladder(start_price: float, end_price: float, step: float) -> list[float]:
    if step <= 0:
        raise ValueError("grid_step_price must be positive")
    direction = 1 if end_price >= start_price else -1
    prices = []
    current = float(start_price)
    limit = float(end_price)
    guard = 0
    while guard < 10000:
        if direction > 0 and current > limit:
            break
        if direction < 0 and current < limit:
            break
        prices.append(current)
        current += direction * step
        guard += 1
    if prices and abs(prices[-1] - limit) > step * 0.25:
        prices.append(limit)
    if not prices:
        prices.append(start_price)
    return prices


def opposite_side(side: str) -> str:
    return "sell" if side == "buy" else "buy"


def adjusted_pending_price(raw_price: float, side: str, spread: float, enabled: bool) -> float:
    if not enabled:
        return raw_price
    if side == "buy":
        return raw_price + spread
    return raw_price - spread


def list_grid_orders_and_positions(bridge: MT5Bridge, prefix: str) -> tuple[list[Any], list[Any]]:
    if mt5 is None:
        return [], []
    magic = int(getattr(bridge, "magic", 0) or 0)
    prefix_upper = str(prefix or "").upper()
    orders = []
    positions = []
    for order in list(mt5.orders_get() or []):
        if int(getattr(order, "magic", 0) or 0) == magic and prefix_upper in str(getattr(order, "comment", "") or "").upper():
            orders.append(order)
    for position in list(mt5.positions_get() or []):
        if int(getattr(position, "magic", 0) or 0) == magic and prefix_upper in str(getattr(position, "comment", "") or "").upper():
            positions.append(position)
    return orders, positions


def position_pnl(position: Any) -> float:
    return (
        float(getattr(position, "profit", 0.0) or 0.0)
        + float(getattr(position, "swap", 0.0) or 0.0)
        + float(getattr(position, "commission", 0.0) or 0.0)
    )


def basket_snapshot(positions: list[Any], orders: list[Any], tick: dict) -> dict:
    mid = float(tick.get("mid") or 0.0) if tick else 0.0
    position_rows = []
    total_volume = 0.0
    total_pnl = 0.0
    above_market = 0
    below_market = 0

    for position in positions:
        price_open = float(getattr(position, "price_open", 0.0) or 0.0)
        volume = float(getattr(position, "volume", 0.0) or 0.0)
        pnl = position_pnl(position)
        total_volume += volume
        total_pnl += pnl
        if mid > 0 and price_open > mid:
            above_market += 1
        elif mid > 0 and price_open < mid:
            below_market += 1
        position_rows.append(
            {
                "ticket": int(getattr(position, "ticket", 0) or 0),
                "symbol": str(getattr(position, "symbol", "") or ""),
                "volume": volume,
                "price_open": price_open,
                "pnl": pnl,
                "comment": str(getattr(position, "comment", "") or ""),
            }
        )

    return {
        "positions_count": len(positions),
        "orders_count": len(orders),
        "total_volume": round(total_volume, 4),
        "floating_pnl": round(total_pnl, 2),
        "positions_above_market": above_market,
        "positions_below_market": below_market,
        "mid": round(mid, 5) if mid > 0 else 0.0,
        "positions": position_rows[:50],
    }


def close_grid_cycle(
    bridge: MT5Bridge,
    existing_orders: list[Any],
    existing_positions: list[Any],
    dry_run: bool,
    prefix: str,
    reason: str,
) -> dict:
    actions = []
    for position in existing_positions:
        actions.append(
            {
                "event": "close_position",
                "reason": reason,
                "ticket": int(getattr(position, "ticket", 0) or 0),
                "pnl": round(position_pnl(position), 2),
                "result": close_position(bridge, position, dry_run, f"{prefix}_PROTECT"),
            }
        )
    for order in existing_orders:
        ticket = int(getattr(order, "ticket", 0) or 0)
        if ticket > 0:
            actions.append(
                {
                    "event": "cancel_order",
                    "reason": reason,
                    "ticket": ticket,
                    "result": bridge.cancel_pending_order(ticket, dry_run=dry_run),
                }
            )
    return {"actions": actions, "reason": reason}


def update_basket_profit_protection(config: dict, state: dict, snapshot: dict) -> dict:
    protection = dict((state or {}).get("basket_profit_protection") or {})
    positions_count = int(snapshot.get("positions_count") or 0)
    current_pnl = float(snapshot.get("floating_pnl") or 0.0)

    if positions_count <= 0:
        return {
            "active": False,
            "peak_pnl": 0.0,
            "current_pnl": 0.0,
            "floor_pnl": 0.0,
            "reason": "no_positions",
        }

    activation = max(0.0, float(config.get("basket_profit_activation_usd", 0.0) or 0.0))
    floor = max(0.0, float(config.get("basket_profit_floor_usd", 0.0) or 0.0))
    retrace_pct = max(0.0, min(100.0, float(config.get("basket_profit_max_retrace_percent", 0.0) or 0.0)))

    previous_peak = float(protection.get("peak_pnl", 0.0) or 0.0)
    peak = max(previous_peak, current_pnl)
    active = bool(protection.get("active", False)) or (activation > 0 and peak >= activation)
    dynamic_floor = peak - (peak * retrace_pct / 100.0) if retrace_pct > 0 and peak > 0 else 0.0
    floor_pnl = max(floor, dynamic_floor)

    should_close = bool(active and floor_pnl > 0 and current_pnl <= floor_pnl)
    return {
        "active": active,
        "peak_pnl": round(peak, 2),
        "current_pnl": round(current_pnl, 2),
        "floor_pnl": round(floor_pnl, 2),
        "activation_usd": round(activation, 2),
        "max_retrace_percent": round(retrace_pct, 2),
        "should_close": should_close,
        "reason": "basket_profit_retrace" if should_close else "tracking",
    }


def grid_zone_from_comment(value: Any) -> str:
    comment = str(value or "").upper()
    if "_0-50_" in comment or comment.endswith("_0-50"):
        return "0-50"
    if "_50-75_" in comment or comment.endswith("_50-75"):
        return "50-75"
    return ""


def count_positions_in_zone(positions: list[Any], zone: str) -> int:
    return sum(1 for position in positions if grid_zone_from_comment(getattr(position, "comment", "")) == zone)


def order_zone(order: Any) -> str:
    return grid_zone_from_comment(getattr(order, "comment", ""))


def set_protective_pause(state: dict, config: dict, reason: str) -> dict:
    minutes = max(0.0, float(config.get("protective_pause_minutes", 0.0) or 0.0))
    if minutes <= 0:
        return {}
    until_epoch = time.time() + (minutes * 60.0)
    pause = {
        "active": True,
        "reason": reason,
        "minutes": round(minutes, 2),
        "until_epoch": round(until_epoch, 3),
        "until": datetime.fromtimestamp(until_epoch).isoformat(timespec="seconds"),
    }
    state["protective_pause"] = pause
    return pause


def current_protective_pause(state: dict) -> dict:
    pause = dict((state or {}).get("protective_pause") or {})
    until_epoch = float(pause.get("until_epoch", 0.0) or 0.0)
    if until_epoch <= time.time():
        return {"active": False}
    pause["active"] = True
    pause["remaining_seconds"] = max(0, int(until_epoch - time.time()))
    return pause


def close_position(bridge: MT5Bridge, position: Any, dry_run: bool, comment: str) -> dict:
    if mt5 is None:
        return {"success": False, "error": "MetaTrader5 package is not installed"}
    symbol = str(getattr(position, "symbol", "") or "")
    volume = float(getattr(position, "volume", 0.0) or 0.0)
    ticket = int(getattr(position, "ticket", 0) or 0)
    pos_type = int(getattr(position, "type", 0) or 0)
    tick = mt5.symbol_info_tick(symbol)
    if tick is None or volume <= 0 or ticket <= 0:
        return {"success": False, "error": "invalid position close inputs", "ticket": ticket}
    close_type = mt5.ORDER_TYPE_SELL if pos_type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = float(tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": close_type,
        "position": ticket,
        "price": price,
        "deviation": int(getattr(bridge, "deviation", 20) or 20),
        "magic": int(getattr(bridge, "magic", 0) or 0),
        "comment": str(comment or "BTC_FIB_CLOSE")[:32],
    }
    if dry_run:
        return {"success": True, "dry_run": True, "request": request}

    fill_candidates: list[int | None] = []
    for fill_name in ["ORDER_FILLING_IOC", "ORDER_FILLING_FOK", "ORDER_FILLING_RETURN"]:
        fill_value = getattr(mt5, fill_name, None)
        if fill_value is None or fill_value in fill_candidates:
            continue
        fill_candidates.append(fill_value)
    if not fill_candidates:
        fill_candidates = [None]

    deviation_base = int(getattr(bridge, "deviation", 20) or 20)
    deviation_candidates = [deviation_base, max(deviation_base * 2, 30), max(deviation_base * 3, 50)]
    seen_dev = set()
    compact_deviations = []
    for one in deviation_candidates:
        if one not in seen_dev:
            seen_dev.add(one)
            compact_deviations.append(one)

    retryable_codes = {
        getattr(mt5, "TRADE_RETCODE_REQUOTE", None),
        getattr(mt5, "TRADE_RETCODE_REJECT", None),
        getattr(mt5, "TRADE_RETCODE_PRICE_CHANGED", None),
        getattr(mt5, "TRADE_RETCODE_PRICE_OFF", None),
        getattr(mt5, "TRADE_RETCODE_INVALID_PRICE", None),
        getattr(mt5, "TRADE_RETCODE_INVALID_FILL", None),
        10004,
        10006,
        10015,
        10020,
        10021,
        10030,
    }
    retryable_codes = {int(code) for code in retryable_codes if code is not None}

    attempts = []
    last_result = None
    last_error = None
    for dev in compact_deviations:
        for fill in fill_candidates:
            req = dict(request)
            req["deviation"] = int(dev)
            if fill is not None:
                req["type_filling"] = fill

            latest_tick = mt5.symbol_info_tick(symbol)
            if latest_tick is not None:
                req["price"] = float(latest_tick.bid if close_type == mt5.ORDER_TYPE_SELL else latest_tick.ask)

            result = mt5.order_send(req)
            if result is None:
                last_error = f"position close failed: {mt5.last_error()}"
                attempts.append(
                    {
                        "retcode": None,
                        "error": last_error,
                        "deviation": int(req.get("deviation", deviation_base)),
                        "type_filling": req.get("type_filling"),
                    }
                )
                continue

            last_result = result
            retcode = int(result.retcode)
            attempts.append(
                {
                    "retcode": retcode,
                    "deviation": int(req.get("deviation", deviation_base)),
                    "type_filling": req.get("type_filling"),
                }
            )

            if retcode == mt5.TRADE_RETCODE_DONE:
                return {
                    "success": True,
                    "retcode": retcode,
                    "result": result._asdict(),
                    "request": req,
                    "attempts": attempts,
                }

            if retcode not in retryable_codes:
                return {
                    "success": False,
                    "retcode": retcode,
                    "result": result._asdict(),
                    "request": req,
                    "attempts": attempts,
                }

    if last_result is None:
        return {"success": False, "error": last_error or "position close failed", "request": request, "attempts": attempts}

    return {
        "success": False,
        "retcode": int(last_result.retcode),
        "result": last_result._asdict(),
        "request": request,
        "attempts": attempts,
    }


def target_reached(tick: dict, target: float, trend_side: str) -> bool:
    if not tick.get("success"):
        return False
    if trend_side == "buy":
        return float(tick.get("bid") or 0.0) >= float(target)
    return float(tick.get("ask") or 0.0) <= float(target)


def basket_close_target_from_orders(config: dict, orders: list[dict], fallback_target: float, trend_side: str) -> dict:
    mode = str(config.get("basket_close_mode") or "fib_level").strip().lower()
    if mode not in {"penultimate_reversal_order", "penultimate_reverse_order", "pre_last_reverse_order"}:
        return {
            "mode": "fib_level",
            "target": fallback_target,
            "source": "basket_close_level",
            "order": None,
        }

    reverse_side = opposite_side(trend_side)
    reverse_orders = [
        row for row in orders
        if str(row.get("side") or "") == reverse_side and str(row.get("zone") or "") == "50-75"
    ]
    if len(reverse_orders) >= 2:
        target_order = reverse_orders[-2]
    elif reverse_orders:
        target_order = reverse_orders[-1]
    else:
        return {
            "mode": mode,
            "target": fallback_target,
            "source": "fallback_no_reversal_orders",
            "order": None,
        }

    target = float(target_order.get("pending_price") or target_order.get("raw_price") or fallback_target)
    return {
        "mode": mode,
        "target": target,
        "source": "penultimate_reversal_order" if len(reverse_orders) >= 2 else "last_reversal_order_fallback",
        "order": target_order,
        "reverse_orders_count": len(reverse_orders),
    }


def build_plan(bridge: MT5Bridge, config: dict) -> dict:
    symbol = str(config.get("symbol") or "BTCUSD").upper()
    timeframe = str(config.get("timeframe") or "M5").upper()
    bars = get_bars(bridge, symbol, timeframe, int(config.get("lookback_bars") or 144))
    highs = [float(row.get("high") or 0.0) for row in bars]
    lows = [float(row.get("low") or 0.0) for row in bars]
    high = max(highs)
    low = min(lows)
    if high <= low:
        raise RuntimeError("invalid swing high/low")

    direction = determine_direction(bars)
    trend_side = direction["side"]
    tick = current_tick(bridge, symbol)
    if not tick.get("success"):
        raise RuntimeError(str(tick.get("error") or "tick unavailable"))

    start_level = float(config.get("zone_start_level", 0.0))
    mid_level = float(config.get("zone_mid_level", 50.0))
    end_level = float(config.get("zone_end_level", 75.0))
    point = broker_point(bridge, symbol)
    step_mode = str(config.get("grid_step_mode") or "price").strip().lower()
    if step_mode in {"broker_points", "points", "mt5_points"}:
        step_points = float(config.get("grid_step_points", 50.0) or 50.0)
        step = step_points * point
    else:
        step_points = float(config.get("grid_step_points", 0.0) or 0.0)
        step = float(config.get("grid_step_price", 50.0) or 50.0)
    spread = float(tick.get("spread") or 0.0)
    original_step = float(step)
    spread_points = (spread / point) if point > 0 else 0.0
    liquidity_reasons = []
    max_spread_points = max(0.0, float(config.get("liquidity_max_spread_points", 0.0) or 0.0))
    if max_spread_points > 0 and spread_points > max_spread_points:
        liquidity_reasons.append(
            f"spread_points {round(spread_points, 2)} exceeds max {round(max_spread_points, 2)}"
        )

    min_step_spread_multiplier = max(0.0, float(config.get("min_grid_step_spread_multiplier", 0.0) or 0.0))
    min_step_by_spread = spread * min_step_spread_multiplier if spread > 0 and min_step_spread_multiplier > 0 else 0.0
    if min_step_by_spread > 0 and step < min_step_by_spread:
        if bool(config.get("auto_widen_grid_step_for_spread", True)):
            step = min_step_by_spread
            if point > 0:
                step_points = step / point
        else:
            liquidity_reasons.append(
                f"grid_step {round(step, 5)} below spread-adjusted minimum {round(min_step_by_spread, 5)}"
            )

    liquidity_allowed = not liquidity_reasons
    spread_adjustment = bool(config.get("spread_adjustment", True))
    prefix = str(config.get("comment_prefix") or "BTC_FIB_GRID")

    p0 = fib_price(start_level, low, high, trend_side)
    p50 = fib_price(mid_level, low, high, trend_side)
    p75 = fib_price(end_level, low, high, trend_side)
    close_target = fib_price(float(config.get("basket_close_level", 50.0)), low, high, trend_side)

    zone_a_prices = generate_price_ladder(p0, p50, step)
    zone_b_prices = generate_price_ladder(p50, p75, step)
    max_orders_raw = config.get("max_pending_orders_per_cycle", 0)
    try:
        max_orders = int(max_orders_raw)
    except Exception:
        max_orders = 0
    raw_orders = []

    for raw in zone_a_prices:
        raw_orders.append({"zone": "0-50", "side": trend_side, "raw_price": raw})
    for raw in zone_b_prices:
        raw_orders.append({"zone": "50-75", "side": opposite_side(trend_side), "raw_price": raw})

    if max_orders > 0 and len(raw_orders) > max_orders:
        market_mid = float(tick.get("mid") or 0.0)
        balanced_zone_selection = bool(config.get("balanced_zone_selection", False))
        if balanced_zone_selection:
            zone_a_rows = [row for row in raw_orders if str(row.get("zone") or "") == "0-50"]
            zone_b_rows = [row for row in raw_orders if str(row.get("zone") or "") == "50-75"]

            zone_a_sorted = sorted(zone_a_rows, key=lambda row: abs(float(row["raw_price"]) - market_mid))
            zone_b_sorted = sorted(zone_b_rows, key=lambda row: abs(float(row["raw_price"]) - market_mid))

            half = max_orders // 2
            take_a = min(len(zone_a_sorted), half)
            take_b = min(len(zone_b_sorted), half)

            selected = zone_a_sorted[:take_a] + zone_b_sorted[:take_b]
            remaining_slots = max_orders - len(selected)
            if remaining_slots > 0:
                leftovers = zone_a_sorted[take_a:] + zone_b_sorted[take_b:]
                leftovers = sorted(leftovers, key=lambda row: abs(float(row["raw_price"]) - market_mid))
                selected.extend(leftovers[:remaining_slots])

            raw_orders = sorted(selected[:max_orders], key=lambda row: float(row["raw_price"]))
        else:
            raw_orders = sorted(raw_orders, key=lambda row: abs(float(row["raw_price"]) - market_mid))[:max_orders]
            raw_orders = sorted(raw_orders, key=lambda row: float(row["raw_price"]))

    orders = []
    for idx, item in enumerate(raw_orders, start=1):
        side = item["side"]
        price = adjusted_pending_price(float(item["raw_price"]), side, spread, spread_adjustment)
        price = normalize_price(bridge, symbol, price)
        orders.append({
            "idx": idx,
            "zone": item["zone"],
            "side": side,
            "raw_price": normalize_price(bridge, symbol, item["raw_price"]),
            "pending_price": price,
            "volume": float(config.get("volume") or 0.01),
            "comment": f"{prefix}_{item['zone']}_{idx}",
        })

    close_target_meta = basket_close_target_from_orders(config, orders, close_target, trend_side)
    close_target = float(close_target_meta.get("target") or close_target)

    return {
        "symbol": symbol,
        "broker_symbol": tick.get("symbol"),
        "timeframe": timeframe,
        "trend_side": trend_side,
        "direction": direction,
        "swing_low": normalize_price(bridge, symbol, low),
        "swing_high": normalize_price(bridge, symbol, high),
        "fib": {
            "0": normalize_price(bridge, symbol, p0),
            "50": normalize_price(bridge, symbol, p50),
            "75": normalize_price(bridge, symbol, p75),
            "basket_close": normalize_price(bridge, symbol, close_target),
        },
        "basket_close_target": {
            **close_target_meta,
            "target": normalize_price(bridge, symbol, close_target),
        },
        "tick": tick,
        "broker_point": point,
        "grid_step_mode": step_mode,
        "grid_step_points": round(step_points, 3),
        "grid_step_price": step,
        "original_grid_step_price": original_step,
        "liquidity_guard": {
            "allowed": liquidity_allowed,
            "reasons": liquidity_reasons,
            "spread": round(spread, 5),
            "spread_broker_points": round(spread_points, 3) if point > 0 else None,
            "max_spread_points": max_spread_points,
            "min_grid_step_spread_multiplier": min_step_spread_multiplier,
            "auto_widened_grid_step": step != original_step,
        },
        "spread_broker_points": round(spread / point, 3) if point > 0 else None,
        "spread_adjustment": spread_adjustment,
        "orders_count": len(orders),
        "orders": orders,
        "target_reached": target_reached(tick, close_target, trend_side),
    }


def execute_plan(bridge: MT5Bridge, config: dict, plan: dict, state: dict | None = None) -> dict:
    dry_run = bool(config.get("dry_run", True))
    prefix = str(config.get("comment_prefix") or "BTC_FIB_GRID")
    symbol = str(plan.get("symbol") or config.get("symbol") or "BTCUSD")
    allow_rebuild_same_cycle = bool(config.get("allow_rebuild_pending_with_existing_positions", False))
    actions = []
    state = state if isinstance(state, dict) else {}

    existing_orders, existing_positions = list_grid_orders_and_positions(bridge, prefix)
    snapshot = basket_snapshot(existing_positions, existing_orders, plan.get("tick") or {})
    anchor_guard = {
        "enabled": bool(config.get("reversal_zone_requires_base_anchor", False)),
        "base_zone": str(config.get("base_anchor_zone") or "0-50"),
        "reversal_zone": str(config.get("reversal_zone") or "50-75"),
        "min_base_positions": max(1, int(config.get("min_base_positions_for_reversal_zone", 1) or 1)),
        "base_positions": 0,
        "anchor_ready": True,
        "canceled_unanchored_reversal_orders": 0,
        "filtered_new_reversal_orders": 0,
    }

    max_loss = max(0.0, float(config.get("max_basket_loss_usd", 0.0) or 0.0))
    if max_loss > 0 and int(snapshot.get("positions_count") or 0) > 0 and float(snapshot.get("floating_pnl") or 0.0) <= -max_loss:
        pause = set_protective_pause(state, config, "max_basket_loss")
        result = close_grid_cycle(
            bridge,
            existing_orders=existing_orders,
            existing_positions=existing_positions,
            dry_run=dry_run,
            prefix=prefix,
            reason="max_basket_loss",
        )
        return {
            "dry_run": dry_run,
            "actions": result.get("actions") or [],
            "reason": result.get("reason"),
            "basket_snapshot": snapshot,
            "protective_pause": pause,
            "anchor_guard": anchor_guard,
        }

    if bool(config.get("basket_profit_protection_enabled", False)):
        protection = update_basket_profit_protection(config, state, snapshot)
        state["basket_profit_protection"] = protection
        if protection.get("should_close"):
            pause = set_protective_pause(state, config, "basket_profit_protection")
            result = close_grid_cycle(
                bridge,
                existing_orders=existing_orders,
                existing_positions=existing_positions,
                dry_run=dry_run,
                prefix=prefix,
                reason="basket_profit_protection",
            )
            return {
                "dry_run": dry_run,
                "actions": result.get("actions") or [],
                "reason": result.get("reason"),
                "basket_snapshot": snapshot,
                "basket_profit_protection": protection,
                "protective_pause": pause,
                "anchor_guard": anchor_guard,
            }

    if plan.get("target_reached") and (existing_orders or existing_positions):
        result = close_grid_cycle(
            bridge,
            existing_orders=existing_orders,
            existing_positions=existing_positions,
            dry_run=dry_run,
            prefix=prefix,
            reason="basket_target_reached",
        )
        return {
            "dry_run": dry_run,
            "actions": result.get("actions") or [],
            "reason": result.get("reason"),
            "basket_snapshot": snapshot,
            "basket_profit_protection": state.get("basket_profit_protection"),
            "anchor_guard": anchor_guard,
        }

    # If the basket target is already reached and there is no active grid,
    # avoid creating a fresh cycle that would be canceled again on the next tick.
    if plan.get("target_reached") and not existing_orders and not existing_positions:
        return {"dry_run": dry_run, "actions": actions, "reason": "target_reached_wait"}

    pause = current_protective_pause(state)
    if pause.get("active") and not existing_orders and not existing_positions:
        return {
            "dry_run": dry_run,
            "actions": actions,
            "reason": "protective_pause_wait",
            "protective_pause": pause,
            "basket_snapshot": snapshot,
            "basket_profit_protection": state.get("basket_profit_protection"),
            "anchor_guard": anchor_guard,
        }

    if anchor_guard["enabled"]:
        anchor_guard["base_positions"] = count_positions_in_zone(existing_positions, anchor_guard["base_zone"])
        anchor_guard["anchor_ready"] = anchor_guard["base_positions"] >= anchor_guard["min_base_positions"]
        if not anchor_guard["anchor_ready"] and bool(config.get("cancel_unanchored_reversal_pending_orders", True)):
            kept_orders = []
            for order in existing_orders:
                if order_zone(order) == anchor_guard["reversal_zone"]:
                    ticket = int(getattr(order, "ticket", 0) or 0)
                    if ticket > 0:
                        actions.append(
                            {
                                "event": "cancel_order",
                                "reason": "unanchored_reversal_zone",
                                "ticket": ticket,
                                "result": bridge.cancel_pending_order(ticket, dry_run=dry_run),
                            }
                        )
                        anchor_guard["canceled_unanchored_reversal_orders"] += 1
                    continue
                kept_orders.append(order)
            existing_orders = kept_orders

    liquidity_guard = plan.get("liquidity_guard") or {}
    if not bool(liquidity_guard.get("allowed", True)) and not existing_orders and not existing_positions:
        return {
            "dry_run": dry_run,
            "actions": actions,
            "reason": "liquidity_guard_wait",
            "liquidity_guard": liquidity_guard,
            "basket_snapshot": snapshot,
            "basket_profit_protection": state.get("basket_profit_protection"),
            "anchor_guard": anchor_guard,
        }

    if existing_orders or existing_positions:
        if not allow_rebuild_same_cycle:
            return {
                "dry_run": dry_run,
                "actions": actions,
                "reason": "existing_grid_cycle_active",
                "existing_orders": len(existing_orders),
                "existing_positions": len(existing_positions),
                "basket_snapshot": snapshot,
                "basket_profit_protection": state.get("basket_profit_protection"),
                "anchor_guard": anchor_guard,
            }
        if bool(config.get("cancel_existing_grid_orders_before_new_cycle", True)):
            for order in existing_orders:
                ticket = int(getattr(order, "ticket", 0) or 0)
                if ticket > 0:
                    actions.append({"event": "cancel_order", "ticket": ticket, "result": bridge.cancel_pending_order(ticket, dry_run=dry_run)})
            existing_orders = []

    if bool(config.get("cancel_existing_grid_orders_before_new_cycle", True)):
        for order in existing_orders:
            ticket = int(getattr(order, "ticket", 0) or 0)
            if ticket > 0:
                actions.append({"event": "cancel_order", "ticket": ticket, "result": bridge.cancel_pending_order(ticket, dry_run=dry_run)})

    orders_to_place = list(plan.get("orders") or [])
    if anchor_guard["enabled"] and not anchor_guard["anchor_ready"]:
        before_count = len(orders_to_place)
        orders_to_place = [item for item in orders_to_place if str(item.get("zone") or "") != anchor_guard["reversal_zone"]]
        anchor_guard["filtered_new_reversal_orders"] = before_count - len(orders_to_place)

    for item in orders_to_place:
        result = bridge.send_order(
            symbol=symbol,
            side=item["side"],
            volume=float(item.get("volume") or 0.01),
            sl=None,
            tp=None,
            comment=item["comment"],
            dry_run=dry_run,
            pending=True,
            entry_price=float(item["pending_price"]),
        )
        actions.append({"event": "place_pending", "order": item, "result": result})

    return {
        "dry_run": dry_run,
        "actions": actions,
        "reason": "new_grid_cycle",
        "basket_snapshot": snapshot,
        "basket_profit_protection": state.get("basket_profit_protection"),
        "anchor_guard": anchor_guard,
    }


def run_once(config_path: Path) -> int:
    config = load_json(config_path, {})
    if not config.get("enabled", True):
        print(json.dumps({"event": "disabled", "config": str(config_path)}, ensure_ascii=False))
        return 0

    bridge = MT5Bridge()
    conn = bridge.connect()
    if not conn.get("success"):
        print(json.dumps({"success": False, "error": conn.get("error"), "status": conn.get("status")}, ensure_ascii=False))
        return 1

    state_path = PROJECT_ROOT / str(config.get("cycle_state_file") or "accounts/account3/btc_fibonacci_grid_state.json")
    previous_state = load_json(state_path, {})
    plan = build_plan(bridge, config)
    execution = execute_plan(bridge, config, plan, previous_state)
    state = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "dry_run": bool(config.get("dry_run", True)),
        "plan": {k: v for k, v in plan.items() if k != "orders"},
        "orders_preview": plan.get("orders", [])[:120],
        "execution_reason": execution.get("reason"),
        "actions_count": len(execution.get("actions") or []),
        "basket_snapshot": execution.get("basket_snapshot"),
        "basket_profit_protection": execution.get("basket_profit_protection") or previous_state.get("basket_profit_protection"),
        "protective_pause": execution.get("protective_pause") or previous_state.get("protective_pause"),
        "anchor_guard": execution.get("anchor_guard"),
    }
    save_json(state_path, state)
    output_plan = dict(plan)
    output_plan["orders_preview"] = output_plan.pop("orders", [])[:120]
    output_execution = dict(execution)
    actions = list(output_execution.pop("actions", []) or [])
    output_execution["actions_count"] = len(actions)
    output_execution["actions_preview"] = actions[:40]
    print(json.dumps({"success": True, "state_path": str(state_path), "plan": output_plan, "execution": output_execution}, ensure_ascii=False, indent=2, default=str))
    return 0


def run_loop(config_path: Path, interval_minutes: float) -> int:
    interval_seconds = max(5.0, float(interval_minutes) * 60.0)
    print(
        json.dumps(
            {
                "event": "loop_started",
                "config": str(config_path),
                "interval_minutes": round(interval_seconds / 60.0, 4),
            },
            ensure_ascii=False,
        )
    )
    while True:
        code = run_once(config_path)
        if code != 0:
            print(json.dumps({"event": "loop_cycle_error", "code": code}, ensure_ascii=False))
        time.sleep(interval_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="BTC Fibonacci grid strategy runner")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "accounts/account3/strategy_btc_fibonacci_grid_v1.json"))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-minutes", type=float, default=None)
    args = parser.parse_args()
    config_path = Path(args.config)

    if args.once:
        return run_once(config_path)

    if args.loop:
        config = load_json(config_path, {})
        configured_interval = config.get("review_levels_every_minutes", 1)
        interval = float(args.interval_minutes if args.interval_minutes is not None else configured_interval)
        return run_loop(config_path, interval)

    print(json.dumps({"error": "Use --once or --loop"}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

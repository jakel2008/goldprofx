from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from services.advanced_analyzer_engine import (
    SUPPORTED_INTERVALS,
    SUPPORTED_SYMBOLS,
    _download_market_data,
    _normalize_symbol,
    _round_price,
)


ALL_INTERVALS = ["5m", "15m", "30m", "1h", "4h", "1d"]
HORIZON_BY_INTERVAL = {
    "5m": "scalping",
    "15m": "scalping",
    "30m": "swing",
    "1h": "swing",
    "4h": "swing",
    "1d": "long_term",
}

SESSION_WINDOWS_UTC = {
    "sydney": (21, 6),
    "asia": (0, 9),
    "london": (7, 16),
    "new_york": (12, 21),
}

NEWS_IMPACT_WEIGHT = {
    "low": 0.5,
    "medium": 1.0,
    "high": 1.8,
}

ECONOMIC_CALENDAR_SOURCES = [
    "https://www.arabictrader.com/ar/economic-calendar",
    "https://www.forexfactory.com/",
]

ECONOMIC_NEWS_CACHE_FILE = Path(__file__).resolve().parents[2] / "economic_news_cache.json"

_CURRENCY_RE = re.compile(r"\b(?:USD|EUR|GBP|JPY|AUD|NZD|CAD|CHF|CNY|XAU|XAG)\b", re.IGNORECASE)

_HIGH_IMPACT_KEYWORDS = {
    "nfp",
    "nonfarm",
    "cpi",
    "inflation",
    "interest rate",
    "rate decision",
    "fomc",
    "fed",
    "ecb",
    "boe",
    "boj",
    "rba",
    "rbnz",
    "بطالة",
    "التضخم",
    "الفائدة",
    "الفيدرالي",
    "مؤشر مديري المشتريات",
    "ism",
    "gdp",
    "الناتج المحلي",
}

_MEDIUM_IMPACT_KEYWORDS = {
    "pmi",
    "jobs",
    "payroll",
    "retail sales",
    "مبيعات التجزئة",
    "إعانات البطالة",
    "claims",
}


@dataclass
class NewsContext:
    minutes_to_event: int | None = None
    impact: str = "low"
    surprise_ratio: float = 0.0


@dataclass
class ScorePart:
    name: str
    score: float
    reason: str


def _normalize_impact(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if text in {"high", "عالية", "high impact"}:
        return "high"
    if text in {"medium", "متوسطة", "medium impact"}:
        return "medium"
    return "low"


def _impact_rank(value: str) -> int:
    impact = _normalize_impact(value)
    if impact == "high":
        return 3
    if impact == "medium":
        return 2
    return 1


def _detect_impact_from_text(text: str) -> str:
    low = str(text or "").lower()
    if any(word in low for word in _HIGH_IMPACT_KEYWORDS):
        return "high"
    if any(word in low for word in _MEDIUM_IMPACT_KEYWORDS):
        return "medium"
    if "عالية" in low:
        return "high"
    if "متوسطة" in low:
        return "medium"
    return "low"


def _extract_currencies(text: str) -> set[str]:
    return {m.group(0).upper() for m in _CURRENCY_RE.finditer(str(text or ""))}


def _symbol_currencies(symbol: str) -> set[str]:
    upper = str(symbol or "").upper()
    known = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY", "XAU", "XAG"}
    found = {m.group(0).upper() for m in _CURRENCY_RE.finditer(upper)}
    found = {item for item in found if item in known}
    if not found and upper in {"US30", "NAS100", "SPX500", "CRUDE", "BRENT", "NATGAS", "BTCUSD", "ETHUSD"}:
        found.add("USD")
    return found


def _parse_dt_to_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _resolve_news_from_calendar_events(symbol: str, events: list[dict[str, Any]]) -> tuple[NewsContext | None, dict[str, Any]]:
    symbol_ccy = _symbol_currencies(symbol)
    now = datetime.now(timezone.utc)
    best: dict[str, Any] | None = None

    for event in events:
        if not isinstance(event, dict):
            continue

        event_ccy = set()
        for key in ("currency", "currencies", "country", "ccy"):
            value = event.get(key)
            if isinstance(value, str):
                event_ccy |= _extract_currencies(value)
            elif isinstance(value, list):
                event_ccy |= {str(v).upper() for v in value if str(v).strip()}

        title = str(event.get("title") or event.get("name") or "")
        event_ccy |= _extract_currencies(title)

        if symbol_ccy and event_ccy and symbol_ccy.isdisjoint(event_ccy):
            continue

        minutes_to_event = event.get("minutes_to_event")
        if minutes_to_event is None:
            event_time = _parse_dt_to_utc(event.get("time_utc") or event.get("datetime") or event.get("event_time"))
            if event_time is not None:
                minutes_to_event = int((event_time - now).total_seconds() // 60)

        if minutes_to_event is None:
            continue

        impact = _normalize_impact(event.get("impact") or _detect_impact_from_text(title))
        score = (_impact_rank(impact) * 1000) - abs(int(minutes_to_event))
        if best is None or score > int(best.get("_score", -10**9)):
            best = {
                "impact": impact,
                "minutes_to_event": int(minutes_to_event),
                "surprise_ratio": float(event.get("surprise_ratio", 0.0) or 0.0),
                "title": title,
                "currencies": sorted(event_ccy),
                "time_utc": event.get("time_utc"),
                "actual": event.get("actual"),
                "forecast": event.get("forecast"),
                "previous": event.get("previous"),
                "revision": event.get("revision"),
                "_score": score,
            }

    if best is None:
        return None, {"calendar_mode": "events", "matched": 0}

    return (
        NewsContext(
            minutes_to_event=int(best["minutes_to_event"]),
            impact=str(best["impact"]),
            surprise_ratio=float(best["surprise_ratio"]),
        ),
        {
            "calendar_mode": "events",
            "matched": 1,
            "event_title": best.get("title"),
            "event_currencies": best.get("currencies") or [],
            "event_time_utc": best.get("time_utc"),
            "actual": best.get("actual"),
            "forecast": best.get("forecast"),
            "previous": best.get("previous"),
            "revision": best.get("revision"),
        },
    )


def _resolve_news_from_cache(symbol: str) -> tuple[NewsContext | None, dict[str, Any]]:
    if not ECONOMIC_NEWS_CACHE_FILE.exists():
        return None, {"calendar_mode": "cache", "available": False}

    try:
        payload = json.loads(ECONOMIC_NEWS_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, {"calendar_mode": "cache", "available": True, "error": str(exc)}

    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list) or not items:
        return None, {"calendar_mode": "cache", "available": True, "items": 0}

    updated_at = _parse_dt_to_utc(payload.get("updated_at") if isinstance(payload, dict) else None)
    age_minutes = None
    cache_clock_skew = False
    if updated_at is not None:
        age_minutes = int((datetime.now(timezone.utc) - updated_at).total_seconds() // 60)
        if age_minutes < 0:
            # Some feeds write local time without timezone; treat negative age as clock skew.
            cache_clock_skew = True
            age_minutes = abs(age_minutes)

    symbol_ccy = _symbol_currencies(symbol)
    relevant_rows: list[dict[str, Any]] = []
    strongest_impact = "low"

    for row in items:
        text = str(row or "").strip()
        if not text:
            continue
        row_ccy = _extract_currencies(text)
        if symbol_ccy and row_ccy and symbol_ccy.isdisjoint(row_ccy):
            continue
        impact = _detect_impact_from_text(text)
        if _impact_rank(impact) > _impact_rank(strongest_impact):
            strongest_impact = impact
        relevant_rows.append({"impact": impact, "currencies": sorted(row_ccy), "title": text})

    if not relevant_rows:
        return None, {"calendar_mode": "cache", "available": True, "items": len(items), "matched": 0}

    # Headlines are post-publication; treat as recent post-event context.
    minutes_to_event = -max(0, age_minutes or 0)
    context = NewsContext(minutes_to_event=minutes_to_event, impact=strongest_impact, surprise_ratio=0.0)

    return context, {
        "calendar_mode": "cache",
        "available": True,
        "items": len(items),
        "matched": len(relevant_rows),
        "matched_impacts": {
            "high": sum(1 for item in relevant_rows if item["impact"] == "high"),
            "medium": sum(1 for item in relevant_rows if item["impact"] == "medium"),
            "low": sum(1 for item in relevant_rows if item["impact"] == "low"),
        },
        "cache_age_minutes": age_minutes,
        "cache_clock_skew": cache_clock_skew,
    }


def _resolve_news_context(symbol: str, news_context: dict[str, Any] | None) -> tuple[NewsContext | None, dict[str, Any]]:
    if news_context:
        if isinstance(news_context.get("calendar_events"), list):
            resolved, details = _resolve_news_from_calendar_events(symbol, news_context.get("calendar_events") or [])
            if resolved is not None:
                details["source"] = str(news_context.get("calendar_source") or ECONOMIC_CALENDAR_SOURCES[0])
                return resolved, details

        if any(key in news_context for key in ("minutes_to_event", "impact", "surprise_ratio")):
            return (
                NewsContext(
                    minutes_to_event=news_context.get("minutes_to_event"),
                    impact=_normalize_impact(str(news_context.get("impact", "low"))),
                    surprise_ratio=float(news_context.get("surprise_ratio", 0.0) or 0.0),
                ),
                {
                    "calendar_mode": "manual",
                    "source": str(news_context.get("calendar_source") or "manual"),
                },
            )

    resolved, details = _resolve_news_from_cache(symbol)
    details["source"] = ECONOMIC_CALENDAR_SOURCES
    return resolved, details


def _ensure_datetime_index(data: pd.DataFrame) -> pd.DataFrame:
    if data.index.inferred_type in ("datetime64", "datetime"):
        result = data.copy()
    else:
        result = data.copy()
        result.index = pd.to_datetime(result.index, utc=True, errors="coerce")
        result = result[~result.index.isna()]
    if result.index.tz is None:
        result.index = result.index.tz_localize(timezone.utc)
    else:
        result.index = result.index.tz_convert(timezone.utc)
    return result.sort_index()


def _session_bounds(reference: datetime, start_hour: int, end_hour: int) -> tuple[datetime, datetime]:
    start = reference.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end = reference.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    if end_hour <= start_hour:
        if reference.hour < end_hour:
            start -= timedelta(days=1)
        else:
            end += timedelta(days=1)
    return start, end


def _session_high_low(data: pd.DataFrame, start_hour: int, end_hour: int) -> tuple[float | None, float | None]:
    if data.empty:
        return None, None
    reference = data.index.max().to_pydatetime()
    start, end = _session_bounds(reference, start_hour, end_hour)
    window = data[(data.index >= start) & (data.index < end)]
    if window.empty:
        return None, None
    return float(window["High"].max()), float(window["Low"].min())


def _daily_high_low(data: pd.DataFrame) -> tuple[float | None, float | None]:
    if data.empty:
        return None, None
    reference_day = data.index.max().date()
    day_slice = data[data.index.date == reference_day]
    if day_slice.empty:
        return None, None
    return float(day_slice["High"].max()), float(day_slice["Low"].min())


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi_values = 100 - (100 / (1 + rs))
    return rsi_values.fillna(50)


def _candle_score(data: pd.DataFrame) -> tuple[float, list[dict[str, Any]]]:
    if len(data) < 6:
        return 0.0, []

    weights = [0.50, 0.25, 0.15, 0.07, 0.03]
    candles = data.tail(5)
    details = []
    total_score = 0.0

    for idx, (_, row) in enumerate(candles.iterrows()):
        open_price = float(row["Open"])
        close_price = float(row["Close"])
        high_price = float(row["High"])
        low_price = float(row["Low"])
        body = abs(close_price - open_price)
        span = max(high_price - low_price, 1e-9)
        upper_wick = high_price - max(open_price, close_price)
        lower_wick = min(open_price, close_price) - low_price

        direction = 1.0 if close_price >= open_price else -1.0
        body_ratio = body / span
        rejection = (lower_wick - upper_wick) / span
        close_location = ((close_price - low_price) / span) * 2 - 1

        candle_raw = (direction * 45.0) + (body_ratio * direction * 25.0) + (rejection * 15.0) + (close_location * 15.0)
        weighted = candle_raw * weights[idx]
        total_score += weighted

        details.append(
            {
                "index_weight": weights[idx],
                "direction": "bullish" if direction > 0 else "bearish",
                "body_ratio": round(body_ratio, 4),
                "rejection": round(rejection, 4),
                "close_location": round(close_location, 4),
                "weighted_score": round(weighted, 3),
            }
        )

    return max(-30.0, min(30.0, total_score)), details


def _indicator_scores(data: pd.DataFrame) -> tuple[float, list[dict[str, Any]]]:
    close = data["Close"].astype(float)
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    rsi_value = float(_rsi(close).iloc[-1])
    momentum = float((close.iloc[-1] / close.iloc[-6] - 1) * 100) if len(close) > 6 else 0.0

    parts = []
    total = 0.0

    if close.iloc[-1] > ema20.iloc[-1] > ema50.iloc[-1]:
        score = 14.0
        reason = "Price above EMA20 and EMA50"
    elif close.iloc[-1] < ema20.iloc[-1] < ema50.iloc[-1]:
        score = -14.0
        reason = "Price below EMA20 and EMA50"
    else:
        score = 0.0
        reason = "EMA structure mixed"
    parts.append({"name": "ema_structure", "score": score, "reason": reason})
    total += score

    macd_gap = float(macd.iloc[-1] - macd_signal.iloc[-1])
    macd_score = max(-10.0, min(10.0, macd_gap * 8000.0))
    parts.append({"name": "macd_gap", "score": round(macd_score, 3), "reason": f"MACD gap {macd_gap:.6f}"})
    total += macd_score

    if rsi_value > 58:
        rsi_score = min(10.0, (rsi_value - 50.0) * 0.6)
    elif rsi_value < 42:
        rsi_score = max(-10.0, -(50.0 - rsi_value) * 0.6)
    else:
        rsi_score = 0.0
    parts.append({"name": "rsi_bias", "score": round(rsi_score, 3), "reason": f"RSI {rsi_value:.2f}"})
    total += rsi_score

    momentum_score = max(-8.0, min(8.0, momentum * 2.2))
    parts.append({"name": "momentum_5bars", "score": round(momentum_score, 3), "reason": f"Momentum {momentum:.3f}%"})
    total += momentum_score

    return max(-40.0, min(40.0, total)), parts


def _channel_breakout_scores(data: pd.DataFrame) -> tuple[float, float, dict[str, Any]]:
    lookback = min(30, len(data))
    if lookback < 10:
        return 0.0, 0.0, {}

    sample = data.tail(lookback)
    high = float(sample["High"].max())
    low = float(sample["Low"].min())
    close_price = float(sample["Close"].iloc[-1])
    span = max(high - low, 1e-9)
    position = (close_price - low) / span

    channel_score = (position - 0.5) * 30.0

    breakout_score = 0.0
    breakout_reason = "inside_channel"
    if close_price > high * 0.9996:
        breakout_score = min(20.0, ((close_price - high) / span) * 350.0 + 8.0)
        breakout_reason = "upside_breakout"
    elif close_price < low * 1.0004:
        breakout_score = max(-20.0, -(((low - close_price) / span) * 350.0 + 8.0))
        breakout_reason = "downside_breakout"

    return channel_score, breakout_score, {
        "channel_high": high,
        "channel_low": low,
        "channel_position": round(position, 4),
        "breakout_reason": breakout_reason,
    }


def _fibonacci_score(data: pd.DataFrame, trend_sign: int) -> tuple[float, dict[str, Any]]:
    lookback = min(80, len(data))
    if lookback < 20:
        return 0.0, {}

    sample = data.tail(lookback)
    swing_high = float(sample["High"].max())
    swing_low = float(sample["Low"].min())
    close_price = float(sample["Close"].iloc[-1])
    span = max(swing_high - swing_low, 1e-9)

    if trend_sign >= 0:
        level_382 = swing_high - span * 0.382
        level_500 = swing_high - span * 0.5
        level_618 = swing_high - span * 0.618
        distances = [abs(close_price - level_382), abs(close_price - level_500), abs(close_price - level_618)]
        nearest = min(distances)
        score = max(0.0, 14.0 - (nearest / span) * 80.0)
        return score, {
            "trend": "bullish",
            "swing_high": swing_high,
            "swing_low": swing_low,
            "fib_levels": {
                "0.382": level_382,
                "0.5": level_500,
                "0.618": level_618,
            },
            "nearest_distance_pct": round((nearest / span) * 100.0, 3),
        }

    level_382 = swing_low + span * 0.382
    level_500 = swing_low + span * 0.5
    level_618 = swing_low + span * 0.618
    distances = [abs(close_price - level_382), abs(close_price - level_500), abs(close_price - level_618)]
    nearest = min(distances)
    score = -max(0.0, 14.0 - (nearest / span) * 80.0)
    return score, {
        "trend": "bearish",
        "swing_high": swing_high,
        "swing_low": swing_low,
        "fib_levels": {
            "0.382": level_382,
            "0.5": level_500,
            "0.618": level_618,
        },
        "nearest_distance_pct": round((nearest / span) * 100.0, 3),
    }


def _session_relation_score(data: pd.DataFrame) -> tuple[float, dict[str, Any]]:
    daily_high, daily_low = _daily_high_low(data)
    sessions: dict[str, dict[str, float | None]] = {}

    for session_name, (start_hour, end_hour) in SESSION_WINDOWS_UTC.items():
        high, low = _session_high_low(data, start_hour, end_hour)
        sessions[session_name] = {"high": high, "low": low}

    close_price = float(data["Close"].iloc[-1])
    score = 0.0

    london_high = sessions.get("london", {}).get("high")
    london_low = sessions.get("london", {}).get("low")
    ny_high = sessions.get("new_york", {}).get("high")
    ny_low = sessions.get("new_york", {}).get("low")

    if london_high and close_price > london_high:
        score += 8.0
    if london_low and close_price < london_low:
        score -= 8.0
    if ny_high and close_price > ny_high:
        score += 10.0
    if ny_low and close_price < ny_low:
        score -= 10.0

    if daily_high and daily_low:
        day_span = max(daily_high - daily_low, 1e-9)
        day_position = (close_price - daily_low) / day_span
        score += (day_position - 0.5) * 8.0

    return max(-24.0, min(24.0, score)), {
        "daily_high": daily_high,
        "daily_low": daily_low,
        "sessions": sessions,
    }


def _news_adjustment(symbol: str, news: NewsContext | None) -> tuple[float, bool, dict[str, Any]]:
    if news is None:
        return 0.0, False, {"news_mode": "none"}

    impact = NEWS_IMPACT_WEIGHT.get(str(news.impact or "low").lower(), 1.0)
    is_crypto = symbol in {"BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "BNBUSD"}
    pair_factor = 1.3 if symbol in {"XAUUSD", "US30", "NAS100"} else (1.15 if is_crypto else 1.0)

    dynamic_pre_lock = int(round(18 * impact * pair_factor))
    dynamic_post_lock = int(round(24 * impact * pair_factor))

    blocked = False
    if news.minutes_to_event is not None and 0 <= news.minutes_to_event <= dynamic_pre_lock:
        blocked = True

    surprise = float(news.surprise_ratio or 0.0)
    surprise_score = max(-16.0, min(16.0, surprise * 18.0 * impact))

    if news.minutes_to_event is not None and -dynamic_post_lock <= news.minutes_to_event < 0:
        surprise_score *= 0.7
        # Keep protective block active shortly after medium/high-impact events.
        if impact >= NEWS_IMPACT_WEIGHT["medium"]:
            blocked = True

    return surprise_score, blocked, {
        "news_mode": "dynamic",
        "impact": str(news.impact or "low").lower(),
        "minutes_to_event": news.minutes_to_event,
        "dynamic_pre_lock_minutes": dynamic_pre_lock,
        "dynamic_post_lock_minutes": dynamic_post_lock,
        "surprise_ratio": surprise,
    }


def _dynamic_weights(volatility_pct: float) -> dict[str, float]:
    base = {
        "indicators": 0.30,
        "candles": 0.20,
        "channel": 0.16,
        "breakout": 0.14,
        "fibonacci": 0.12,
        "sessions": 0.08,
    }

    if volatility_pct >= 3.5:
        base["breakout"] += 0.05
        base["candles"] -= 0.04
        base["fibonacci"] -= 0.01
    elif volatility_pct <= 1.2:
        base["fibonacci"] += 0.04
        base["sessions"] += 0.02
        base["breakout"] -= 0.03
        base["indicators"] -= 0.03

    total = sum(base.values())
    return {name: value / total for name, value in base.items()}


def _evaluate_single_interval(symbol: str, interval: str, news: NewsContext | None) -> dict[str, Any]:
    market_data = _download_market_data(symbol, interval)
    market_data = _ensure_datetime_index(market_data)

    if market_data.empty or len(market_data) < 70:
        return {
            "success": False,
            "interval": interval,
            "error": "Not enough market data for interval scoring.",
        }

    close = market_data["Close"].astype(float)
    volatility_pct = float(close.pct_change().tail(20).std() * 100.0)

    indicator_score, indicator_parts = _indicator_scores(market_data)
    candle_score, candle_details = _candle_score(market_data)
    channel_score, breakout_score, channel_info = _channel_breakout_scores(market_data)
    trend_sign = 1 if indicator_score >= 0 else -1
    fib_score, fib_info = _fibonacci_score(market_data, trend_sign)
    session_score, session_info = _session_relation_score(market_data)

    weights = _dynamic_weights(volatility_pct)

    raw_score = (
        indicator_score * weights["indicators"]
        + candle_score * weights["candles"]
        + channel_score * weights["channel"]
        + breakout_score * weights["breakout"]
        + fib_score * weights["fibonacci"]
        + session_score * weights["sessions"]
    )

    news_score, news_blocked, news_info = _news_adjustment(symbol, news)
    total_score = raw_score + news_score
    total_score = max(-100.0, min(100.0, total_score))

    if total_score >= 22.0:
        recommendation = "buy"
    elif total_score <= -22.0:
        recommendation = "sell"
    else:
        recommendation = "wait"

    close_price = float(close.iloc[-1])
    return {
        "success": True,
        "symbol": symbol,
        "interval": interval,
        "horizon": HORIZON_BY_INTERVAL.get(interval, "swing"),
        "close_price": _round_price(close_price, symbol),
        "volatility_pct": round(volatility_pct, 4),
        "weights": {k: round(v, 4) for k, v in weights.items()},
        "scores": {
            "indicators": round(indicator_score, 3),
            "candles": round(candle_score, 3),
            "channel": round(channel_score, 3),
            "breakout": round(breakout_score, 3),
            "fibonacci": round(fib_score, 3),
            "sessions": round(session_score, 3),
            "news": round(news_score, 3),
            "raw": round(raw_score, 3),
            "total": round(total_score, 3),
        },
        "recommendation": recommendation,
        "news_blocked": news_blocked,
        "indicator_parts": indicator_parts,
        "candle_details": candle_details,
        "channel_info": channel_info,
        "session_info": session_info,
        "fibonacci_info": fib_info,
        "news_info": news_info,
    }


def evaluate_experimental_decision(
    symbol: str,
    preferred_interval: str = "1h",
    news_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_symbol = _normalize_symbol(symbol)
    normalized_interval = (preferred_interval or "1h").strip().lower()

    if normalized_symbol not in SUPPORTED_SYMBOLS:
        return {
            "success": False,
            "error": f"Unsupported symbol '{symbol}'.",
            "supported_symbols": sorted(SUPPORTED_SYMBOLS.keys()),
        }

    if normalized_interval not in SUPPORTED_INTERVALS:
        normalized_interval = "1h"

    news, news_context_info = _resolve_news_context(normalized_symbol, news_context)

    interval_results = []
    for interval in ALL_INTERVALS:
        if interval not in SUPPORTED_INTERVALS:
            continue
        result = _evaluate_single_interval(normalized_symbol, interval, news)
        interval_results.append(result)

    successful = [item for item in interval_results if item.get("success")]
    if not successful:
        return {
            "success": False,
            "symbol": normalized_symbol,
            "error": "Unable to score any timeframe.",
            "interval_results": interval_results,
        }

    best = max(successful, key=lambda item: abs(float(item["scores"]["total"])) + (0.75 if item["interval"] == normalized_interval else 0.0))

    return {
        "success": True,
        "mode": "experimental_shadow",
        "symbol": normalized_symbol,
        "symbol_label": SUPPORTED_SYMBOLS[normalized_symbol]["label"],
        "chosen_interval": best["interval"],
        "chosen_horizon": best["horizon"],
        "preferred_interval": normalized_interval,
        "recommendation": best["recommendation"],
        "news_blocked": bool(best.get("news_blocked")),
        "news_context_info": news_context_info,
        "calendar_sources": ECONOMIC_CALENDAR_SOURCES,
        "final_score": best["scores"]["total"],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "chosen_details": best,
        "interval_results": successful,
    }

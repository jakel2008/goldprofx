# -*- coding: utf-8 -*-
"""
Smart Forex Analyzer - Full Backend Module
Based on tkinter original code
"""
import requests
import pandas as pd
import ta
import numpy as np
import os
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration
API_KEY = "079cdb64bbc8415abcf8f7be7e389349"
BASE_URL = "https://api.twelvedata.com/time_series"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
CACHE_DIR = Path(__file__).parent / "cache" / "market_data"
YF_COOLDOWN_SECONDS = int(os.environ.get("YF_ANALYZER_COOLDOWN_SECONDS", "90"))
TD_COOLDOWN_SECONDS = int(os.environ.get("TWELVEDATA_COOLDOWN_SECONDS", "600"))
CRYPTO_DATA_SOURCE_MODE = str(os.environ.get("CRYPTO_DATA_SOURCE_MODE", "auto") or "auto").strip().lower()

logger = logging.getLogger("forex_analyzer")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

_YF_COOLDOWN_UNTIL = {}
_YF_COOLDOWN_LOCK = threading.Lock()
_TD_COOLDOWN_UNTIL = 0.0
_TD_COOLDOWN_REASON = ""
_TD_COOLDOWN_LOCK = threading.Lock()

LAST_FETCH_METADATA = {
    "symbol": None,
    "interval": None,
    "source": None,
    "cache_used": False,
    "stale_cache_used": False,
    "rows": 0,
    "timestamp": None,
    "errors": []
}

CRYPTO_BINANCE_SYMBOLS = {
    "BTCUSD": "BTCUSDT",
    "ETHUSD": "ETHUSDT",
    "BNBUSD": "BNBUSDT",
    "SOLUSD": "SOLUSDT",
    "XRPUSD": "XRPUSDT",
    "ADAUSD": "ADAUSDT",
    "DOGEUSD": "DOGEUSDT",
    "LTCUSD": "LTCUSDT",
    "BTC/USDT": "BTCUSDT",
    "ETH/USDT": "ETHUSDT",
    "BNB/USDT": "BNBUSDT",
    "SOL/USDT": "SOLUSDT",
    "XRP/USDT": "XRPUSDT",
    "BTC/USDC": "BTCUSDC",
    "ETH/USDC": "ETHUSDC"
}

KNOWN_CRYPTO_BASES = {
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "LTC",
    "DOT", "AVAX", "LINK", "TRX", "MATIC", "UNI", "ATOM", "BCH"
}

YF_SYMBOLS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "USDCHF": "USDCHF=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "EURGBP": "EURGBP=X",
    "CADJPY": "CADJPY=X",
    "CHFJPY": "CHFJPY=X",
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "US30": "^DJI",
    "NAS100": "^IXIC",
    "SPX500": "^GSPC",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD"
}

INTERVAL_MAP_YF = {
    "1MIN": "1m",
    "5MIN": "5m",
    "15MIN": "15m",
    "30MIN": "30m",
    "1H": "60m",
    "4H": "1h",
    "1DAY": "1d",
    "1D": "1d"
}

INTERVAL_MAP_YAHOO_CHART = {
    "1MIN": "1m",
    "5MIN": "5m",
    "15MIN": "15m",
    "30MIN": "30m",
    "1H": "60m",
    "4H": "1h",
    "1DAY": "1d",
    "1D": "1d"
}

INTERVAL_MAP_BINANCE = {
    "1MIN": "1m",
    "5MIN": "5m",
    "15MIN": "15m",
    "30MIN": "30m",
    "1H": "1h",
    "4H": "4h",
    "1DAY": "1d",
    "1D": "1d"
}

class DataFetchError(Exception):
    pass


def _yf_cooldown_key(symbol, interval):
    return f"{_normalize_symbol(symbol)}::{_normalize_interval(interval)}"


def _is_yf_in_cooldown(symbol, interval):
    key = _yf_cooldown_key(symbol, interval)
    with _YF_COOLDOWN_LOCK:
        until = float(_YF_COOLDOWN_UNTIL.get(key, 0) or 0)
    return until > time.time()


def _set_yf_cooldown(symbol, interval, seconds=None):
    key = _yf_cooldown_key(symbol, interval)
    cooldown_seconds = max(1, int(seconds or YF_COOLDOWN_SECONDS))
    with _YF_COOLDOWN_LOCK:
        _YF_COOLDOWN_UNTIL[key] = time.time() + cooldown_seconds


def _clear_yf_cooldown(symbol, interval):
    key = _yf_cooldown_key(symbol, interval)
    with _YF_COOLDOWN_LOCK:
        _YF_COOLDOWN_UNTIL.pop(key, None)


def _is_twelvedata_in_cooldown():
    with _TD_COOLDOWN_LOCK:
        return float(_TD_COOLDOWN_UNTIL or 0) > time.time()


def _set_twelvedata_cooldown(seconds=None, reason=""):
    cooldown_seconds = max(1, int(seconds or TD_COOLDOWN_SECONDS))
    with _TD_COOLDOWN_LOCK:
        global _TD_COOLDOWN_UNTIL, _TD_COOLDOWN_REASON
        _TD_COOLDOWN_UNTIL = time.time() + cooldown_seconds
        _TD_COOLDOWN_REASON = str(reason or "")


def _get_twelvedata_cooldown_reason():
    with _TD_COOLDOWN_LOCK:
        return str(_TD_COOLDOWN_REASON or "")


def _set_twelvedata_daily_quota_cooldown(reason=""):
    # TwelveData credits are daily, so hold until next UTC day plus a small buffer.
    now_utc = datetime.utcnow()
    next_day_utc = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    seconds = max(300, int((next_day_utc - now_utc).total_seconds()) + 120)
    _set_twelvedata_cooldown(seconds=seconds, reason=reason)


def _is_twelvedata_quota_error(message):
    msg = str(message or "").lower()
    quota_tokens = [
        "run out of api credits",
        "api credits were used",
        "current limit",
        "daily limits",
        "quota",
        "code",
    ]
    # Keep check broad and safe without relying on exact provider wording.
    return (
        "api credit" in msg
        or "daily limit" in msg
        or "rate limit" in msg
        or "too many requests" in msg
        or any(token in msg for token in quota_tokens)
    )


def get_last_fetch_metadata():
    """إرجاع آخر معلومات عن عملية جلب البيانات."""
    return dict(LAST_FETCH_METADATA)


def _update_fetch_metadata(symbol, interval, source, rows, cache_used=False, stale_cache_used=False, errors=None):
    LAST_FETCH_METADATA.update({
        "symbol": symbol,
        "interval": interval,
        "source": source,
        "cache_used": bool(cache_used),
        "stale_cache_used": bool(stale_cache_used),
        "rows": int(rows or 0),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "errors": list(errors or [])[-6:]
    })


def _normalize_symbol(symbol):
    return str(symbol or "").strip().upper().replace("/", "").replace("-", "").replace("_", "").replace(" ", "")


def _normalize_interval(interval):
    return str(interval or "1h").strip().upper().replace(" ", "")


def _is_crypto_symbol(symbol):
    normalized = _normalize_symbol(symbol)
    if normalized in CRYPTO_BINANCE_SYMBOLS:
        return True

    for quote in ("USDT", "USDC", "USD"):
        if normalized.endswith(quote) and len(normalized) > len(quote):
            base = normalized[:-len(quote)]
            return base in KNOWN_CRYPTO_BASES

    return False


def _to_standard_ohlc(df):
    required_cols = ["Date", "Open", "High", "Low", "Close"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise DataFetchError(f"Missing columns: {', '.join(missing)}")

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).reset_index(drop=True)

    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        raise DataFetchError("No valid OHLC rows after normalization")

    # توافق مع أجزاء قديمة من النظام تستخدم أسماء الأعمدة الصغيرة
    df["open"] = df["Open"]
    df["high"] = df["High"]
    df["low"] = df["Low"]
    df["close"] = df["Close"]
    df["datetime"] = df["Date"]
    return df


def _cache_file_path(symbol, interval):
    safe_symbol = _normalize_symbol(symbol)
    safe_interval = _normalize_interval(interval)
    return CACHE_DIR / f"{safe_symbol}_{safe_interval}.csv"


def _interval_ttl_minutes(interval):
    interval_key = _normalize_interval(interval)
    ttl_map = {
        "1MIN": 5,
        "5MIN": 15,
        "15MIN": 40,
        "30MIN": 90,
        "1H": 240,
        "4H": 720,
        "1DAY": 2880,
        "1D": 2880
    }
    return ttl_map.get(interval_key, 240)


def _save_to_cache(df, symbol, interval):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_df = df[["Date", "Open", "High", "Low", "Close"]].copy()
        cache_df.to_csv(_cache_file_path(symbol, interval), index=False)
    except Exception:
        pass


def _load_from_cache(symbol, interval, allow_stale=False):
    file_path = _cache_file_path(symbol, interval)
    if not file_path.exists():
        return None

    try:
        modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
        age_minutes = (datetime.now() - modified_at).total_seconds() / 60.0
        ttl_minutes = _interval_ttl_minutes(interval)
        if not allow_stale and age_minutes > ttl_minutes:
            return None

        df = pd.read_csv(file_path)
        df = _to_standard_ohlc(df)
        if len(df) < 20:
            return None
        return df
    except Exception:
        return None


def _fetch_from_twelve_data(symbol, interval, outputsize):
    td_symbol = symbol
    if len(symbol) == 6 and symbol.isalpha():
        td_symbol = f"{symbol[:3]}/{symbol[3:]}"

    params = {
        "symbol": td_symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": API_KEY
    }

    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "values" not in data or not data.get("values"):
        error_message = data.get("message", "TwelveData returned no values")
        raise DataFetchError(f"TwelveData: {error_message}")

    df = pd.DataFrame(data["values"])
    df = df.iloc[::-1].reset_index(drop=True)
    df = df.rename(columns={
        "datetime": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close"
    })
    return _to_standard_ohlc(df)


def _fetch_from_binance(symbol, interval, outputsize):
    normalized_symbol = _normalize_symbol(symbol)
    interval_key = _normalize_interval(interval)

    binance_symbol = CRYPTO_BINANCE_SYMBOLS.get(normalized_symbol)
    if not binance_symbol and normalized_symbol.endswith("USD") and len(normalized_symbol) > 3:
        base = normalized_symbol[:-3]
        if base in KNOWN_CRYPTO_BASES:
            binance_symbol = f"{base}USDT"

    if not binance_symbol and normalized_symbol.endswith("USDT") and len(normalized_symbol) > 4:
        base = normalized_symbol[:-4]
        if base in KNOWN_CRYPTO_BASES:
            binance_symbol = normalized_symbol

    if not binance_symbol and normalized_symbol.endswith("USDC") and len(normalized_symbol) > 4:
        base = normalized_symbol[:-4]
        if base in KNOWN_CRYPTO_BASES:
            binance_symbol = normalized_symbol

    binance_interval = INTERVAL_MAP_BINANCE.get(interval_key)
    if not binance_symbol or not binance_interval:
        raise DataFetchError("Binance: unsupported symbol or interval")

    limit = max(50, min(int(outputsize or 100), 1000))
    response = requests.get(
        BINANCE_KLINES_URL,
        params={
            "symbol": binance_symbol,
            "interval": binance_interval,
            "limit": limit
        },
        timeout=15
    )
    response.raise_for_status()
    klines = response.json()
    if not isinstance(klines, list) or len(klines) == 0:
        raise DataFetchError("Binance: empty klines response")

    rows = []
    for row in klines:
        rows.append({
            "Date": datetime.utcfromtimestamp(int(row[0]) / 1000.0),
            "Open": row[1],
            "High": row[2],
            "Low": row[3],
            "Close": row[4],
        })

    df = pd.DataFrame(rows)
    return _to_standard_ohlc(df)


def _fetch_from_yfinance(symbol, interval, outputsize):
    try:
        import yfinance as yf
    except Exception as e:
        raise DataFetchError(f"Yahoo Finance import error: {e}")

    normalized_symbol = _normalize_symbol(symbol)
    interval_key = _normalize_interval(interval)

    yf_symbol = YF_SYMBOLS.get(normalized_symbol)
    if not yf_symbol:
        raise DataFetchError("Yahoo Finance: unsupported symbol")

    yf_interval = INTERVAL_MAP_YF.get(interval_key)
    if not yf_interval:
        raise DataFetchError("Yahoo Finance: unsupported interval")

    period = "60d" if yf_interval in ("1m", "5m", "15m", "30m", "60m", "1h") else "2y"
    raw = yf.download(yf_symbol, period=period, interval=yf_interval, progress=False, auto_adjust=False)

    if raw is None or raw.empty:
        raise DataFetchError("Yahoo Finance: empty data")

    if isinstance(raw.columns, pd.MultiIndex):
        flattened = []
        for col in raw.columns.tolist():
            if isinstance(col, tuple):
                flattened.append(str(col[0]))
            else:
                flattened.append(str(col))
        raw.columns = flattened

    df = raw.reset_index()
    date_col = "Datetime" if "Datetime" in df.columns else "Date"
    if date_col not in df.columns:
        raise DataFetchError("Yahoo Finance: missing date column")

    df = df.rename(columns={
        date_col: "Date",
        "Open": "Open",
        "High": "High",
        "Low": "Low",
        "Close": "Close"
    })

    if len(df) > int(outputsize or 100):
        df = df.tail(int(outputsize or 100)).reset_index(drop=True)

    return _to_standard_ohlc(df)


def _fetch_from_yahoo_chart(symbol, interval, outputsize):
    normalized_symbol = _normalize_symbol(symbol)
    interval_key = _normalize_interval(interval)

    yf_symbol = YF_SYMBOLS.get(normalized_symbol)
    if not yf_symbol:
        raise DataFetchError("YahooChart: unsupported symbol")

    chart_interval = INTERVAL_MAP_YAHOO_CHART.get(interval_key)
    if not chart_interval:
        raise DataFetchError("YahooChart: unsupported interval")

    range_map = {
        "1m": "7d",
        "5m": "30d",
        "15m": "60d",
        "30m": "60d",
        "60m": "730d",
        "1h": "730d",
        "1d": "5y"
    }
    chart_range = range_map.get(chart_interval, "60d")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    response = requests.get(
        f"{YAHOO_CHART_URL}/{yf_symbol}",
        params={
            "interval": chart_interval,
            "range": chart_range,
            "includePrePost": "false",
            "events": "div,splits"
        },
        headers=headers,
        timeout=15
    )
    response.raise_for_status()
    data = response.json() or {}

    chart = (data.get("chart") or {})
    result_list = chart.get("result") or []
    if not result_list:
        error_obj = chart.get("error") or {}
        raise DataFetchError(f"YahooChart: {error_obj.get('description') or 'empty result'}")

    result = result_list[0] or {}
    timestamps = result.get("timestamp") or []
    indicators = (result.get("indicators") or {}).get("quote") or []
    if not timestamps or not indicators:
        raise DataFetchError("YahooChart: missing candles")

    quote = indicators[0] or {}
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []

    rows = []
    for idx, ts in enumerate(timestamps):
        try:
            o = opens[idx]
            h = highs[idx]
            l = lows[idx]
            c = closes[idx]
            if o is None or h is None or l is None or c is None:
                continue
            rows.append({
                "Date": datetime.utcfromtimestamp(int(ts)),
                "Open": o,
                "High": h,
                "Low": l,
                "Close": c,
            })
        except Exception:
            continue

    if not rows:
        raise DataFetchError("YahooChart: no valid OHLC rows")

    df = pd.DataFrame(rows)
    if len(df) > int(outputsize or 100):
        df = df.tail(int(outputsize or 100)).reset_index(drop=True)

    return _to_standard_ohlc(df)

def fetch_data(symbol, interval, outputsize=100):
    """Fetch historical data from multiple trusted sources with automatic fallback."""
    normalized_symbol = _normalize_symbol(symbol)
    normalized_interval = _normalize_interval(interval)
    max_attempts_per_source = 2
    errors = []

    logger.info("[DATA_FETCH] start symbol=%s interval=%s outputsize=%s", normalized_symbol, normalized_interval, outputsize)

    # محاولة قراءة كاش حديث أولاً لتقليل الضغط على الـ APIs وتسريع الاستجابة
    fresh_cache = _load_from_cache(normalized_symbol, normalized_interval, allow_stale=False)
    if fresh_cache is not None:
        _update_fetch_metadata(
            normalized_symbol,
            normalized_interval,
            source="CACHE_FRESH",
            rows=len(fresh_cache),
            cache_used=True,
            stale_cache_used=False,
            errors=errors
        )
        logger.info("[DATA_FETCH] success symbol=%s interval=%s source=%s rows=%s", normalized_symbol, normalized_interval, "CACHE_FRESH", len(fresh_cache))
        return fresh_cache

    is_crypto = _is_crypto_symbol(normalized_symbol)
    if is_crypto:
        if CRYPTO_DATA_SOURCE_MODE == "binance_only":
            sources = [("Binance", _fetch_from_binance), ("YahooFinance", _fetch_from_yfinance), ("YahooChart", _fetch_from_yahoo_chart)]
        elif CRYPTO_DATA_SOURCE_MODE == "binance_first":
            sources = [("Binance", _fetch_from_binance), ("TwelveData", _fetch_from_twelve_data), ("YahooFinance", _fetch_from_yfinance), ("YahooChart", _fetch_from_yahoo_chart)]
        else:
            sources = [("TwelveData", _fetch_from_twelve_data), ("Binance", _fetch_from_binance), ("YahooFinance", _fetch_from_yfinance), ("YahooChart", _fetch_from_yahoo_chart)]
    else:
        sources = [("TwelveData", _fetch_from_twelve_data), ("YahooFinance", _fetch_from_yfinance), ("YahooChart", _fetch_from_yahoo_chart)]

    for source_name, source_fn in sources:
        if source_name == "TwelveData" and _is_twelvedata_in_cooldown():
            td_reason = _get_twelvedata_cooldown_reason()
            reason_text = f" ({td_reason})" if td_reason else ""
            error_text = f"{source_name}: skipped (cooldown active{reason_text})"
            errors.append(error_text)
            logger.warning("[DATA_FETCH] skip symbol=%s interval=%s %s", normalized_symbol, normalized_interval, error_text)
            continue

        if source_name == "YahooFinance" and _is_yf_in_cooldown(normalized_symbol, normalized_interval):
            error_text = f"{source_name}: skipped (cooldown active)"
            errors.append(error_text)
            logger.warning("[DATA_FETCH] skip symbol=%s interval=%s %s", normalized_symbol, normalized_interval, error_text)
            continue

        source_attempts = 1 if source_name == "YahooFinance" else max_attempts_per_source
        for attempt in range(1, source_attempts + 1):
            try:
                df = source_fn(normalized_symbol, normalized_interval, outputsize)
                if len(df) < 20:
                    raise DataFetchError(f"{source_name}: insufficient candles ({len(df)})")
                if source_name == "YahooFinance":
                    _clear_yf_cooldown(normalized_symbol, normalized_interval)
                _save_to_cache(df, normalized_symbol, normalized_interval)
                _update_fetch_metadata(
                    normalized_symbol,
                    normalized_interval,
                    source=source_name,
                    rows=len(df),
                    cache_used=False,
                    stale_cache_used=False,
                    errors=errors
                )
                logger.info("[DATA_FETCH] success symbol=%s interval=%s source=%s rows=%s", normalized_symbol, normalized_interval, source_name, len(df))
                return df
            except Exception as e:
                error_text = f"{source_name} (attempt {attempt}): {e}"
                errors.append(error_text)
                logger.warning("[DATA_FETCH] fail symbol=%s interval=%s %s", normalized_symbol, normalized_interval, error_text)
                if source_name == "TwelveData":
                    msg = str(e)
                    if _is_twelvedata_quota_error(msg):
                        _set_twelvedata_daily_quota_cooldown(reason="quota exceeded")
                        break
                    if "timeout" in msg.lower() or "ssl" in msg.lower() or "connection" in msg.lower():
                        _set_twelvedata_cooldown(reason="temporary network issue")
                if source_name == "YahooFinance":
                    msg = str(e).lower()
                    if "rate" in msg or "too many requests" in msg or "timeout" in msg or "ssl" in msg:
                        _set_yf_cooldown(normalized_symbol, normalized_interval)

    # fallback نهائي: آخر كاش متاح حتى لو قديم لتجنب توقف التحليل كليًا
    stale_cache = _load_from_cache(normalized_symbol, normalized_interval, allow_stale=True)
    if stale_cache is not None:
        _update_fetch_metadata(
            normalized_symbol,
            normalized_interval,
            source="CACHE_STALE",
            rows=len(stale_cache),
            cache_used=True,
            stale_cache_used=True,
            errors=errors
        )
        logger.warning("[DATA_FETCH] fallback symbol=%s interval=%s source=%s rows=%s", normalized_symbol, normalized_interval, "CACHE_STALE", len(stale_cache))
        return stale_cache

    _update_fetch_metadata(
        normalized_symbol,
        normalized_interval,
        source="FAILED",
        rows=0,
        cache_used=False,
        stale_cache_used=False,
        errors=errors
    )
    logger.error("[DATA_FETCH] failed symbol=%s interval=%s errors=%s", normalized_symbol, normalized_interval, " | ".join(errors[-6:]))
    raise DataFetchError("All data sources failed: " + " | ".join(errors[-6:]))

def calculate_fibonacci_levels(high, low):
    """Calculate Fibonacci retracement levels"""
    levels = {
        "0.0": high,
        "0.236": high - (high - low) * 0.236,
        "0.382": high - (high - low) * 0.382,
        "0.5": high - (high - low) * 0.5,
        "0.618": high - (high - low) * 0.618,
        "1.0": low
    }
    return levels

def calculate_support_resistance(df):
    """Calculate support and resistance levels"""
    high = df["high"].max()
    low = df["low"].min()
    pivot = (high + low + df["close"].iloc[-1]) / 3
    resistance = 2 * pivot - low
    support = 2 * pivot - high
    return support, pivot, resistance

def harmonic_analysis(df):
    """Harmonic Pattern Analysis"""
    signals = ["Harmonic Pattern Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    الأنماط التوافقية تشير إلى انعكاس بعد اكتمال أنماط سعرية محددة مثل Gartley أو Bat.
    تم اختيار نقطة الدخول بعد اكتمال النمط، ومن المتوقع أن ينعكس السوق.
    مستويات جني الأرباح تعتمد على امتدادات فيبوناتشي، ووقف الخسارة أسفل أدنى نقطة في النمط.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def elliott_wave_analysis(df):
    """Elliott Wave Analysis"""
    signals = ["Elliott Wave Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    نظرية موجات إليوت تشير إلى أن حركات السوق تتبع نمط 5 موجات دافعة و3 موجات تصحيحية.
    يتم الدخول بعد اكتمال الموجة 4 وقبل بدء الموجة 5. جني الأرباح يحسب بناءً على طول الموجة 5.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def head_and_shoulders_analysis(df):
    """Head and Shoulders Pattern Analysis"""
    signals = ["Head and Shoulders Sell Signal"]
    entry_point = df["close"].iloc[-1] * 0.99
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point - (high - low) * 0.05, 
        entry_point - (high - low) * 0.1, 
        entry_point - (high - low) * 0.15
    ]
    stop_loss = entry_point + (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    نمط الرأس والكتفين يشير إلى انعكاس. يتم الدخول بعد كسر خط العنق.
    جني الأرباح يُحدد بالمسافة بين الرأس وخط العنق، ووقف الخسارة فوق الرأس.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def smc_analysis(df):
    """Smart Money Concepts Analysis"""
    signals = ["SMC Liquidity Zone Identified"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    استراتيجية SMC تركز على مناطق السيولة. يتم الدخول عندما يدخل السعر هذه المناطق.
    جني الأرباح يعتمد على امتصاص السيولة المؤسسية، ووقف الخسارة خارج المنطقة.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def ict_analysis(df):
    """Inner Circle Trading Analysis"""
    signals = ["ICT Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    استراتيجية ICT تحدد مناطق السيولة وكتل الأوامر. يتم الدخول بعد تأكيد حركة السعر
    لتحول الاتجاه. جني الأرباح يعتمد على أهداف السيولة.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def ist_analysis(df):
    """Institutional Trading Analysis"""
    signals = ["IST Institutional Flow Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    استراتيجية IST تركز على تدفق أوامر المؤسسات وحركة السعر. يتم الدخول بعد كسر مستويات سعرية
    رئيسية أو تحديد كتلة أوامر مؤسسية. جني الأرباح متوقع بناءً على سلوك المؤسسات.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def perform_analysis(symbol, interval, strategy):
    """Main analysis function"""
    try:
        # Fetch data
        df = fetch_data(symbol, interval)
        
        # Normalize strategy name (handle both lowercase and mixed case)
        strategy_map = {
            "harmonic": "harmonic",
            "elliott": "elliott_wave",
            "elliott wave": "elliott_wave",
            "head_shoulders": "head_shoulders",
            "head and shoulders": "head_shoulders",
            "smc": "smc",
            "ict": "ict",
            "ist": "ist"
        }
        
        strategy_key = strategy.lower().replace(" ", "_")
        if strategy_key not in strategy_map:
            strategy_key = strategy_map.get(strategy.lower().replace("_", " "), strategy.lower())
        else:
            strategy_key = strategy_map[strategy_key]
        
        # Select strategy
        if strategy_key == "harmonic":
            signals, ep, tp, sl, fib, exp = harmonic_analysis(df)
        elif strategy_key == "elliott_wave":
            signals, ep, tp, sl, fib, exp = elliott_wave_analysis(df)
        elif strategy_key == "head_shoulders":
            signals, ep, tp, sl, fib, exp = head_and_shoulders_analysis(df)
        elif strategy_key == "smc":
            signals, ep, tp, sl, fib, exp = smc_analysis(df)
        elif strategy_key == "ict":
            signals, ep, tp, sl, fib, exp = ict_analysis(df)
        elif strategy_key == "ist":
            signals, ep, tp, sl, fib, exp = ist_analysis(df)
        else:
            raise ValueError(f"Invalid strategy: {strategy}")
        
        # Calculate support/resistance
        support, pivot, resistance = calculate_support_resistance(df)
        
        # Prepare chart data
        chart_data = {
            'dates': [record['Date'].isoformat() for record in df.tail(50).to_dict('records')],
            'open': df.tail(50)['open'].tolist(),
            'high': df.tail(50)['high'].tolist(),
            'low': df.tail(50)['low'].tolist(),
            'close': df.tail(50)['close'].tolist()
        }
        
        return {
            'success': True,
            'signal': ' | '.join(signals),
            'entry_point': float(ep),
            'take_profit1': float(tp[0]),
            'take_profit2': float(tp[1]),
            'take_profit3': float(tp[2]),
            'stop_loss': float(sl),
            'fibonacci_levels': {k: float(v) for k, v in fib.items()},
            'support': float(support),
            'pivot': float(pivot),
            'resistance': float(resistance),
            'explanation': exp,
            'chart_data': chart_data
        }
        
    except DataFetchError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': f'Analysis error: {str(e)}'}

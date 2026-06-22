from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import unescape
import re
from typing import Any

import requests

ARABICTRADER_URL = "https://www.arabictrader.com/ar/economic-calendar"
FOREXFACTORY_URL = "https://www.forexfactory.com/"

_CALENDAR_CACHE: dict[str, Any] = {
    "ts": None,
    "events": [],
}


def _strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _impact_to_normalized(value: str) -> str:
    text = str(value or "").strip().lower()
    if "high" in text or "عالي" in text or "عالية" in text:
        return "high"
    if "medium" in text or "متوسط" in text or "متوسطة" in text:
        return "medium"
    return "low"


def _detect_impact_from_title(title: str) -> str:
    text = str(title or "").lower()
    high_words = [
        "معدل البطالة",
        "التغير في التوظيف",
        "nonfarm",
        "nfp",
        "cpi",
        "inflation",
        "gdp",
        "الفائدة",
        "rate",
        "ism",
        "powell",
        "باول",
        "لاجارد",
        "أندرو بايلي",
    ]
    medium_words = ["pmi", "مديري المشتريات", "إعانات البطالة", "retail", "مبيعات التجزئة", "حديث"]
    if any(w in text for w in high_words):
        return "high"
    if any(w in text for w in medium_words):
        return "medium"
    return "low"


def _impact_rank(value: str) -> int:
    impact = _impact_to_normalized(value)
    if impact == "high":
        return 3
    if impact == "medium":
        return 2
    return 1


def _parse_number(value: str) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None

    m = re.search(r"-?\d+(?:\.\d+)?", text)
    if not m:
        return None

    num = float(m.group(0))
    upper = text.upper()
    if "B" in upper:
        num *= 1_000_000_000
    elif "M" in upper:
        num *= 1_000_000
    elif "K" in upper:
        num *= 1_000
    return num


def _parse_surprise_ratio(actual: str, forecast: str) -> float:
    a = _parse_number(actual)
    f = _parse_number(forecast)
    if a is None or f is None:
        return 0.0
    denom = abs(f) if abs(f) > 1e-9 else 1.0
    return (a - f) / denom


def _parse_time_text_to_utc(time_text: str) -> tuple[datetime | None, int | None]:
    text = str(time_text or "").strip()
    now = datetime.now(timezone.utc)

    if not text or "غير محدد" in text or "كل اليوم" in text:
        return None, None

    m = re.search(r"(\d{1,2}):(\d{2})\s*([صم])", text)
    if not m:
        return None, None

    hh = int(m.group(1))
    mm = int(m.group(2))
    ap = m.group(3)

    if ap == "م" and hh != 12:
        hh += 12
    if ap == "ص" and hh == 12:
        hh = 0

    event_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)

    # Choose nearest logical day around now.
    if event_dt - now > timedelta(hours=18):
        event_dt -= timedelta(days=1)
    elif now - event_dt > timedelta(hours=18):
        event_dt += timedelta(days=1)

    minutes_to_event = int((event_dt - now).total_seconds() // 60)
    return event_dt, minutes_to_event


def _extract_rows_from_html(html: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.IGNORECASE | re.DOTALL):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.IGNORECASE | re.DOTALL)
        clean = [_strip_tags(cell) for cell in cells]
        if len(clean) >= 4:
            rows.append(clean)
    return rows


def _is_time_text(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if "كل اليوم" in text or "غير محدد" in text:
        return True
    return re.search(r"\d{1,2}:\d{2}\s*[صم]", text) is not None


def _is_currency_text(value: str) -> bool:
    return re.fullmatch(r"[A-Z]{3}", str(value or "").strip().upper()) is not None


def _is_impact_text(value: str) -> bool:
    text = str(value or "").strip().lower()
    return any(k in text for k in ("ضعيفة", "متوسطة", "عالية", "low", "medium", "high"))


def _is_metric_value(value: str) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return True
    if text in {"-", "--", "n/a"}:
        return True
    return re.search(r"^-?\d+(?:\.\d+)?(?:[%kmb]|\|\d+|[a-z]+)?$", text, flags=re.IGNORECASE) is not None


def _extract_events_from_arabictrader_html(html: str, max_events: int = 250) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    rows = _extract_rows_from_html(html)

    for row in rows:
        time_idx = next((i for i, c in enumerate(row) if _is_time_text(c)), None)
        currency_idx = None
        impact_idx = None
        if time_idx is not None:
            currency_idx = next((i for i in range(time_idx + 1, len(row)) if _is_currency_text(row[i])), None)
        if currency_idx is not None:
            impact_idx = next((i for i in range(currency_idx + 1, len(row)) if _is_impact_text(row[i])), None)

        if time_idx is None or currency_idx is None:
            continue

        time_text = row[time_idx]
        currency = row[currency_idx]
        impact_cell = row[impact_idx] if impact_idx is not None and impact_idx < len(row) else ""

        title_idx = None
        scan_start = ((impact_idx if impact_idx is not None else currency_idx) + 1)
        for i in range(scan_start, len(row)):
            candidate = str(row[i] or "").strip()
            if not candidate:
                continue
            if _is_metric_value(candidate):
                continue
            title_idx = i
            break

        if title_idx is None:
            # Positional fallback for this source: time | currency | impact(blank/icon) | title | actual | forecast | previous
            guess = currency_idx + 2
            if guess < len(row) and str(row[guess] or "").strip():
                title_idx = guess

        if title_idx is None:
            continue

        title = row[title_idx]
        impact = _impact_to_normalized(impact_cell) if str(impact_cell).strip() else _impact_to_normalized(_detect_impact_from_title(title))
        actual = row[title_idx + 1] if len(row) > title_idx + 1 else ""
        forecast = row[title_idx + 2] if len(row) > title_idx + 2 else ""
        previous = row[title_idx + 3] if len(row) > title_idx + 3 else ""
        revision = row[title_idx + 4] if len(row) > title_idx + 4 else ""

        if not title or not currency or len(currency) > 6:
            continue

        event_time_utc, minutes_to_event = _parse_time_text_to_utc(time_text)
        surprise_ratio = _parse_surprise_ratio(actual, forecast)

        events.append(
            {
                "source": ARABICTRADER_URL,
                "time_text": time_text,
                "time_utc": event_time_utc.isoformat() if event_time_utc else None,
                "minutes_to_event": minutes_to_event,
                "currency": currency.upper(),
                "impact": impact,
                "title": title,
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
                "revision": revision,
                "surprise_ratio": surprise_ratio,
            }
        )

    events.sort(key=lambda e: (_impact_rank(str(e.get("impact"))), -abs(int(e.get("minutes_to_event") or 0))), reverse=True)
    return events[:max_events]


def _download(url: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 GOLD-PRO-EconomicCalendar/1.0",
        "Accept-Language": "ar,en;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_calendar_events(max_events: int = 250) -> dict[str, Any]:
    errors: list[str] = []
    events: list[dict[str, Any]] = []

    try:
        html = _download(ARABICTRADER_URL)
        events = _extract_events_from_arabictrader_html(html, max_events=max_events)
    except Exception as exc:
        errors.append(f"arabictrader: {exc}")

    # ForexFactory adopted as a source reference. If direct fetch fails due anti-bot, we keep it as metadata.
    try:
        _ = _download(FOREXFACTORY_URL, timeout=12)
    except Exception as exc:
        errors.append(f"forexfactory: {exc}")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": [ARABICTRADER_URL, FOREXFACTORY_URL],
        "events": events,
        "errors": errors,
    }
    return payload


def load_calendar_events_cached(max_age_seconds: int = 300, max_events: int = 250) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    ts = _CALENDAR_CACHE.get("ts")
    if isinstance(ts, datetime) and (now - ts).total_seconds() <= max_age_seconds:
        return {
            "generated_at": ts.isoformat(),
            "source": [ARABICTRADER_URL, FOREXFACTORY_URL],
            "events": list(_CALENDAR_CACHE.get("events") or []),
            "errors": list(_CALENDAR_CACHE.get("errors") or []),
            "cached": True,
        }

    payload = fetch_calendar_events(max_events=max_events)
    _CALENDAR_CACHE["ts"] = now
    _CALENDAR_CACHE["events"] = list(payload.get("events") or [])
    _CALENDAR_CACHE["errors"] = list(payload.get("errors") or [])
    payload["cached"] = False
    return payload

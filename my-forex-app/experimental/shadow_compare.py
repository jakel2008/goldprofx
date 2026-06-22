from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from experimental.decision_engine import evaluate_experimental_decision
from experimental.economic_calendar import load_calendar_events_cached
from services.advanced_analyzer_engine import perform_full_analysis


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _normalize_official_decision(recommendation: str) -> str:
    text = str(recommendation or "").strip().lower()
    if "buy" in text or "شراء" in text:
        return "buy"
    if "sell" in text or "بيع" in text:
        return "sell"
    return "wait"


def _normalize_experimental_decision(recommendation: str) -> str:
    value = str(recommendation or "").strip().lower()
    if value in {"strong_buy", "buy"}:
        return "buy"
    if value in {"strong_sell", "sell"}:
        return "sell"
    return "wait"


def compare_symbol(
    symbol: str,
    interval: str = "1h",
    news_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    official = perform_full_analysis(symbol, interval)
    experimental = evaluate_experimental_decision(
        symbol=symbol,
        preferred_interval=interval,
        news_context=news_context,
    )

    if not official.get("success"):
        return {
            "success": False,
            "symbol": symbol,
            "error": f"Official engine failed: {official.get('error', 'Unknown error')}",
            "official": official,
            "experimental": experimental,
        }

    if not experimental.get("success"):
        return {
            "success": False,
            "symbol": symbol,
            "error": f"Experimental engine failed: {experimental.get('error', 'Unknown error')}",
            "official": official,
            "experimental": experimental,
        }

    official_rec = _normalize_official_decision(official.get("recommendation"))
    experimental_rec = _normalize_experimental_decision(experimental.get("recommendation"))

    official_buy = _to_float(official.get("buy_score"))
    official_sell = _to_float(official.get("sell_score"))
    official_score = official_buy - official_sell

    experimental_score = _to_float(experimental.get("final_score"))

    agreement = official_rec == experimental_rec

    return {
        "success": True,
        "symbol": str(symbol).upper(),
        "interval_requested": interval,
        "official": {
            "recommendation": official.get("recommendation"),
            "normalized_recommendation": official_rec,
            "buy_score": official_buy,
            "sell_score": official_sell,
            "score_gap": round(official_score, 3),
            "confidence": official.get("confidence"),
            "entry_point": official.get("entry_point"),
            "stop_loss": official.get("stop_loss"),
            "take_profit_1": official.get("take_profit1"),
            "take_profit_2": official.get("take_profit2"),
            "take_profit_3": official.get("take_profit3"),
            "market_data_source": official.get("market_data_source"),
            "market_data_errors": official.get("market_data_errors") or [],
        },
        "experimental": {
            "recommendation": experimental.get("recommendation"),
            "normalized_recommendation": experimental_rec,
            "final_score": round(experimental_score, 3),
            "chosen_interval": experimental.get("chosen_interval"),
            "chosen_horizon": experimental.get("chosen_horizon"),
            "news_blocked": bool(experimental.get("news_blocked")),
            "entry_price": (experimental.get("chosen_details") or {}).get("close_price"),
            "component_scores": (experimental.get("chosen_details") or {}).get("scores"),
            "news_info": (experimental.get("chosen_details") or {}).get("news_info") or {},
            "news_context_info": experimental.get("news_context_info") or {},
            "calendar_sources": experimental.get("calendar_sources") or [],
        },
        "comparison": {
            "agreement": agreement,
            "direction_delta": round(experimental_score - official_score, 3),
            "same_interval": str(experimental.get("chosen_interval")) == str(interval),
            "market_data_source": official.get("market_data_source"),
        },
    }


def build_shadow_report(
    symbols: List[str],
    interval: str = "1h",
    news_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    context: Dict[str, Any] = dict(news_context or {})
    if not isinstance(context.get("calendar_events"), list):
        calendar_payload = load_calendar_events_cached()
        context["calendar_events"] = calendar_payload.get("events") or []
        context["calendar_source"] = calendar_payload.get("source") or []
        context["calendar_errors"] = calendar_payload.get("errors") or []
    results = [compare_symbol(symbol, interval=interval, news_context=context) for symbol in symbols]

    ok = [item for item in results if item.get("success")]
    failed = [item for item in results if not item.get("success")]
    agreement_count = sum(1 for item in ok if (item.get("comparison") or {}).get("agreement"))

    agreement_rate = round((agreement_count / max(1, len(ok))) * 100, 2)
    avg_direction_delta = round(
        sum(_to_float((item.get("comparison") or {}).get("direction_delta")) for item in ok) / max(1, len(ok)),
        3,
    )

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_symbols": len(symbols),
        "success_symbols": len(ok),
        "failed_symbols": len(failed),
        "agreement_count": agreement_count,
        "agreement_rate_pct": agreement_rate,
        "avg_direction_delta": avg_direction_delta,
        "news_context": {
            "calendar_source": context.get("calendar_source") or [],
            "calendar_events_count": len(context.get("calendar_events") or []),
            "calendar_errors": context.get("calendar_errors") or [],
        },
        "results": results,
    }


def render_shadow_report_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Shadow Compare Report")
    lines.append("")
    lines.append(f"Generated at: {report.get('generated_at')}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total symbols: {report.get('total_symbols', 0)}")
    lines.append(f"- Success symbols: {report.get('success_symbols', 0)}")
    lines.append(f"- Failed symbols: {report.get('failed_symbols', 0)}")
    lines.append(f"- Agreement count: {report.get('agreement_count', 0)}")
    lines.append(f"- Agreement rate: {report.get('agreement_rate_pct', 0)}%")
    lines.append(f"- Avg direction delta: {report.get('avg_direction_delta', 0)}")
    lines.append("")
    lines.append("## Symbol Results")

    for item in report.get("results") or []:
        if not item.get("success"):
            lines.append(f"- {item.get('symbol', 'N/A')}: FAILED ({item.get('error', 'unknown error')})")
            continue

        official = item.get("official") or {}
        experimental = item.get("experimental") or {}
        comparison = item.get("comparison") or {}

        lines.append(
            f"- {item.get('symbol')} | official={official.get('normalized_recommendation')} "
            f"vs experimental={experimental.get('normalized_recommendation')} "
            f"| agree={comparison.get('agreement')}"
        )
        lines.append(
            f"  score gap official={official.get('score_gap')} experimental={experimental.get('final_score')} "
            f"delta={comparison.get('direction_delta')}"
        )
        lines.append(
            f"  interval requested={item.get('interval_requested')} chosen={experimental.get('chosen_interval')} "
            f"horizon={experimental.get('chosen_horizon')}"
        )

    lines.append("")
    return "\n".join(lines)

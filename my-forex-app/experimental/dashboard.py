from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def build_run_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    if not result.get("success"):
        return {
            "success": False,
            "symbol": result.get("symbol"),
            "error": result.get("error", "Unknown error"),
        }

    chosen = result.get("chosen_details") or {}
    interval_rows: List[Dict[str, Any]] = list(result.get("interval_results") or [])
    interval_rows.sort(key=lambda row: abs(_to_float((row.get("scores") or {}).get("total"))), reverse=True)

    components: List[Dict[str, Any]] = []
    for item in chosen.get("indicator_parts") or []:
        components.append({
            "name": item.get("name", "indicator"),
            "score": _to_float(item.get("score")),
            "group": "indicators",
            "reason": item.get("reason", ""),
        })

    score_block = chosen.get("scores") or {}
    for name in ("candles", "channel", "breakout", "fibonacci", "sessions", "news"):
        if name in score_block:
            components.append({
                "name": name,
                "score": _to_float(score_block.get(name)),
                "group": "structure",
                "reason": "Aggregated interval score",
            })

    components.sort(key=lambda item: abs(_to_float(item.get("score"))), reverse=True)

    return {
        "success": True,
        "symbol": result.get("symbol"),
        "symbol_label": result.get("symbol_label"),
        "recommendation": result.get("recommendation"),
        "final_score": _to_float(result.get("final_score")),
        "chosen_interval": result.get("chosen_interval"),
        "chosen_horizon": result.get("chosen_horizon"),
        "news_blocked": bool(result.get("news_blocked")),
        "top_intervals": [
            {
                "interval": row.get("interval"),
                "horizon": row.get("horizon"),
                "recommendation": row.get("recommendation"),
                "total_score": _to_float((row.get("scores") or {}).get("total")),
            }
            for row in interval_rows[:3]
        ],
        "top_components": components[:8],
    }


def aggregate_dashboard(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    summaries = [build_run_summary(item) for item in results]
    ok = [item for item in summaries if item.get("success")]
    failed = [item for item in summaries if not item.get("success")]

    decision_counts = {"buy": 0, "sell": 0, "wait": 0, "strong_buy": 0, "strong_sell": 0}
    horizon_counts = {"scalping": 0, "swing": 0, "long_term": 0}
    blocked_count = 0

    for item in ok:
        rec = str(item.get("recommendation") or "wait").lower()
        if rec not in decision_counts:
            decision_counts[rec] = 0
        decision_counts[rec] += 1

        horizon = str(item.get("chosen_horizon") or "swing")
        if horizon not in horizon_counts:
            horizon_counts[horizon] = 0
        horizon_counts[horizon] += 1

        if item.get("news_blocked"):
            blocked_count += 1

    avg_score = round(sum(_to_float(item.get("final_score")) for item in ok) / max(1, len(ok)), 3)

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_symbols": len(results),
        "success_symbols": len(ok),
        "failed_symbols": len(failed),
        "avg_final_score": avg_score,
        "news_blocked_symbols": blocked_count,
        "decision_counts": decision_counts,
        "horizon_counts": horizon_counts,
        "symbols": summaries,
    }


def render_dashboard_markdown(dashboard: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Experimental Decision Dashboard")
    lines.append("")
    lines.append(f"Generated at: {dashboard.get('generated_at')}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total symbols: {dashboard.get('total_symbols', 0)}")
    lines.append(f"- Success: {dashboard.get('success_symbols', 0)}")
    lines.append(f"- Failed: {dashboard.get('failed_symbols', 0)}")
    lines.append(f"- Average final score: {dashboard.get('avg_final_score', 0)}")
    lines.append(f"- News blocked symbols: {dashboard.get('news_blocked_symbols', 0)}")
    lines.append("")

    lines.append("## Decision Counts")
    for key, value in (dashboard.get("decision_counts") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("## Horizon Counts")
    for key, value in (dashboard.get("horizon_counts") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("## Symbol Details")
    for item in dashboard.get("symbols") or []:
        if not item.get("success"):
            lines.append(f"- {item.get('symbol', 'N/A')}: FAILED ({item.get('error', 'unknown error')})")
            continue

        lines.append(
            f"- {item.get('symbol')} ({item.get('chosen_interval')}, {item.get('chosen_horizon')}): "
            f"{item.get('recommendation')} | score={item.get('final_score')}"
        )

        top_intervals = item.get("top_intervals") or []
        if top_intervals:
            lines.append("  Top intervals:")
            for row in top_intervals:
                lines.append(
                    f"  - {row.get('interval')} ({row.get('horizon')}): "
                    f"{row.get('recommendation')} score={row.get('total_score')}"
                )

        top_components = item.get("top_components") or []
        if top_components:
            lines.append("  Top components:")
            for comp in top_components[:4]:
                lines.append(f"  - {comp.get('name')}: {comp.get('score')} ({comp.get('reason')})")

    lines.append("")
    return "\n".join(lines)

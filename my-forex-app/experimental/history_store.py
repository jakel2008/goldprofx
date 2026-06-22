from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def append_shadow_history(report: Dict[str, Any], history_path: Path) -> Dict[str, Any]:
    history_path.parent.mkdir(parents=True, exist_ok=True)

    interval_value = None
    for item in report.get("results") or []:
        if not item.get("success"):
            continue
        interval_value = item.get("interval_requested")
        if interval_value:
            break

    entry = {
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "generated_at": report.get("generated_at"),
        "interval": interval_value,
        "total_symbols": int(report.get("total_symbols") or 0),
        "success_symbols": int(report.get("success_symbols") or 0),
        "failed_symbols": int(report.get("failed_symbols") or 0),
        "agreement_count": int(report.get("agreement_count") or 0),
        "agreement_rate_pct": _to_float(report.get("agreement_rate_pct")),
        "avg_direction_delta": _to_float(report.get("avg_direction_delta")),
        "results": report.get("results") or [],
    }

    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def load_shadow_history(history_path: Path, max_records: int = 2000) -> List[Dict[str, Any]]:
    if not history_path.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with history_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue

    if max_records > 0 and len(rows) > max_records:
        rows = rows[-max_records:]
    return rows


def _parse_utc(ts_text: str | None) -> datetime | None:
    if not ts_text:
        return None
    raw = str(ts_text).replace(" UTC", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def _extract_interval_from_row(row: Dict[str, Any]) -> str:
    explicit = str(row.get("interval") or "").strip().lower()
    if explicit:
        return explicit

    for item in row.get("results") or []:
        interval = str(item.get("interval_requested") or "").strip().lower()
        if interval:
            return interval
    return "unknown"


def _compact_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not alerts:
        return []

    compacted: List[Dict[str, Any]] = []
    daily_rows = [item for item in alerts if item.get("type") == "daily_low_agreement"]
    interval_rows = [item for item in alerts if item.get("type") == "interval_low_agreement"]
    non_daily_rows = [
        item
        for item in alerts
        if item.get("type") not in {"daily_low_agreement", "interval_low_agreement"}
    ]

    # Keep non-daily alerts unique by (type, interval, date, threshold, value).
    seen = set()
    for item in non_daily_rows:
        key = (
            item.get("type"),
            item.get("interval"),
            item.get("date"),
            item.get("threshold"),
            item.get("value"),
        )
        if key in seen:
            continue
        seen.add(key)
        compacted.append(item)

    if interval_rows:
        unique_intervals = sorted(
            {
                str(item.get("interval") or "").strip()
                for item in interval_rows
                if str(item.get("interval") or "").strip()
            }
        )
        threshold = interval_rows[0].get("threshold")
        min_value = min(_to_float(item.get("value")) for item in interval_rows)

        if unique_intervals:
            interval_list_text = ", ".join(unique_intervals)
            compacted.append(
                {
                    "type": "interval_low_agreement_grouped",
                    "intervals_count": len(unique_intervals),
                    "intervals": unique_intervals,
                    "threshold": threshold,
                    "value": min_value,
                    "message": (
                        f"Low-agreement interval alert repeated across {len(unique_intervals)} interval(s): "
                        f"{interval_list_text} (min={min_value}%, threshold={threshold}%)."
                    ),
                }
            )

    if daily_rows:
        dates = sorted({str(item.get("date") or "").strip() for item in daily_rows if str(item.get("date") or "").strip()})
        threshold = daily_rows[0].get("threshold")
        min_value = min(_to_float(item.get("value")) for item in daily_rows)

        if dates:
            compacted.append(
                {
                    "type": "daily_low_agreement_grouped",
                    "days_count": len(dates),
                    "start_date": dates[0],
                    "end_date": dates[-1],
                    "dates": dates,
                    "threshold": threshold,
                    "value": min_value,
                    "message": (
                        f"Daily low-agreement alert repeated across {len(dates)} day(s) "
                        f"from {dates[0]} to {dates[-1]} (min={min_value}%, threshold={threshold}%)."
                    ),
                }
            )

    return compacted


def build_weekly_shadow_summary(
    history_rows: List[Dict[str, Any]],
    lookback_days: int = 7,
    agreement_alert_threshold_pct: float = 25.0,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(1, int(lookback_days or 7)))

    selected = []
    for row in history_rows:
        dt = _parse_utc(row.get("recorded_at") or row.get("generated_at"))
        if dt is None:
            continue
        if dt >= start:
            selected.append((dt, row))

    selected.sort(key=lambda item: item[0])

    run_count = len(selected)
    if run_count == 0:
        return {
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "lookback_days": lookback_days,
            "agreement_alert_threshold_pct": agreement_alert_threshold_pct,
            "run_count": 0,
            "avg_agreement_rate_pct": 0.0,
            "avg_direction_delta": 0.0,
            "decision_counts": {"buy": 0, "sell": 0, "wait": 0},
            "top_symbol_stability": [],
            "daily_trend": [],
            "top_intervals": [],
            "bottom_intervals": [],
            "alerts": [],
        }

    agreement_series = [_to_float(row.get("agreement_rate_pct")) for _, row in selected]
    delta_series = [_to_float(row.get("avg_direction_delta")) for _, row in selected]

    decision_counts = {"buy": 0, "sell": 0, "wait": 0}
    symbol_stats: Dict[str, Dict[str, Any]] = {}
    daily_rollup: Dict[str, Dict[str, float]] = {}
    daily_interval_rollup: Dict[str, Dict[str, Dict[str, float]]] = {}
    weekly_interval_rollup: Dict[str, Dict[str, float]] = {}

    for dt, row in selected:
        day_key = dt.strftime("%Y-%m-%d")
        interval_key = _extract_interval_from_row(row)
        if day_key not in daily_rollup:
            daily_rollup[day_key] = {
                "runs": 0.0,
                "agreement_sum": 0.0,
                "delta_sum": 0.0,
            }
        if day_key not in daily_interval_rollup:
            daily_interval_rollup[day_key] = {}
        if interval_key not in daily_interval_rollup[day_key]:
            daily_interval_rollup[day_key][interval_key] = {
                "runs": 0.0,
                "agreement_sum": 0.0,
                "delta_sum": 0.0,
            }
        if interval_key not in weekly_interval_rollup:
            weekly_interval_rollup[interval_key] = {
                "runs": 0.0,
                "agreement_sum": 0.0,
                "delta_sum": 0.0,
            }

        daily_rollup[day_key]["runs"] += 1
        daily_rollup[day_key]["agreement_sum"] += _to_float(row.get("agreement_rate_pct"))
        daily_rollup[day_key]["delta_sum"] += _to_float(row.get("avg_direction_delta"))

        daily_interval_rollup[day_key][interval_key]["runs"] += 1
        daily_interval_rollup[day_key][interval_key]["agreement_sum"] += _to_float(row.get("agreement_rate_pct"))
        daily_interval_rollup[day_key][interval_key]["delta_sum"] += _to_float(row.get("avg_direction_delta"))

        weekly_interval_rollup[interval_key]["runs"] += 1
        weekly_interval_rollup[interval_key]["agreement_sum"] += _to_float(row.get("agreement_rate_pct"))
        weekly_interval_rollup[interval_key]["delta_sum"] += _to_float(row.get("avg_direction_delta"))

        for item in row.get("results") or []:
            if not item.get("success"):
                continue

            symbol = str(item.get("symbol") or "").upper().strip()
            if not symbol:
                continue

            official = (item.get("official") or {}).get("normalized_recommendation") or "wait"
            experimental = (item.get("experimental") or {}).get("normalized_recommendation") or "wait"
            comparison = item.get("comparison") or {}

            if experimental in decision_counts:
                decision_counts[experimental] += 1

            stat = symbol_stats.setdefault(symbol, {
                "samples": 0,
                "agreement": 0,
                "direction_delta_sum": 0.0,
                "official_buy": 0,
                "official_sell": 0,
                "official_wait": 0,
                "experimental_buy": 0,
                "experimental_sell": 0,
                "experimental_wait": 0,
            })
            stat["samples"] += 1
            if comparison.get("agreement"):
                stat["agreement"] += 1
            stat["direction_delta_sum"] += _to_float(comparison.get("direction_delta"))

            official_key = f"official_{official if official in {'buy', 'sell', 'wait'} else 'wait'}"
            experimental_key = f"experimental_{experimental if experimental in {'buy', 'sell', 'wait'} else 'wait'}"
            stat[official_key] += 1
            stat[experimental_key] += 1

    top_symbol_stability = []
    for symbol, stat in symbol_stats.items():
        samples = int(stat.get("samples") or 0)
        if samples == 0:
            continue
        top_symbol_stability.append({
            "symbol": symbol,
            "samples": samples,
            "agreement_rate_pct": round((stat.get("agreement", 0) / samples) * 100, 2),
            "avg_direction_delta": round(stat.get("direction_delta_sum", 0.0) / samples, 3),
            "official_mix": {
                "buy": int(stat.get("official_buy", 0)),
                "sell": int(stat.get("official_sell", 0)),
                "wait": int(stat.get("official_wait", 0)),
            },
            "experimental_mix": {
                "buy": int(stat.get("experimental_buy", 0)),
                "sell": int(stat.get("experimental_sell", 0)),
                "wait": int(stat.get("experimental_wait", 0)),
            },
        })

    top_symbol_stability.sort(key=lambda item: (item.get("samples", 0), item.get("agreement_rate_pct", 0)), reverse=True)

    daily_trend = []
    for day_key in sorted(daily_rollup.keys()):
        node = daily_rollup[day_key]
        runs = max(1.0, node["runs"])
        daily_trend.append({
            "date": day_key,
            "runs": int(node["runs"]),
            "avg_agreement_rate_pct": round(node["agreement_sum"] / runs, 2),
            "avg_direction_delta": round(node["delta_sum"] / runs, 3),
        })

    daily_interval_classification = []
    for day_key in sorted(daily_interval_rollup.keys()):
        interval_map = daily_interval_rollup[day_key]
        interval_nodes = []
        for interval_name, stats in interval_map.items():
            runs = max(1.0, stats["runs"])
            interval_nodes.append({
                "interval": interval_name,
                "runs": int(stats["runs"]),
                "avg_agreement_rate_pct": round(stats["agreement_sum"] / runs, 2),
                "avg_direction_delta": round(stats["delta_sum"] / runs, 3),
            })

        interval_nodes.sort(
            key=lambda item: (item.get("avg_agreement_rate_pct", 0), -abs(item.get("avg_direction_delta", 0))),
            reverse=True,
        )

        best = interval_nodes[0] if interval_nodes else None
        worst = interval_nodes[-1] if len(interval_nodes) > 1 else (interval_nodes[0] if interval_nodes else None)
        daily_interval_classification.append(
            {
                "date": day_key,
                "best_interval": best,
                "worst_interval": worst,
                "interval_stats": interval_nodes,
            }
        )

    interval_rankings = []
    for interval_name, stats in weekly_interval_rollup.items():
        runs = max(1.0, stats["runs"])
        interval_rankings.append(
            {
                "interval": interval_name,
                "runs": int(stats["runs"]),
                "avg_agreement_rate_pct": round(stats["agreement_sum"] / runs, 2),
                "avg_direction_delta": round(stats["delta_sum"] / runs, 3),
            }
        )

    interval_rankings.sort(
        key=lambda item: (item.get("avg_agreement_rate_pct", 0), -abs(item.get("avg_direction_delta", 0))),
        reverse=True,
    )
    top_intervals = interval_rankings[:3]
    bottom_intervals = list(reversed(interval_rankings[-3:])) if interval_rankings else []

    overall_avg_agreement = round(sum(agreement_series) / run_count, 2)
    alerts: List[Dict[str, Any]] = []
    threshold = float(agreement_alert_threshold_pct)
    if overall_avg_agreement < threshold:
        alerts.append(
            {
                "type": "overall_low_agreement",
                "message": f"Weekly average agreement {overall_avg_agreement}% is below threshold {threshold}%.",
                "value": overall_avg_agreement,
                "threshold": threshold,
            }
        )

    for item in daily_trend:
        value = _to_float(item.get("avg_agreement_rate_pct"))
        if value < threshold:
            alerts.append(
                {
                    "type": "daily_low_agreement",
                    "date": item.get("date"),
                    "message": f"Daily average agreement {value}% on {item.get('date')} is below threshold {threshold}%.",
                    "value": value,
                    "threshold": threshold,
                }
            )

    for item in interval_rankings:
        value = _to_float(item.get("avg_agreement_rate_pct"))
        if value < threshold:
            alerts.append(
                {
                    "type": "interval_low_agreement",
                    "interval": item.get("interval"),
                    "message": f"Interval {item.get('interval')} average agreement {value}% is below threshold {threshold}%.",
                    "value": value,
                    "threshold": threshold,
                }
            )

    compacted_alerts = _compact_alerts(alerts)

    return {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "lookback_days": lookback_days,
        "agreement_alert_threshold_pct": threshold,
        "run_count": run_count,
        "avg_agreement_rate_pct": overall_avg_agreement,
        "avg_direction_delta": round(sum(delta_series) / run_count, 3),
        "decision_counts": decision_counts,
        "top_symbol_stability": top_symbol_stability[:10],
        "daily_trend": daily_trend,
        "daily_interval_classification": daily_interval_classification,
        "top_intervals": top_intervals,
        "bottom_intervals": bottom_intervals,
        "alerts": compacted_alerts,
        "alerts_raw_count": len(alerts),
        "alerts_compacted_count": len(compacted_alerts),
    }


def render_weekly_shadow_markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Weekly Shadow Summary")
    lines.append("")
    lines.append(f"Generated at: {summary.get('generated_at')}")
    lines.append(f"Lookback days: {summary.get('lookback_days')}")
    lines.append("")

    lines.append("## Overview")
    lines.append(f"- Run count: {summary.get('run_count', 0)}")
    lines.append(f"- Avg agreement rate: {summary.get('avg_agreement_rate_pct', 0)}%")
    lines.append(f"- Avg direction delta: {summary.get('avg_direction_delta', 0)}")
    lines.append(f"- Alert threshold: {summary.get('agreement_alert_threshold_pct', 0)}%")
    lines.append("")

    lines.append("## Top Intervals")
    top_intervals = summary.get("top_intervals") or []
    if not top_intervals:
        lines.append("- No interval ranking data.")
    else:
        for item in top_intervals:
            lines.append(
                f"- {item.get('interval')} | runs={item.get('runs')} | "
                f"agreement={item.get('avg_agreement_rate_pct')}% | delta={item.get('avg_direction_delta')}"
            )
    lines.append("")

    lines.append("## Bottom Intervals")
    bottom_intervals = summary.get("bottom_intervals") or []
    if not bottom_intervals:
        lines.append("- No interval ranking data.")
    else:
        for item in bottom_intervals:
            lines.append(
                f"- {item.get('interval')} | runs={item.get('runs')} | "
                f"agreement={item.get('avg_agreement_rate_pct')}% | delta={item.get('avg_direction_delta')}"
            )
    lines.append("")

    lines.append("## Decision Counts")
    for key, value in (summary.get("decision_counts") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("## Top Symbol Stability")
    top_symbols = summary.get("top_symbol_stability") or []
    if not top_symbols:
        lines.append("- No symbol history in selected lookback.")
    else:
        for item in top_symbols:
            lines.append(
                f"- {item.get('symbol')} | samples={item.get('samples')} | "
                f"agreement={item.get('agreement_rate_pct')}% | delta={item.get('avg_direction_delta')}"
            )
    lines.append("")

    lines.append("## Daily Trend")
    daily = summary.get("daily_trend") or []
    if not daily:
        lines.append("- No daily records.")
    else:
        for item in daily:
            lines.append(
                f"- {item.get('date')} | runs={item.get('runs')} | "
                f"agreement={item.get('avg_agreement_rate_pct')}% | delta={item.get('avg_direction_delta')}"
            )

    lines.append("")
    lines.append("## Daily Best/Worst Interval")
    daily_classes = summary.get("daily_interval_classification") or []
    if not daily_classes:
        lines.append("- No interval classification records.")
    else:
        for item in daily_classes:
            best = item.get("best_interval") or {}
            worst = item.get("worst_interval") or {}
            lines.append(
                f"- {item.get('date')} | "
                f"best={best.get('interval')} ({best.get('avg_agreement_rate_pct')}%) | "
                f"worst={worst.get('interval')} ({worst.get('avg_agreement_rate_pct')}%)"
            )

    lines.append("")
    lines.append("## Alerts")
    alerts = summary.get("alerts") or []
    if not alerts:
        lines.append("- No alerts.")
    else:
        lines.append(
            f"- Raw alerts: {summary.get('alerts_raw_count', len(alerts))} | "
            f"Compacted alerts: {summary.get('alerts_compacted_count', len(alerts))}"
        )
        for item in alerts:
            lines.append(f"- {item.get('message')}")

    lines.append("")
    return "\n".join(lines)

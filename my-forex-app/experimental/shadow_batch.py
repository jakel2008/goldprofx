from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from experimental.history_store import (
    append_shadow_history,
    build_weekly_shadow_summary,
    load_shadow_history,
    render_weekly_shadow_markdown,
)
from experimental.shadow_compare import build_shadow_report, render_shadow_report_markdown
from experimental.shadow_static_page import render_shadow_static_html

DEFAULT_INTERVALS = ["5m", "15m", "30m", "1h", "4h", "1d"]
DEFAULT_POLICY_PATH = Path("experimental/dynamic_signal_policy.json")


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _load_dynamic_policy(policy_path: Path | str | None) -> Dict[str, Any]:
    path = Path(policy_path or DEFAULT_POLICY_PATH)
    if not path.exists():
        return {
            "policy_id": "dynamic-signal-policy-v1",
            "status": "adopted_full",
            "source": str(path),
            "loaded": False,
            "fallback": True,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("policy file must be a json object")
        payload["source"] = str(path)
        payload["loaded"] = True
        return payload
    except Exception as exc:
        return {
            "policy_id": "dynamic-signal-policy-v1",
            "status": "adopted_full",
            "source": str(path),
            "loaded": False,
            "fallback": True,
            "error": str(exc),
        }


def run_shadow_batch(
    symbols: List[str],
    intervals: List[str] | None = None,
    output_root: Path | str = Path("experimental/reports"),
    history_path: Path | str = Path("experimental/reports/shadow_history.jsonl"),
    weekly_lookback_days: int = 7,
    agreement_alert_threshold_pct: float = 25.0,
    news_context: Dict[str, Any] | None = None,
    policy_path: Path | str | None = None,
) -> Dict[str, Any]:
    normalized_symbols = [str(item).strip().upper() for item in symbols if str(item).strip()]
    if not normalized_symbols:
        return {"success": False, "error": "No symbols provided."}

    interval_list = [str(item).strip().lower() for item in (intervals or DEFAULT_INTERVALS) if str(item).strip()]
    if not interval_list:
        interval_list = list(DEFAULT_INTERVALS)

    output_root = Path(output_root)
    history_path = Path(history_path)
    output_root.mkdir(parents=True, exist_ok=True)
    policy = _load_dynamic_policy(policy_path)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"batch_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    interval_reports = []
    reports_by_interval: Dict[str, Dict[str, Any]] = {}
    for interval in interval_list:
        report = build_shadow_report(symbols=normalized_symbols, interval=interval, news_context=news_context)
        report_md = render_shadow_report_markdown(report)

        report_json_path = run_dir / f"shadow_compare_{interval}.json"
        report_md_path = run_dir / f"shadow_compare_{interval}.md"

        report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report_md_path.write_text(report_md, encoding="utf-8")
        reports_by_interval[str(interval).lower()] = report

        append_shadow_history(report, history_path)
        interval_reports.append(
            {
                "interval": interval,
                "report_json": str(report_json_path),
                "report_markdown": str(report_md_path),
                "summary": {
                    "total_symbols": int(report.get("total_symbols") or 0),
                    "success_symbols": int(report.get("success_symbols") or 0),
                    "failed_symbols": int(report.get("failed_symbols") or 0),
                    "agreement_rate_pct": _to_float(report.get("agreement_rate_pct")),
                    "avg_direction_delta": _to_float(report.get("avg_direction_delta")),
                },
            }
        )

    history_rows = load_shadow_history(history_path)
    weekly_summary = build_weekly_shadow_summary(
        history_rows,
        lookback_days=weekly_lookback_days,
        agreement_alert_threshold_pct=agreement_alert_threshold_pct,
    )
    weekly_summary_md = render_weekly_shadow_markdown(weekly_summary)

    weekly_json_path = run_dir / "shadow_weekly_summary.json"
    weekly_md_path = run_dir / "shadow_weekly_summary.md"
    dashboard_html_path = run_dir / "shadow_dashboard.html"
    dashboard_html_ar_path = run_dir / "shadow_dashboard_ar.html"
    dashboard_html_en_path = run_dir / "shadow_dashboard_en.html"
    latest_dashboard_html_path = output_root / "shadow_latest.html"
    latest_dashboard_html_ar_path = output_root / "shadow_latest_ar.html"
    latest_dashboard_html_en_path = output_root / "shadow_latest_en.html"
    weekly_json_path.write_text(json.dumps(weekly_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    weekly_md_path.write_text(weekly_summary_md, encoding="utf-8")

    batch_summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "run_id": run_id,
        "run_dir": str(run_dir),
        "history_path": str(history_path),
        "policy": policy,
        "symbols": normalized_symbols,
        "intervals": interval_list,
        "interval_reports": interval_reports,
        "weekly_summary_json": str(weekly_json_path),
        "weekly_summary_markdown": str(weekly_md_path),
    }

    summary_json_path = run_dir / "batch_summary.json"
    summary_json_path.write_text(json.dumps(batch_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    dashboard_html_ar = render_shadow_static_html(
        batch_summary=batch_summary,
        weekly_summary=weekly_summary,
        reports_by_interval=reports_by_interval,
        lang="ar",
    )
    dashboard_html_en = render_shadow_static_html(
        batch_summary=batch_summary,
        weekly_summary=weekly_summary,
        reports_by_interval=reports_by_interval,
        lang="en",
    )
    dashboard_html_path.write_text(dashboard_html_ar, encoding="utf-8")
    dashboard_html_ar_path.write_text(dashboard_html_ar, encoding="utf-8")
    dashboard_html_en_path.write_text(dashboard_html_en, encoding="utf-8")
    latest_dashboard_html_path.write_text(dashboard_html_ar, encoding="utf-8")
    latest_dashboard_html_ar_path.write_text(dashboard_html_ar, encoding="utf-8")
    latest_dashboard_html_en_path.write_text(dashboard_html_en, encoding="utf-8")

    return {
        "success": True,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "batch_summary_json": str(summary_json_path),
        "dashboard_html": str(dashboard_html_path),
        "dashboard_html_ar": str(dashboard_html_ar_path),
        "dashboard_html_en": str(dashboard_html_en_path),
        "latest_dashboard_html": str(latest_dashboard_html_path),
        "latest_dashboard_html_ar": str(latest_dashboard_html_ar_path),
        "latest_dashboard_html_en": str(latest_dashboard_html_en_path),
        "history_path": str(history_path),
        "policy": {
            "policy_id": str(policy.get("policy_id") or "dynamic-signal-policy-v1"),
            "status": str(policy.get("status") or "adopted_full"),
            "loaded": bool(policy.get("loaded", False)),
            "source": str(policy.get("source") or ""),
        },
        "interval_reports": interval_reports,
        "weekly_summary": {
            "run_count": int(weekly_summary.get("run_count") or 0),
            "avg_agreement_rate_pct": _to_float(weekly_summary.get("avg_agreement_rate_pct")),
            "avg_direction_delta": _to_float(weekly_summary.get("avg_direction_delta")),
            "alerts_count": len(weekly_summary.get("alerts") or []),
        },
    }

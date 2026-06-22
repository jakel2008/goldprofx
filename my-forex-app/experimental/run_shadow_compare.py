from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare official vs experimental decision engines in shadow mode.")
    parser.add_argument("--symbols", default="XAUUSD,EURUSD,GBPUSD,BTCUSD", help="Comma-separated symbol list")
    parser.add_argument("--interval", default="1h", help="Requested interval for official engine")
    parser.add_argument("--minutes-to-event", type=int, default=None, help="Minutes before/after event")
    parser.add_argument("--impact", choices=["low", "medium", "high"], default="low", help="Economic event impact")
    parser.add_argument("--surprise", type=float, default=0.0, help="News surprise ratio")
    parser.add_argument("--output-dir", default="experimental/reports", help="Directory to store compare outputs")
    parser.add_argument("--history-path", default="experimental/reports/shadow_history.jsonl", help="JSONL file path for historical shadow snapshots")
    parser.add_argument("--weekly-lookback-days", type=int, default=7, help="Lookback window in days for weekly summary")
    parser.add_argument("--agreement-alert-threshold", type=float, default=25.0, help="Alert threshold for agreement rate percent")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        from experimental.shadow_compare import build_shadow_report, render_shadow_report_markdown
        from experimental.history_store import (
            append_shadow_history,
            build_weekly_shadow_summary,
            load_shadow_history,
            render_weekly_shadow_markdown,
        )
    except ModuleNotFoundError as exc:
        result = {
            "success": False,
            "error": f"Missing dependency: {exc}",
            "hint": "Install project dependencies, then retry. Example: pip install pandas yfinance",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    symbols = [item.strip().upper() for item in str(args.symbols or "").split(",") if item.strip()]
    if not symbols:
        print(json.dumps({"success": False, "error": "No symbols provided."}, ensure_ascii=False, indent=2))
        return

    news_context = {
        "minutes_to_event": args.minutes_to_event,
        "impact": args.impact,
        "surprise_ratio": args.surprise,
    }
    if args.minutes_to_event is None and args.surprise == 0.0 and args.impact == "low":
        news_context = None

    report = build_shadow_report(symbols=symbols, interval=args.interval, news_context=news_context)
    report_md = render_shadow_report_markdown(report)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "shadow_compare_report.json"
    md_path = output_dir / "shadow_compare_report.md"
    weekly_json_path = output_dir / "shadow_weekly_summary.json"
    weekly_md_path = output_dir / "shadow_weekly_summary.md"
    history_path = Path(args.history_path)

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(report_md, encoding="utf-8")

    append_shadow_history(report, history_path)
    history_rows = load_shadow_history(history_path)
    weekly_summary = build_weekly_shadow_summary(
        history_rows,
        lookback_days=args.weekly_lookback_days,
        agreement_alert_threshold_pct=args.agreement_alert_threshold,
    )
    weekly_summary_md = render_weekly_shadow_markdown(weekly_summary)

    weekly_json_path.write_text(json.dumps(weekly_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    weekly_md_path.write_text(weekly_summary_md, encoding="utf-8")

    console = {
        "success": True,
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "history_jsonl": str(history_path),
        "weekly_summary_json": str(weekly_json_path),
        "weekly_summary_markdown": str(weekly_md_path),
        "summary": {
            "total_symbols": report.get("total_symbols"),
            "success_symbols": report.get("success_symbols"),
            "failed_symbols": report.get("failed_symbols"),
            "agreement_rate_pct": report.get("agreement_rate_pct"),
            "weekly_run_count": weekly_summary.get("run_count"),
            "weekly_avg_agreement_rate_pct": weekly_summary.get("avg_agreement_rate_pct"),
            "weekly_alerts_count": len(weekly_summary.get("alerts") or []),
        },
    }
    print(json.dumps(console, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

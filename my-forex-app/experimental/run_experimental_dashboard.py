from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run experimental dashboard across multiple symbols.")
    parser.add_argument("--symbols", default="XAUUSD,EURUSD,GBPUSD,BTCUSD", help="Comma-separated symbol list")
    parser.add_argument("--interval", default="1h", help="Preferred interval")
    parser.add_argument("--minutes-to-event", type=int, default=None, help="Minutes before/after scheduled event")
    parser.add_argument("--impact", choices=["low", "medium", "high"], default="low", help="Economic event impact")
    parser.add_argument("--surprise", type=float, default=0.0, help="News surprise ratio")
    parser.add_argument("--output-dir", default="experimental/reports", help="Directory to store dashboard outputs")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        from experimental.decision_engine import evaluate_experimental_decision
        from experimental.dashboard import aggregate_dashboard, render_dashboard_markdown
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

    raw_results = []
    for symbol in symbols:
        result = evaluate_experimental_decision(
            symbol=symbol,
            preferred_interval=args.interval,
            news_context=news_context,
        )
        raw_results.append(result)

    dashboard = aggregate_dashboard(raw_results)
    report_md = render_dashboard_markdown(dashboard)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "experimental_dashboard.json"
    md_path = output_dir / "experimental_dashboard.md"

    json_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(report_md, encoding="utf-8")

    console = {
        "success": True,
        "dashboard_json": str(json_path),
        "dashboard_markdown": str(md_path),
        "summary": {
            "total_symbols": dashboard.get("total_symbols"),
            "success_symbols": dashboard.get("success_symbols"),
            "failed_symbols": dashboard.get("failed_symbols"),
            "avg_final_score": dashboard.get("avg_final_score"),
        },
    }
    print(json.dumps(console, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run isolated experimental decision scoring.")
    parser.add_argument("--symbol", default="XAUUSD", help="Market symbol, e.g. XAUUSD")
    parser.add_argument("--interval", default="1h", help="Preferred interval")
    parser.add_argument("--minutes-to-event", type=int, default=None, help="Minutes before (positive) or after (negative) event")
    parser.add_argument("--impact", choices=["low", "medium", "high"], default="low", help="Economic event impact")
    parser.add_argument("--surprise", type=float, default=0.0, help="News surprise ratio, e.g. 1.2 or -0.8")
    parser.add_argument("--report-path", default="", help="Optional JSON output path for the run report")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        from experimental.decision_engine import evaluate_experimental_decision
    except ModuleNotFoundError as exc:
        result = {
            "success": False,
            "error": f"Missing dependency: {exc}",
            "hint": "Install project dependencies, then retry. Example: pip install pandas yfinance",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    news_context = {
        "minutes_to_event": args.minutes_to_event,
        "impact": args.impact,
        "surprise_ratio": args.surprise,
    }
    if args.minutes_to_event is None and args.surprise == 0.0 and args.impact == "low":
        news_context = None

    result = evaluate_experimental_decision(
        symbol=args.symbol,
        preferred_interval=args.interval,
        news_context=news_context,
    )

    report_path = str(args.report_path or "").strip()
    if report_path:
        path_obj = Path(report_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

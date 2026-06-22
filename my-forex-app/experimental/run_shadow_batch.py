from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run batch shadow comparisons across multiple intervals.")
    parser.add_argument("--symbols", default="XAUUSD,EURUSD,GBPUSD,BTCUSD", help="Comma-separated symbol list")
    parser.add_argument("--intervals", default="5m,15m,30m,1h,4h,1d", help="Comma-separated intervals")
    parser.add_argument("--minutes-to-event", type=int, default=None, help="Minutes before/after event")
    parser.add_argument("--impact", choices=["low", "medium", "high"], default="low", help="Economic event impact")
    parser.add_argument("--surprise", type=float, default=0.0, help="News surprise ratio")
    parser.add_argument("--output-dir", default="experimental/reports", help="Directory to store batch outputs")
    parser.add_argument("--history-path", default="experimental/reports/shadow_history.jsonl", help="History jsonl path")
    parser.add_argument("--weekly-lookback-days", type=int, default=7, help="Lookback window in days")
    parser.add_argument("--agreement-alert-threshold", type=float, default=25.0, help="Alert threshold for agreement rate percent")
    parser.add_argument("--policy-path", default="experimental/dynamic_signal_policy.json", help="Dynamic policy json path")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        from experimental.shadow_batch import run_shadow_batch
    except ModuleNotFoundError as exc:
        result = {
            "success": False,
            "error": f"Missing dependency: {exc}",
            "hint": "Install project dependencies, then retry. Example: pip install pandas yfinance",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    symbols = [item.strip().upper() for item in str(args.symbols or "").split(",") if item.strip()]
    intervals = [item.strip().lower() for item in str(args.intervals or "").split(",") if item.strip()]

    news_context = {
        "minutes_to_event": args.minutes_to_event,
        "impact": args.impact,
        "surprise_ratio": args.surprise,
    }
    if args.minutes_to_event is None and args.surprise == 0.0 and args.impact == "low":
        news_context = None

    result = run_shadow_batch(
        symbols=symbols,
        intervals=intervals,
        output_root=Path(args.output_dir),
        history_path=Path(args.history_path),
        weekly_lookback_days=args.weekly_lookback_days,
        agreement_alert_threshold_pct=args.agreement_alert_threshold,
        news_context=news_context,
        policy_path=Path(args.policy_path),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from recommendations_engine import ALL_AVAILABLE_PAIRS  # type: ignore
from experimental.shadow_batch import run_shadow_batch


def _all_symbols() -> list[str]:
    symbols: list[str] = []
    for group in ALL_AVAILABLE_PAIRS.values():
        symbols.extend(str(s).upper() for s in group.keys())
    return sorted(set(symbols))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run shadow batch continuously for live page updates.")
    p.add_argument("--interval-seconds", type=int, default=180, help="Seconds between runs")
    p.add_argument("--symbols", default="", help="Comma-separated symbols; empty means all")
    p.add_argument("--timeframes", default="5m,15m,30m,1h,4h,1d", help="Comma-separated intervals")
    p.add_argument("--output-dir", default="my-forex-app/experimental/reports", help="Output folder")
    return p


def main() -> None:
    args = _build_parser().parse_args()

    symbols = [s.strip().upper() for s in str(args.symbols or "").split(",") if s.strip()] or _all_symbols()
    intervals = [t.strip().lower() for t in str(args.timeframes or "").split(",") if t.strip()]
    output_root = Path(args.output_dir)
    history_path = output_root / "shadow_history.jsonl"

    print("=" * 60)
    print("[SHADOW_LIVE] live generation started")
    print(f"[SHADOW_LIVE] symbols={len(symbols)} intervals={intervals}")
    print(f"[SHADOW_LIVE] refresh every {int(args.interval_seconds)}s")
    print("=" * 60)

    while True:
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = run_shadow_batch(
                symbols=symbols,
                intervals=intervals,
                output_root=output_root,
                history_path=history_path,
                weekly_lookback_days=7,
                agreement_alert_threshold_pct=25.0,
                news_context=None,
            )
            print(json.dumps({
                "ts": started,
                "success": result.get("success"),
                "run_id": result.get("run_id"),
                "latest_ar": result.get("latest_dashboard_html_ar"),
                "latest_en": result.get("latest_dashboard_html_en"),
            }, ensure_ascii=False))
        except KeyboardInterrupt:
            print("\n[SHADOW_LIVE] stopped by user")
            return
        except Exception as exc:
            print(json.dumps({"ts": started, "success": False, "error": str(exc)}, ensure_ascii=False))

        time.sleep(max(15, int(args.interval_seconds)))


if __name__ == "__main__":
    main()

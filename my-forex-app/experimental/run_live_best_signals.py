from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
	std_path = str(PROJECT_ROOT)
	if std_path not in sys.path:
		sys.path.insert(0, std_path)
if str(APP_ROOT) not in sys.path:
	sys.path.insert(0, str(APP_ROOT))

from recommendations_engine import ALL_AVAILABLE_PAIRS  # type: ignore
from experimental.economic_calendar import load_calendar_events_cached
from experimental.shadow_compare import build_shadow_report
LIVE_SIGNAL_FILE = PROJECT_ROOT / "signals" / "live_best_signals.json"


def _all_symbols() -> list[str]:
	symbols: list[str] = []
	for group in ALL_AVAILABLE_PAIRS.values():
		symbols.extend(str(symbol).upper() for symbol in group.keys())
	return sorted(set(symbols))


def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Continuously analyze and broadcast the best live signals.")
	parser.add_argument("--symbols", default="", help="Comma-separated symbols; empty means all available")
	parser.add_argument("--intervals", default="5m,15m,30m,1h,4h,1d", help="Comma-separated intervals to evaluate")
	parser.add_argument("--max-signals", type=int, default=5, help="Maximum number of signals to keep per cycle")
	parser.add_argument("--min-quality", type=int, default=70, help="Minimum quality score required for broadcast")
	parser.add_argument("--interval-seconds", type=int, default=300, help="Seconds between analysis cycles")
	parser.add_argument("--broadcast", action="store_true", help="Broadcast immediately after each analysis cycle")
	parser.add_argument("--signal-file", default=str(LIVE_SIGNAL_FILE), help="Output JSON file for live signals")
	parser.add_argument("--signal-prefix", default="live_best_", help="Filename prefix used by the broadcaster")
	return parser


def _normalize_recommendation(value: Any) -> str:
	text = str(value or "").strip().lower()
	if "buy" in text or "شراء" in text:
		return "buy"
	if "sell" in text or "بيع" in text:
		return "sell"
	return "wait"


def _quality_score(item: dict[str, Any]) -> int:
	official = item.get("official") or {}
	experimental = item.get("experimental") or {}
	comparison = item.get("comparison") or {}

	official_rec = str(official.get("normalized_recommendation") or "wait")
	experimental_rec = str(experimental.get("normalized_recommendation") or "wait")
	experimental_score = abs(float(experimental.get("final_score") or 0.0))
	official_gap = abs(float(official.get("score_gap") or 0.0))
	agreement_bonus = 15 if comparison.get("agreement") else 0
	same_interval_bonus = 5 if comparison.get("same_interval") else 0
	non_wait_bonus = 10 if official_rec != "wait" and experimental_rec != "wait" else 0
	news_penalty = 25 if experimental.get("news_blocked") else 0
	source_bonus = 5 if (official.get("market_data_source") or comparison.get("market_data_source")) else 0

	score = (experimental_score * 12.0) + (official_gap * 3.0) + agreement_bonus + same_interval_bonus + non_wait_bonus + source_bonus - news_penalty
	return max(0, min(100, int(round(score))))


def _build_signal_payload(item: dict[str, Any], quality_score: int, cycle_id: str) -> dict[str, Any] | None:
	official = item.get("official") or {}
	experimental = item.get("experimental") or {}
	experimental_rec = _normalize_recommendation(experimental.get("normalized_recommendation"))
	official_rec = _normalize_recommendation(official.get("normalized_recommendation"))
	final_recommendation = experimental_rec if experimental_rec != "wait" else official_rec
	if final_recommendation == "wait":
		return None

	entry = official.get("entry_point") or experimental.get("entry_price")
	stop_loss = official.get("stop_loss")
	tp1 = official.get("take_profit_1") or official.get("take_profit1")
	tp2 = official.get("take_profit_2") or official.get("take_profit2")
	tp3 = official.get("take_profit_3") or official.get("take_profit3")
	if entry is None or stop_loss is None or tp1 is None:
		return None

	symbol = str(item.get("symbol") or "").upper()
	trade_type = "buy" if final_recommendation == "buy" else "sell"
	market_data_source = official.get("market_data_source") or experimental.get("market_data_source") or item.get("market_data_source") or "unknown"
	status_reason = "صالح للبث في هذه الدورة"
	signal_status = "مستمرة"
	if experimental.get("news_blocked"):
		signal_status = "متوقفة"
		status_reason = "موقوفة بسبب الأخبار أو التقويم الاقتصادي"
	elif quality_score < 70:
		signal_status = "متوقفة"
		status_reason = "الجودة أقل من الحد الأدنى المطلوب"
	elif final_recommendation == "wait":
		signal_status = "متوقفة"
		status_reason = "لا توجد أفضلية اتجاهية واضحة"

	return {
		"trade_id": f"{cycle_id}_{symbol}_{item.get('interval_requested') or item.get('interval') or 'na'}",
		"symbol": symbol,
		"pair": symbol,
		"signal_type": trade_type,
		"signal": trade_type,
		"trade_type": trade_type,
		"entry_price": float(entry),
		"entry": float(entry),
		"stop_loss": float(stop_loss),
		"sl": float(stop_loss),
		"take_profit_1": float(tp1),
		"take_profit_2": float(tp2) if tp2 is not None else float(tp1),
		"take_profit_3": float(tp3) if tp3 is not None else float(tp1),
		"tp1": float(tp1),
		"tp2": float(tp2) if tp2 is not None else float(tp1),
		"tp3": float(tp3) if tp3 is not None else float(tp1),
		"quality_score": int(quality_score),
		"confidence": str(official.get("confidence") or experimental.get("confidence") or "MEDIUM").upper(),
		"interval": str(item.get("interval_requested") or item.get("interval") or "1h"),
		"chosen_interval": str(experimental.get("chosen_interval") or item.get("interval_requested") or "1h"),
		"chosen_horizon": str(experimental.get("chosen_horizon") or "-"),
		"official_recommendation": str(official.get("normalized_recommendation") or "wait"),
		"experimental_recommendation": str(experimental.get("normalized_recommendation") or "wait"),
		"agreement": bool((item.get("comparison") or {}).get("agreement")),
		"final_score": float(experimental.get("final_score") or 0.0),
		"score_gap": float(official.get("score_gap") or 0.0),
		"market_data_source": market_data_source,
		"news_blocked": bool(experimental.get("news_blocked")),
		"signal_status": signal_status,
		"signal_status_reason": status_reason,
		"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
	}


def _ranked_signals(report: dict[str, Any], max_signals: int, min_quality: int, cycle_id: str) -> list[dict[str, Any]]:
	candidates: list[dict[str, Any]] = []
	for item in report.get("results") or []:
		if not item.get("success"):
			continue
		quality_score = _quality_score(item)
		if quality_score < min_quality:
			continue
		payload = _build_signal_payload(item, quality_score, cycle_id)
		if payload:
			candidates.append(payload)

	candidates.sort(
		key=lambda row: (
			int(row.get("quality_score") or 0),
			1 if row.get("agreement") else 0,
			abs(float(row.get("final_score") or 0.0)),
			abs(float(row.get("score_gap") or 0.0)),
		),
		reverse=True,
	)
	return candidates[: max(1, int(max_signals))]


def _write_live_signals(path: Path, signals: list[dict[str, Any]], summary: dict[str, Any]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	payload = {
		"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
		"summary": summary,
		"signals": signals,
	}
	path.write_text(json.dumps(payload["signals"], ensure_ascii=False, indent=2), encoding="utf-8")



def main() -> None:
	args = _build_parser().parse_args()
	all_symbols = [item.strip().upper() for item in str(args.symbols or "").split(",") if item.strip()] or _all_symbols()
	intervals = [item.strip().lower() for item in str(args.intervals or "").split(",") if item.strip()]
	output_path = Path(args.signal_file)
	cycle = 0

	print("=" * 60)
	print("[LIVE_SIGNALS] continuous analysis + broadcast started")
	print(f"[LIVE_SIGNALS] symbols={len(all_symbols)} intervals={intervals}")
	print(f"[LIVE_SIGNALS] max_signals={int(args.max_signals)} min_quality={int(args.min_quality)}")
	print(f"[LIVE_SIGNALS] signal_file={output_path}")
	print(f"[LIVE_SIGNALS] signal_prefix={args.signal_prefix}")
	print(f"[LIVE_SIGNALS] broadcast={bool(args.broadcast)}")
	print("=" * 60)

	os.environ.setdefault("SIGNAL_FILE_PREFIX", str(args.signal_prefix))
	from signal_broadcaster import read_and_broadcast_signals

	while True:
		cycle += 1
		started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
		try:
			news_context = load_calendar_events_cached()
			report_per_interval: list[dict[str, Any]] = []
			all_ranked: list[dict[str, Any]] = []

			for interval in intervals:
				report = build_shadow_report(symbols=all_symbols, interval=interval, news_context=news_context)
				report_per_interval.append(
					{
						"interval": interval,
						"success_symbols": report.get("success_symbols"),
						"failed_symbols": report.get("failed_symbols"),
						"agreement_rate_pct": report.get("agreement_rate_pct"),
						"avg_direction_delta": report.get("avg_direction_delta"),
					}
				)
				all_ranked.extend(_ranked_signals(report, max_signals=args.max_signals, min_quality=args.min_quality, cycle_id=f"cycle{cycle}"))

			all_ranked.sort(
				key=lambda row: (
					int(row.get("quality_score") or 0),
					1 if row.get("agreement") else 0,
					abs(float(row.get("final_score") or 0.0)),
					abs(float(row.get("score_gap") or 0.0)),
				),
				reverse=True,
			)
			best_signals = all_ranked[: max(1, int(args.max_signals))]
			for signal in best_signals:
				signal["signal_status"] = str(signal.get("signal_status") or "مستمرة")
				signal["signal_status_reason"] = str(signal.get("signal_status_reason") or "صالح للبث في هذه الدورة")
				signal["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=int(args.interval_seconds))).strftime("%Y-%m-%d %H:%M:%S UTC")
				signal["valid_for_seconds"] = int(args.interval_seconds)
			_write_live_signals(
				output_path,
				best_signals,
				{
					"cycle": cycle,
					"started_at": started,
					"symbols": len(all_symbols),
					"intervals": intervals,
					"candidates": len(all_ranked),
					"selected": len(best_signals),
					"interval_reports": report_per_interval,
				},
			)

			print(json.dumps({
				"cycle": cycle,
				"started_at": started,
				"selected": len(best_signals),
				"top": [f"{item.get('symbol')}:{item.get('signal_type')}@{item.get('quality_score')}" for item in best_signals],
			}, ensure_ascii=False))

			if args.broadcast:
				broadcasted = read_and_broadcast_signals()
				print(json.dumps({"cycle": cycle, "broadcasted": broadcasted}, ensure_ascii=False))
		except KeyboardInterrupt:
			print("\n[LIVE_SIGNALS] stopped by user")
			return
		except Exception as exc:
			print(json.dumps({"cycle": cycle, "started_at": started, "success": False, "error": str(exc)}, ensure_ascii=False))

		time.sleep(max(15, int(args.interval_seconds)))


if __name__ == "__main__":
	main()

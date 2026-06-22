import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto trader health checker")
    parser.add_argument("--log", default="auto_trader_live.out.log", help="Path to trader output log")
    parser.add_argument("--health-log", default="auto_trader_health.log", help="Path to health monitor log")
    parser.add_argument("--window-min", type=int, default=10, help="Success lookback window in minutes")
    parser.add_argument("--interval-sec", type=int, default=300, help="Health check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run one check and exit")
    return parser.parse_args()


def parse_json_lines(file_path: Path) -> list[dict]:
    if not file_path.exists():
        return []
    rows: list[dict] = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            text = line.strip()
            if not text.startswith("{"):
                continue
            try:
                rows.append(json.loads(text))
            except Exception:
                continue
    return rows


def collect_events(entries: list[dict]) -> list[dict]:
    events: list[dict] = []
    for entry in entries:
        scan_time = entry.get("time")
        actions = entry.get("actions") if isinstance(entry.get("actions"), list) else []
        for action in actions:
            if not isinstance(action, dict):
                continue
            row = dict(action)
            row["scan_time"] = scan_time
            events.append(row)
    return events


def parse_local_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def evaluate_health(events: list[dict], window_min: int) -> dict:
    now = datetime.now()
    cutoff = now - timedelta(minutes=max(1, window_min))

    recent = []
    for event in events:
        dt = parse_local_time(event.get("scan_time"))
        if dt and dt >= cutoff:
            recent.append(event)

    success = [e for e in recent if e.get("event") == "execute_signal" and bool(e.get("success"))]
    failed = [e for e in recent if e.get("event") == "execute_signal" and not bool(e.get("success"))]

    status = "healthy" if success else "warning"
    summary = {
        "checked_at": now.isoformat(timespec="seconds"),
        "status": status,
        "window_minutes": max(1, window_min),
        "recent_execute_success": len(success),
        "recent_execute_failed": len(failed),
    }

    if failed:
        last_fail = failed[-1]
        summary["last_failure_symbol"] = last_fail.get("symbol")
        summary["last_failure_interval"] = last_fail.get("interval")
        summary["last_failure_error"] = last_fail.get("error")

    return summary


def append_health_log(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_once(log_path: Path, health_log_path: Path, window_min: int) -> int:
    entries = parse_json_lines(log_path)
    events = collect_events(entries)
    result = evaluate_health(events, window_min)
    append_health_log(health_log_path, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main() -> int:
    args = parse_args()
    log_path = Path(args.log)
    health_log_path = Path(args.health_log)

    if args.once:
        return run_once(log_path, health_log_path, args.window_min)

    while True:
        run_once(log_path, health_log_path, args.window_min)
        time.sleep(max(30, int(args.interval_sec)))


if __name__ == "__main__":
    raise SystemExit(main())

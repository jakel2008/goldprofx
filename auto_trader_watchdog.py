import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_log(log_path: Path, payload: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restart continuous_auto_trader.py if it exits")
    parser.add_argument("--config", required=True, help="Path to account config JSON")
    parser.add_argument("--state", required=True, help="Path to runtime state JSON")
    parser.add_argument("--wallet-config", required=True, help="Path to MT5 wallet config JSON")
    parser.add_argument("--account-id", required=True, help="Account id for lock namespacing")
    parser.add_argument("--restart-delay", type=float, default=5.0, help="Seconds to wait before restart")
    parser.add_argument("--log", default="", help="Path to watchdog JSONL log")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    log_path = Path(args.log) if args.log else PROJECT_ROOT / "accounts" / args.account_id / "trader_watchdog.jsonl"
    trader_path = PROJECT_ROOT / "continuous_auto_trader.py"

    command = [
        sys.executable,
        "-u",
        str(trader_path),
        "--config",
        args.config,
        "--state",
        args.state,
        "--wallet-config",
        args.wallet_config,
        "--account-id",
        args.account_id,
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    restart_count = 0
    _write_log(log_path, {"event": "watchdog_started", "time": _timestamp(), "account_id": args.account_id})

    while True:
        started_at = _timestamp()
        _write_log(
            log_path,
            {
                "event": "trader_start",
                "time": started_at,
                "account_id": args.account_id,
                "restart_count": restart_count,
            },
        )

        process = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        if process.stdout is not None:
            for line in process.stdout:
                line = line.rstrip("\n")
                if line:
                    print(line, flush=True)
                    _write_log(log_path, {"event": "trader_output", "time": _timestamp(), "line": line})

        exit_code = process.wait()
        _write_log(
            log_path,
            {
                "event": "trader_exit",
                "time": _timestamp(),
                "account_id": args.account_id,
                "exit_code": exit_code,
                "restart_count": restart_count,
            },
        )

        restart_count += 1
        time.sleep(max(1.0, float(args.restart_delay)))


if __name__ == "__main__":
    raise SystemExit(main())
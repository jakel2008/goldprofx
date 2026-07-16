"""Run the website signal generator continuously for the selected wallet symbols.

This runner keeps `vip_signals.db` fresh for the site-db auto trader without
starting the Flask server or Telegram command bot.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "accounts" / "account1_gold" / "config.json"


def _clean_symbol(value: object) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum() or ch == "*")


def _load_account_settings(config_path: Path) -> dict:
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        config = {}

    symbols = [_clean_symbol(item) for item in config.get("symbols", [])]
    symbols = [symbol for symbol in symbols if symbol and symbol != "*"]
    if not symbols:
        symbols = ["XAUUSD"]

    max_age_minutes = max(1, int(config.get("site_signals_max_age_minutes") or 1))
    return {
        "symbols": symbols,
        "max_age_minutes": max_age_minutes,
        "min_quality": int(config.get("site_signals_min_quality") or 0),
    }


def _prepare_environment(settings: dict) -> None:
    os.environ.setdefault("BACKGROUND_SERVICES_ENABLED", "0")
    os.environ.setdefault("TELEGRAM_COMMAND_BOT_ENABLED", "0")
    os.environ.setdefault("VIP_SIGNALS_DB_PATH", "vip_signals.db")
    os.environ["CONTINUOUS_ANALYZER_SYMBOLS"] = ",".join(settings["symbols"])
    os.environ["ACTIVE_SIGNAL_BLOCK_MINUTES"] = str(settings["max_age_minutes"])


class _SilentTelegramSender:
    @staticmethod
    def send_signal_to_subscribers(*_args, **_kwargs) -> dict:
        return {"sent_count": 0, "failed_count": 0, "skipped": True}

    @staticmethod
    def format_signal_message(_signal_data: dict) -> str:
        return ""

    @staticmethod
    def send_broadcast_to_configured_targets(*_args, **_kwargs) -> dict:
        return {"sent_count": 0, "failed_count": 0, "skipped": True}


def _run_cycle(web_app_complete, config_path: Path) -> dict:
    settings = _load_account_settings(config_path)
    web_app_complete.CONTINUOUS_ANALYZER_SYMBOLS = settings["symbols"]
    web_app_complete.ACTIVE_SIGNAL_BLOCK_MINUTES = settings["max_age_minutes"]
    web_app_complete.telegram_sender = _SilentTelegramSender()

    result = web_app_complete._run_continuous_analyzer_once(interval="1h", force_live=True)
    return {
        "event": "site_signal_generator_cycle",
        "time": datetime.now().isoformat(timespec="seconds"),
        "symbols": settings["symbols"],
        "max_age_minutes": settings["max_age_minutes"],
        "min_quality": settings["min_quality"],
        "success": bool(result.get("success")),
        "analyzed_count": result.get("analyzed_count"),
        "generated_count": result.get("generated_count"),
        "failed_count": result.get("failed_count"),
        "details": result.get("details", [])[:8],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuously generate fresh site DB signals for the selected wallet symbols.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Account config JSON path")
    parser.add_argument("--interval-seconds", type=int, default=45, help="Seconds between cycle starts")
    parser.add_argument("--once", action="store_true", help="Run a single generation cycle and exit")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    initial_settings = _load_account_settings(config_path)
    _prepare_environment(initial_settings)

    import web_app_complete  # noqa: PLC0415

    interval_seconds = max(15, int(args.interval_seconds or 45))
    while True:
        cycle_started = time.monotonic()
        try:
            summary = _run_cycle(web_app_complete, config_path)
        except Exception as exc:
            summary = {
                "event": "site_signal_generator_error",
                "time": datetime.now().isoformat(timespec="seconds"),
                "error": str(exc),
            }

        print(json.dumps(summary, ensure_ascii=False), flush=True)
        if args.once:
            return 0 if summary.get("success", False) else 1

        elapsed = time.monotonic() - cycle_started
        time.sleep(max(1.0, interval_seconds - elapsed))


if __name__ == "__main__":
    raise SystemExit(main())
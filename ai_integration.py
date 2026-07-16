from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class _FallbackEngine:
    def generate_signal(self, symbol: str, yf_symbol: str) -> Optional[dict[str, Any]]:
        return None

    def format_signal_message(self, signal: Optional[dict[str, Any]]) -> str:
        if signal is None:
            return "لا توجد إشارة قوية حالياً"
        return f"إشارة AI: {signal.get('symbol', 'N/A')}"


def _create_engine() -> Any:
    try:
        from advanced_signal_engine import AdvancedSignalEngine  # type: ignore

        return AdvancedSignalEngine()
    except Exception:
        return _FallbackEngine()


def build_ai_signal_payload(
    symbol: str,
    yf_symbol: Optional[str] = None,
    engine: Optional[Any] = None,
    analysis_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Build a structured AI signal payload for the given symbol."""
    normalized_symbol = str(symbol or "").strip().upper()
    normalized_yf = (yf_symbol or normalized_symbol).strip()

    if engine is None:
        engine = _create_engine()

    signal = None
    message = "لا توجد إشارة قوية حالياً"

    try:
        signal = engine.generate_signal(normalized_symbol, normalized_yf)
        if signal:
            message = engine.format_signal_message(signal)
    except Exception as exc:  # pragma: no cover - defensive path
        message = f"خطأ في إنشاء الإشارة: {exc}"

    payload: dict[str, Any] = {
        "status": "ok" if signal else "empty",
        "symbol": normalized_symbol,
        "yf_symbol": normalized_yf,
        "signal": signal,
        "message": message,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if analysis_dir is not None and signal:
        try:
            analysis_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = analysis_dir / f"ai_signal_{normalized_symbol}_{stamp}.json"
            with output_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            payload["saved_to"] = str(output_path)
        except Exception:
            payload["saved_to"] = None

    return payload

import tempfile
import unittest
from pathlib import Path

from ai_integration import build_ai_signal_payload


class StubEngine:
    def generate_signal(self, symbol, yf_symbol):
        return {
            "symbol": symbol,
            "yf_symbol": yf_symbol,
            "direction": "buy",
            "quality_score": 85,
            "confidence": 0.85,
            "entry": 1.1000,
            "stop_loss": 1.0900,
            "tp1": 1.1200,
            "tp2": 1.1300,
            "tp3": 1.1400,
        }

    def format_signal_message(self, signal):
        return f"AI signal for {signal['symbol']}"


class AiIntegrationTests(unittest.TestCase):
    def test_build_ai_signal_payload_returns_structured_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = build_ai_signal_payload(
                symbol="EURUSD",
                yf_symbol="EURUSD=X",
                engine=StubEngine(),
                analysis_dir=Path(tmpdir),
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["symbol"], "EURUSD")
            self.assertEqual(payload["signal"]["direction"], "buy")
            self.assertIn("AI signal", payload["message"])


if __name__ == "__main__":
    unittest.main()

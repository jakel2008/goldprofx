from pathlib import Path
import sys

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

try:
    from services.advanced_analyzer_engine import perform_full_analysis
except (ImportError, AttributeError) as exc:
    perform_full_analysis = None
    ANALYZER_IMPORT_ERROR = exc
else:
    ANALYZER_IMPORT_ERROR = None


DEFAULT_SYMBOL = "EURUSD"
DEFAULT_INTERVAL = "1h"


def get_signals(symbol=DEFAULT_SYMBOL, interval=DEFAULT_INTERVAL):
    """Return a structured analysis payload for the requested symbol and interval."""
    if perform_full_analysis is None:
        return {
            'success': False,
            'symbol': symbol,
            'interval': interval,
            'error': str(ANALYZER_IMPORT_ERROR),
            'signals': [],
        }

    return perform_full_analysis(symbol, interval)

def display_strong_signals(symbol, interval):
    """Fetch and display strong trading signals for the given symbol and interval."""
    result = get_signals(symbol, interval)
    
    if not result['success']:
        return f"Error fetching strong signals: {result['error']}"
    
    strong_signals = []
    for signal in result['signals']:
        if "قوي" in signal or "شراء قوي" in signal or "بيع قوي" in signal:
            strong_signals.append(signal)
    
    if not strong_signals:
        return "لا توجد إشارات قوية حالياً."
    
    display_output = "\n".join(strong_signals)
    return f"إشارات قوية لـ {symbol} ({interval}):\n{display_output}"
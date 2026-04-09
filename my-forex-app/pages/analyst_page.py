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


def get_analyst_view(symbol=DEFAULT_SYMBOL, interval=DEFAULT_INTERVAL):
    if perform_full_analysis is None:
        return {
            'success': False,
            'symbol': symbol,
            'interval': interval,
            'error': str(ANALYZER_IMPORT_ERROR),
        }

    result = perform_full_analysis(symbol, interval)
    if not result.get('success'):
        return result

    return {
        'success': True,
        'symbol': result['symbol'],
        'symbol_label': result['symbol_label'],
        'interval': result['interval'],
        'analyst_report': result.get('analyst_report'),
        'executive_summary': result.get('executive_summary'),
        'scenario': result.get('scenario'),
        'scenario_horizons': result.get('scenario_horizons'),
        'technical': result.get('technical'),
        'recommendation': result.get('recommendation'),
        'buy_score': result.get('buy_score'),
        'sell_score': result.get('sell_score'),
        'fetched_at': result.get('fetched_at'),
        'error': None,
    }
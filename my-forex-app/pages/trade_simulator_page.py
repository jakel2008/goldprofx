from pathlib import Path
import sys

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

try:
    from services.trade_simulator import simulate_trade
except (ImportError, AttributeError) as exc:
    simulate_trade = None
    SIMULATOR_IMPORT_ERROR = exc
else:
    SIMULATOR_IMPORT_ERROR = None


DEFAULT_SYMBOL = 'EURUSD'
DEFAULT_INTERVAL = '1h'
DEFAULT_CAPITAL = 1000.0
DEFAULT_LEVERAGE = 100.0
DEFAULT_RISK_PERCENT = 1.0
DEFAULT_REPLAY_BARS = 24


def get_trade_simulation(
    symbol=DEFAULT_SYMBOL,
    interval=DEFAULT_INTERVAL,
    capital=DEFAULT_CAPITAL,
    leverage=DEFAULT_LEVERAGE,
    risk_percent=DEFAULT_RISK_PERCENT,
    replay_bars=DEFAULT_REPLAY_BARS,
):
    if simulate_trade is None:
        return {
            'success': False,
            'error': str(SIMULATOR_IMPORT_ERROR),
            'symbol': symbol,
            'interval': interval,
            'capital': capital,
            'leverage': leverage,
            'risk_percent': risk_percent,
            'replay_bars': replay_bars,
        }

    return simulate_trade(
        symbol,
        interval,
        float(capital),
        float(leverage),
        float(risk_percent),
        int(replay_bars),
    )
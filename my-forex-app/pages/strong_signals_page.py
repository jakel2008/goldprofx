from pathlib import Path
import sys
from datetime import datetime, timezone

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

try:
    from services.advanced_analyzer_engine import SUPPORTED_SYMBOLS, perform_full_analysis
except (ImportError, AttributeError):
    perform_full_analysis = None
    ANALYZER_IMPORT_ERROR = "Analyzer service is unavailable."
    SUPPORTED_SYMBOLS = {}
else:
    ANALYZER_IMPORT_ERROR = None


DEFAULT_SYMBOL = "ALL"
DEFAULT_INTERVAL = "1h"

SYMBOL_CATEGORY_GROUPS = {
    'الأزواج الرئيسية': [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
    ],
    'الأزواج التقاطعية': [
        'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
        'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD',
        'AUDJPY', 'AUDNZD', 'AUDCAD', 'AUDCHF',
        'CADJPY', 'CADCHF', 'CHFJPY',
        'NZDJPY', 'NZDCHF', 'NZDCAD',
    ],
    'المؤشرات الأمريكية': ['US500', 'NAS100', 'US30', 'US2000'],
    'العملات المشفرة': ['BTCUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'BNBUSD'],
    'المعادن': ['XAUUSD', 'XAGUSD'],
}

SYMBOL_CATEGORY_MAP = {
    symbol: category
    for category, symbols in SYMBOL_CATEGORY_GROUPS.items()
    for symbol in symbols
}


def _normalize_symbol(symbol):
    return (symbol or "").strip().upper().replace("/", "")


def _symbols_to_scan(symbol):
    normalized_symbol = _normalize_symbol(symbol)
    if normalized_symbol in ("", "ALL"):
        return list(SUPPORTED_SYMBOLS.keys())
    if normalized_symbol in SUPPORTED_SYMBOLS:
        return [normalized_symbol]
    return []


def _symbol_category(symbol):
    return SYMBOL_CATEGORY_MAP.get(symbol, 'غير مصنف')


def fetch_strong_signals(symbol, interval):
    """Scan symbols and return only strong buy/sell signals."""
    if perform_full_analysis is None:
        return {
            'signals': [],
            'scanned_symbols': 0,
            'scan_errors': [],
        }

    symbols_to_scan = _symbols_to_scan(symbol)
    strong_signals = []
    scan_errors = []

    for current_symbol in symbols_to_scan:
        analysis_result = perform_full_analysis(current_symbol, interval)
        if not analysis_result.get('success'):
            scan_errors.append({
                'symbol': current_symbol,
                'error': analysis_result.get('error', 'Unknown scan error'),
            })
            continue

        recommendation = analysis_result['recommendation']
        if recommendation not in ["شراء قوي", "بيع قوي"]:
            continue

        score_gap = abs(analysis_result['buy_score'] - analysis_result['sell_score'])
        strong_signals.append({
            'symbol': current_symbol,
            'symbol_label': analysis_result.get('symbol_label', current_symbol),
            'category': _symbol_category(current_symbol),
            'recommendation': recommendation,
            'buy_score': analysis_result['buy_score'],
            'sell_score': analysis_result['sell_score'],
            'entry_price': analysis_result['entry_point'],
            'take_profit1': analysis_result['take_profit1'],
            'take_profit2': analysis_result['take_profit2'],
            'take_profit3': analysis_result['take_profit3'],
            'stop_loss': analysis_result['stop_loss'],
            'confidence': analysis_result['confidence'],
            'scenario': analysis_result.get('scenario'),
            'executive_summary': analysis_result.get('executive_summary'),
            'price_change_pct': analysis_result.get('price_change_pct'),
            'score_gap': score_gap,
        })

    strong_signals.sort(key=lambda item: (item['score_gap'], item['buy_score'], item['sell_score']), reverse=True)
    return {
        'signals': strong_signals,
        'scanned_symbols': len(symbols_to_scan),
        'scan_errors': scan_errors,
    }


def render_strong_signals(strong_signals):
    """Render the strong signals in the user interface."""
    if not strong_signals:
        return "لا توجد إشارات قوية حالياً."

    output = []
    for signal in strong_signals:
        output.append(f"توصية: {signal['recommendation']}")
        output.append(f"سعر الدخول: {signal['entry_price']}")
        output.append(f"أهداف جني الأرباح: TP1: {signal['take_profit1']}, TP2: {signal['take_profit2']}, TP3: {signal['take_profit3']}")
        output.append(f"وقف الخسارة: {signal['stop_loss']}")
        output.append(f"مستوى الثقة: {signal['confidence']}")
        output.append("=" * 50)

    return "\n".join(output)


def display_strong_signals(symbol, interval):
    """Display strong trading signals for the specified symbol and interval."""
    scan_result = fetch_strong_signals(symbol, interval)
    return render_strong_signals(scan_result['signals'])


def get_strong_signals(symbol=DEFAULT_SYMBOL, interval=DEFAULT_INTERVAL):
    """Return strong-signal scan results for all symbols or a selected symbol."""
    if perform_full_analysis is None:
        return {
            'success': False,
            'symbol': symbol,
            'interval': interval,
            'signals': [],
            'error': ANALYZER_IMPORT_ERROR,
        }

    symbols_to_scan = _symbols_to_scan(symbol)
    if not symbols_to_scan:
        return {
            'success': False,
            'symbol': symbol,
            'interval': interval,
            'signals': [],
            'error': 'الرمز المطلوب غير مدعوم في صفحة الإشارات القوية.',
        }

    scan_result = fetch_strong_signals(symbol, interval)
    target_label = 'كل الأسواق' if _normalize_symbol(symbol) in ('', 'ALL') else SUPPORTED_SYMBOLS[symbol]['label']

    return {
        'success': True,
        'symbol': _normalize_symbol(symbol) or 'ALL',
        'interval': interval,
        'symbol_label': target_label,
        'signals': scan_result['signals'],
        'categories': list(SYMBOL_CATEGORY_GROUPS.keys()),
        'scanned_symbols': scan_result['scanned_symbols'],
        'matched_signals': len(scan_result['signals']),
        'scan_errors': scan_result['scan_errors'],
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'error': None,
    }
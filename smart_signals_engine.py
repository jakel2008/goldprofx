from __future__ import annotations

from datetime import datetime, timezone

try:
    from advanced_analyzer_engine import perform_full_analysis
except Exception:
    perform_full_analysis = None

try:
    from forex_analyzer import CRYPTO_BINANCE_SYMBOLS, YF_SYMBOLS
except Exception:
    CRYPTO_BINANCE_SYMBOLS = {}
    YF_SYMBOLS = {}


DEFAULT_SYMBOL = 'ALL'
DEFAULT_INTERVAL = '1h'

RAW_SYMBOL_CATEGORY_GROUPS = {
    'الأزواج الرئيسية': [
        'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD', 'NZD/USD',
    ],
    'الأزواج التقاطعية': [
        'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/AUD', 'EUR/CAD', 'EUR/NZD',
        'GBP/JPY', 'GBP/CHF', 'GBP/AUD', 'GBP/CAD', 'GBP/NZD',
        'AUD/JPY', 'AUD/NZD', 'AUD/CAD', 'AUD/CHF',
        'CAD/JPY', 'CAD/CHF', 'CHF/JPY',
        'NZD/JPY', 'NZD/CHF', 'NZD/CAD',
    ],
    'المؤشرات الأمريكية': ['US500', 'NAS100', 'US30', 'US2000'],
    'العملات المشفرة': ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'BNB/USD'],
    'المعادن': ['XAU/USD', 'XAG/USD'],
}


def _normalize_symbol(symbol: str) -> str:
    cleaned = (symbol or '').strip().upper().replace(' ', '')
    if cleaned == 'ALL':
        return 'ALL'
    if '/' in cleaned:
        return cleaned
    if len(cleaned) == 6:
        return f'{cleaned[:3]}/{cleaned[3:]}'
    return cleaned


def _normalize_symbol_key(symbol: str) -> str:
    return (symbol or '').strip().upper().replace('/', '').replace(' ', '')


SUPPORTED_SYMBOL_KEYS = {
    _normalize_symbol_key(symbol)
    for symbol in [*YF_SYMBOLS.keys(), *CRYPTO_BINANCE_SYMBOLS.keys()]
}


def _is_supported_scan_symbol(symbol: str) -> bool:
    return _normalize_symbol_key(symbol) in SUPPORTED_SYMBOL_KEYS


SYMBOL_CATEGORY_GROUPS = {
    category: [symbol for symbol in symbols if _is_supported_scan_symbol(symbol)]
    for category, symbols in RAW_SYMBOL_CATEGORY_GROUPS.items()
}

SYMBOL_CATEGORY_GROUPS = {
    category: symbols
    for category, symbols in SYMBOL_CATEGORY_GROUPS.items()
    if symbols
}

SYMBOL_CATEGORY_MAP = {
    symbol: category
    for category, symbols in SYMBOL_CATEGORY_GROUPS.items()
    for symbol in symbols
}


def _symbols_to_scan(symbol: str) -> list[str]:
    normalized_symbol = _normalize_symbol(symbol)
    if normalized_symbol in ('', 'ALL'):
        all_symbols = []
        for group_symbols in SYMBOL_CATEGORY_GROUPS.values():
            all_symbols.extend(group_symbols)
        return all_symbols

    if normalized_symbol in SYMBOL_CATEGORY_MAP:
        return [normalized_symbol]

    if _is_supported_scan_symbol(normalized_symbol):
        return [normalized_symbol]

    return []


def _symbol_category(symbol: str) -> str:
    return SYMBOL_CATEGORY_MAP.get(symbol, 'غير مصنف')


def _classify_strong_recommendation(recommendation: str, buy_score: float, sell_score: float, score_gap: float) -> str | None:
    normalized_recommendation = (recommendation or '').strip()

    if normalized_recommendation in {'شراء قوي', 'بيع قوي'}:
        return normalized_recommendation

    dominant_score = max(buy_score, sell_score)
    if dominant_score < 1.5 or score_gap < 1.0:
        return None

    if 'شراء' in normalized_recommendation or buy_score > sell_score:
        return 'شراء قوي'

    if 'بيع' in normalized_recommendation or sell_score > buy_score:
        return 'بيع قوي'

    return None


def fetch_strong_signals(symbol: str, interval: str) -> dict:
    if perform_full_analysis is None:
        return {
            'signals': [],
            'scanned_symbols': 0,
            'scan_errors': [{'symbol': 'system', 'error': 'محرك التحليل غير متاح حالياً.'}],
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

        buy_score = float(analysis_result.get('buy_score', 0) or 0)
        sell_score = float(analysis_result.get('sell_score', 0) or 0)
        score_gap = abs(buy_score - sell_score)
        raw_recommendation = analysis_result.get('recommendation') or analysis_result.get('signal') or ''
        recommendation = _classify_strong_recommendation(raw_recommendation, buy_score, sell_score, score_gap)
        if recommendation is None:
            continue

        strong_signals.append({
            'symbol': current_symbol,
            'symbol_label': current_symbol,
            'category': _symbol_category(current_symbol),
            'recommendation': recommendation,
            'source_recommendation': raw_recommendation,
            'buy_score': round(buy_score, 2),
            'sell_score': round(sell_score, 2),
            'entry_price': analysis_result.get('entry_point'),
            'take_profit1': analysis_result.get('take_profit1'),
            'take_profit2': analysis_result.get('take_profit2'),
            'take_profit3': analysis_result.get('take_profit3'),
            'stop_loss': analysis_result.get('stop_loss'),
            'confidence': analysis_result.get('confidence'),
            'support': analysis_result.get('support'),
            'pivot': analysis_result.get('pivot'),
            'resistance': analysis_result.get('resistance'),
            'volatility': analysis_result.get('volatility'),
            'atr': analysis_result.get('atr'),
            'signals_list': analysis_result.get('signals_list') or analysis_result.get('signals') or [],
            'explanation': analysis_result.get('explanation') or analysis_result.get('analysis_text') or '',
            'score_gap': round(score_gap, 2),
        })

    strong_signals.sort(
        key=lambda item: (item['score_gap'], item['buy_score'], item['sell_score']),
        reverse=True,
    )
    return {
        'signals': strong_signals,
        'scanned_symbols': len(symbols_to_scan),
        'scan_errors': scan_errors,
    }


def get_smart_signals(symbol: str = DEFAULT_SYMBOL, interval: str = DEFAULT_INTERVAL) -> dict:
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
    normalized_symbol = _normalize_symbol(symbol)
    target_label = 'كل الأسواق' if normalized_symbol in ('', 'ALL') else normalized_symbol

    return {
        'success': True,
        'symbol': normalized_symbol or 'ALL',
        'interval': interval,
        'symbol_label': target_label,
        'signals': scan_result['signals'],
        'categories': [category for category, symbols in SYMBOL_CATEGORY_GROUPS.items() if symbols],
        'scanned_symbols': scan_result['scanned_symbols'],
        'matched_signals': len(scan_result['signals']),
        'scan_errors': scan_result['scan_errors'],
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'error': None,
    }
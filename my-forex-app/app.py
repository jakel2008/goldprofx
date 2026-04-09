import importlib.util
import os
import sys
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urlparse

from flask import Flask, jsonify, render_template, request
from pages.analyst_page import get_analyst_view
from pages.signals_page import get_signals
from pages.strong_signals_page import get_strong_signals
from pages.trade_simulator_page import get_trade_simulation
from services.advanced_analyzer_engine import SUPPORTED_INTERVALS, SUPPORTED_SYMBOLS

app = Flask(__name__)
ALLOWED_INTEGRATION_ORIGIN = 'https://goldprofx-1.onrender.com'
MAIN_SITE_URL = os.environ.get('MAIN_SITE_URL', '/')
DEFAULT_GOLD_PRO_DIR = Path(os.environ.get('GOLD_PRO_DIR', Path(__file__).resolve().parent.parent / 'GOLD PRO'))


SYMBOL_GROUPS = {
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


def build_grouped_symbol_options(include_all_option=False):
    grouped_options = []
    if include_all_option:
        grouped_options.append({
            'label': 'نطاق البحث',
            'options': [{'value': 'ALL', 'label': 'كل الأسواق'}],
        })
    for group_label, symbols in SYMBOL_GROUPS.items():
        options = []
        for symbol in symbols:
            info = SUPPORTED_SYMBOLS.get(symbol)
            if info is None:
                continue
            options.append({'value': symbol, 'label': info['label']})
        if options:
            grouped_options.append({'label': group_label, 'options': options})
    return grouped_options


def resolve_main_site_url():
    return MAIN_SITE_URL


def build_selector_context(selected_symbol='EURUSD', selected_interval='1h', include_all_option=False):
    main_site_url = resolve_main_site_url()
    return {
        'symbol_options': [
            {'value': symbol, 'label': info['label']}
            for symbol, info in SUPPORTED_SYMBOLS.items()
        ],
        'grouped_symbol_options': build_grouped_symbol_options(include_all_option=include_all_option),
        'interval_options': list(SUPPORTED_INTERVALS.keys()),
        'selected_symbol': selected_symbol,
        'selected_interval': selected_interval,
        'symbol_count': len(SUPPORTED_SYMBOLS),
        'interval_count': len(SUPPORTED_INTERVALS),
        'main_site_url': main_site_url,
        'return_to_param': quote(main_site_url, safe=''),
    }


def with_integration_cors(response):
    response.headers['Access-Control-Allow-Origin'] = ALLOWED_INTEGRATION_ORIGIN
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


def normalize_gold_pro_symbol(symbol):
    raw_symbol = str(symbol or 'EURUSD').strip().upper().replace('-', '').replace('_', '')
    if '/' in raw_symbol:
        return raw_symbol
    if len(raw_symbol) == 6 and raw_symbol.isalpha():
        return f'{raw_symbol[:3]}/{raw_symbol[3:]}'
    if raw_symbol in {'XAUUSD', 'XAGUSD', 'BTCUSD', 'ETHUSD'}:
        return f'{raw_symbol[:-3]}/{raw_symbol[-3:]}'
    return raw_symbol


@lru_cache(maxsize=1)
def load_gold_pro_perform_full_analysis():
    gold_pro_dir = DEFAULT_GOLD_PRO_DIR
    engine_path = gold_pro_dir / 'advanced_analyzer_engine.py'

    if not engine_path.exists():
        raise FileNotFoundError(f'Gold Pro analyzer not found at {engine_path}')

    if str(gold_pro_dir) not in sys.path:
        sys.path.insert(0, str(gold_pro_dir))

    module_name = 'gold_pro_advanced_analyzer_engine'
    existing_module = sys.modules.get(module_name)
    if existing_module and hasattr(existing_module, 'perform_full_analysis'):
        return existing_module.perform_full_analysis

    spec = importlib.util.spec_from_file_location(module_name, str(engine_path))
    if spec is None or spec.loader is None:
        raise ImportError(f'Unable to load Gold Pro analyzer from {engine_path}')

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.perform_full_analysis

@app.route('/')
def home():
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    return render_template('home.html', **build_selector_context(symbol, interval))

@app.route('/signals')
def signals():
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    signals_data = get_signals(symbol, interval)
    return render_template('signals.html', signals=signals_data, **build_selector_context(symbol, interval))

@app.route('/analyst')
def analyst():
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    analyst_data = get_analyst_view(symbol, interval)
    return render_template('analyst.html', analyst=analyst_data, **build_selector_context(symbol, interval))


@app.route('/trade-simulator')
def trade_simulator():
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    capital = request.args.get('capital', '1000')
    leverage = request.args.get('leverage', '100')
    risk_percent = request.args.get('risk_percent', '1')
    replay_bars = request.args.get('replay_bars', '24')
    embed_mode = request.args.get('embed', '0') == '1'
    simulation = get_trade_simulation(symbol, interval, capital, leverage, risk_percent, replay_bars)
    return render_template(
        'trade_simulator.html',
        simulation=simulation,
        embed_mode=embed_mode,
        **build_selector_context(symbol, interval),
    )


@app.route('/api/trade-simulator', methods=['GET', 'OPTIONS'])
def trade_simulator_api():
    if request.method == 'OPTIONS':
        return with_integration_cors(app.make_default_options_response())

    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    capital = request.args.get('capital', '1000')
    leverage = request.args.get('leverage', '100')
    risk_percent = request.args.get('risk_percent', '1')
    replay_bars = request.args.get('replay_bars', '24')
    simulation = get_trade_simulation(symbol, interval, capital, leverage, risk_percent, replay_bars)
    status_code = 200 if simulation.get('success') else 400
    return with_integration_cors(jsonify(simulation)), status_code

@app.route('/strong-signals')
def strong_signals():
    symbol = request.args.get('symbol', 'ALL')
    interval = request.args.get('interval', '1h')
    strong_signals_data = get_strong_signals(symbol, interval)
    return render_template('strong_signals.html', strong_signals=strong_signals_data, **build_selector_context(symbol, interval, include_all_option=True))


@app.route('/api/strong-signals')
def strong_signals_api():
    symbol = request.args.get('symbol', 'ALL')
    interval = request.args.get('interval', '1h')
    strong_signals_data = get_strong_signals(symbol, interval)
    status_code = 200 if strong_signals_data.get('success') else 400
    return jsonify(strong_signals_data), status_code


@app.route('/advanced-analyzer')
@app.route('/advanced_analyzer')
@app.route('/gold-pro-analyzer')
def advanced_analyzer():
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    return render_template(
        'advanced_analyzer.html',
        strategy_options=['harmonic', 'elliott', 'head_shoulders', 'smc', 'ict', 'ist'],
        **build_selector_context(symbol, interval),
    )


@app.route('/api/advanced-analysis', methods=['POST'])
@app.route('/api/advanced_analysis', methods=['POST'])
def advanced_analysis_api():
    data = request.get_json(silent=True) or {}
    symbol = data.get('symbol', 'EURUSD')
    interval = data.get('interval', '1h')

    try:
        perform_full_analysis = load_gold_pro_perform_full_analysis()
        result = perform_full_analysis(normalize_gold_pro_symbol(symbol), interval)
    except Exception as error:
        return jsonify({'success': False, 'error': f'تعذر تشغيل محلل Gold Pro: {error}'}), 500

    status_code = 200 if result.get('success') else 400
    return jsonify({'success': bool(result.get('success')), 'data': result, 'error': result.get('error')}), status_code

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=int(os.environ.get('PORT', '5002')))
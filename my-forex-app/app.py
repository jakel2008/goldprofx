import importlib.util
import json
import os
import sys
import threading
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urlparse
from typing import Any

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
WATCH_FILE = Path(__file__).resolve().parent / 'shadow_trade_watch.json'
WATCH_LOCK = threading.Lock()
WATCH_POLL_SECONDS = max(10, int(os.environ.get('SHADOW_WATCH_POLL_SECONDS', '30') or 30))
WATCH_THREAD_STARTED = False

if not DEFAULT_GOLD_PRO_DIR.exists():
    fallback_dir = Path(__file__).resolve().parent.parent
    if (fallback_dir / 'advanced_analyzer_engine.py').exists():
        DEFAULT_GOLD_PRO_DIR = fallback_dir


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


def build_grouped_symbol_options(include_all_option=False, lang='ar'):
    grouped_options = []
    if include_all_option:
        grouped_options.append({
            'label': 'Search scope' if lang == 'en' else 'نطاق البحث',
            'options': [{'value': 'ALL', 'label': 'All markets' if lang == 'en' else 'كل الأسواق'}],
        })
    for group_label, symbols in SYMBOL_GROUPS.items():
        options = []
        for symbol in symbols:
            info = SUPPORTED_SYMBOLS.get(symbol)
            if info is None:
                continue
            options.append({'value': symbol, 'label': info['label']})
        if options:
            english_group_labels = {
                'الأزواج الرئيسية': 'Major pairs',
                'الأزواج التقاطعية': 'Cross pairs',
                'المؤشرات الأمريكية': 'US indices',
                'العملات المشفرة': 'Cryptocurrencies',
                'المعادن': 'Metals',
            }
            grouped_options.append({'label': english_group_labels.get(group_label, group_label) if lang == 'en' else group_label, 'options': options})
    return grouped_options


def resolve_main_site_url():
    return MAIN_SITE_URL


def build_selector_context(selected_symbol='EURUSD', selected_interval='1h', include_all_option=False, lang='ar'):
    main_site_url = resolve_main_site_url()
    current_dir = 'rtl' if lang == 'ar' else 'ltr'
    return {
        'symbol_options': [
            {'value': symbol, 'label': info['label']}
            for symbol, info in SUPPORTED_SYMBOLS.items()
        ],
        'grouped_symbol_options': build_grouped_symbol_options(include_all_option=include_all_option, lang=lang),
        'interval_options': list(SUPPORTED_INTERVALS.keys()),
        'selected_symbol': selected_symbol,
        'selected_interval': selected_interval,
        'symbol_count': len(SUPPORTED_SYMBOLS),
        'interval_count': len(SUPPORTED_INTERVALS),
        'main_site_url': main_site_url,
        'return_to_param': quote(main_site_url, safe=''),
        'current_lang': lang,
        'current_dir': current_dir,
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


@lru_cache(maxsize=1)
def load_gold_pro_mt5_bridge():
    gold_pro_dir = DEFAULT_GOLD_PRO_DIR
    bridge_path = gold_pro_dir / 'mt5_bridge.py'

    if not bridge_path.exists():
        raise FileNotFoundError(f'Gold Pro MT5 bridge not found at {bridge_path}')

    if str(gold_pro_dir) not in sys.path:
        sys.path.insert(0, str(gold_pro_dir))

    module_name = 'gold_pro_mt5_bridge'
    existing_module = sys.modules.get(module_name)
    if existing_module and hasattr(existing_module, 'mt5_bridge'):
        return existing_module.mt5_bridge

    spec = importlib.util.spec_from_file_location(module_name, str(bridge_path))
    if spec is None or spec.loader is None:
        raise ImportError(f'Unable to load Gold Pro MT5 bridge from {bridge_path}')

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.mt5_bridge


def recommendation_to_side(value: Any) -> str:
    text = str(value or '').strip().lower()
    if any(token in text for token in ['buy', 'شراء']):
        return 'buy'
    if any(token in text for token in ['sell', 'بيع']):
        return 'sell'
    return ''


def _watch_state_default() -> dict:
    return {'groups': []}


def _load_watch_state() -> dict:
    if not WATCH_FILE.exists():
        return _watch_state_default()
    try:
        with WATCH_FILE.open('r', encoding='utf-8') as handle:
            data = json.load(handle) or {}
            groups = data.get('groups') if isinstance(data, dict) else None
            return {'groups': groups if isinstance(groups, list) else []}
    except Exception:
        return _watch_state_default()


def _save_watch_state(state: dict) -> None:
    WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with WATCH_FILE.open('w', encoding='utf-8') as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)


def _analysis_supports_direction(symbol: str, interval: str, side: str) -> tuple[bool, str]:
    try:
        perform_full_analysis = load_gold_pro_perform_full_analysis()
        result = perform_full_analysis(normalize_gold_pro_symbol(symbol), interval or '1h')
        if not bool(result.get('success')):
            return True, 'analysis_unavailable_keep_active'
        recommendation = str(result.get('recommendation') or result.get('signal') or '').strip()
        resolved_side = recommendation_to_side(recommendation)
        return resolved_side == side, recommendation
    except Exception as error:
        return True, f'analysis_error_keep_active:{error}'


def _register_watch_group(payload: dict, result: dict, interval: str) -> dict:
    orders = list(result.get('orders') or [])
    tickets = []
    for order in orders:
        details = order.get('result') if isinstance(order, dict) else None
        ticket = details.get('order') if isinstance(details, dict) else None
        try:
            ticket_value = int(ticket or 0)
        except Exception:
            ticket_value = 0
        if ticket_value > 0:
            tickets.append(ticket_value)

    created_at = int(time.time())
    group = {
        'group_id': f"{payload.get('symbol', 'UNK')}_{created_at}",
        'symbol': str(payload.get('symbol') or ''),
        'side': str(payload.get('signal_type') or ''),
        'interval': str(interval or '1h'),
        'created_at': created_at,
        'updated_at': created_at,
        'status': 'active',
        'had_position': False,
        'pending_tickets': tickets,
        'entry_price': float(payload.get('entry_price')) if payload.get('entry_price') is not None else None,
        'stop_loss': float(payload.get('stop_loss')) if payload.get('stop_loss') is not None else None,
        'take_profit_1': float(payload.get('take_profit_1')) if payload.get('take_profit_1') is not None else None,
        'take_profit_2': float(payload.get('take_profit_2')) if payload.get('take_profit_2') is not None else None,
        'take_profit_3': float(payload.get('take_profit_3')) if payload.get('take_profit_3') is not None else None,
        'sl_stage': 0,
        'sl_actions': [],
    }

    with WATCH_LOCK:
        state = _load_watch_state()
        state['groups'] = [item for item in state.get('groups', []) if item.get('status') == 'active']
        state['groups'].append(group)
        _save_watch_state(state)

    return group


def run_shadow_watchdog_once() -> dict:
    try:
        mt5_bridge = load_gold_pro_mt5_bridge()
    except Exception as error:
        return {'success': False, 'error': f'MT5 bridge unavailable: {error}'}

    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return str(raw).strip().lower() in {'1', 'true', 'yes', 'on'}

    mt5_bridge.enabled = _env_bool('MT5_ENABLED', True)
    mt5_bridge.allow_site_signals = _env_bool('MT5_ALLOW_SITE_SIGNALS', True)
    mt5_bridge.allow_trading = _env_bool('MT5_ALLOW_TRADING', False)

    with WATCH_LOCK:
        state = _load_watch_state()

    groups = state.get('groups', [])
    if not groups:
        return {'success': True, 'checked': 0, 'active': 0, 'updated': []}

    updated = []
    active_count = 0

    def _to_float(value):
        try:
            if value is None:
                return None
            return float(value)
        except Exception:
            return None

    def _price_close(a, b):
        aa = _to_float(a)
        bb = _to_float(b)
        if aa is None or bb is None:
            return False
        tolerance = max(abs(bb) * 0.0002, 0.0005)
        return abs(aa - bb) <= tolerance

    for group in groups:
        if group.get('status') != 'active':
            updated.append(group)
            continue

        symbol = str(group.get('symbol') or '')
        side = str(group.get('side') or '')
        interval = str(group.get('interval') or '1h')
        tickets = [int(item) for item in (group.get('pending_tickets') or []) if int(item) > 0]

        pending_open = []
        for ticket in tickets:
            info = mt5_bridge.get_pending_order(ticket)
            if bool(info.get('success')) and bool(info.get('exists')):
                pending_open.append(ticket)

        pos_info = mt5_bridge.has_open_positions(symbol=symbol, magic=getattr(mt5_bridge, 'magic', None))
        has_open_position = bool(pos_info.get('has_open')) if bool(pos_info.get('success')) else False
        had_position = bool(group.get('had_position')) or has_open_position
        positions = list(pos_info.get('positions') or []) if bool(pos_info.get('success')) else []

        tp_candidates = [
            _to_float(group.get('take_profit_1')),
            _to_float(group.get('take_profit_2')),
            _to_float(group.get('take_profit_3')),
        ]
        tp_candidates = [item for item in tp_candidates if item is not None]
        tracked_positions = []
        for row in positions:
            row_tp = _to_float(row.get('tp'))
            if (not tp_candidates) or any(_price_close(row_tp, tp) for tp in tp_candidates):
                tracked_positions.append(row)
        if not tracked_positions:
            tracked_positions = positions

        open_tracked_count = len(tracked_positions)
        side_is_buy = str(side).strip().lower() == 'buy'
        entry_price = _to_float(group.get('entry_price'))
        tp1 = _to_float(group.get('take_profit_1'))
        sl_stage = int(group.get('sl_stage') or 0)
        sl_actions = list(group.get('sl_actions') or [])

        def _needs_sl_update(current_sl, target_sl):
            if target_sl is None:
                return False
            cur = _to_float(current_sl)
            if cur is None:
                return True
            if _price_close(cur, target_sl):
                return False
            # Avoid moving stop in the wrong direction.
            if side_is_buy and cur > target_sl:
                return False
            if (not side_is_buy) and cur < target_sl:
                return False
            return True

        def _apply_stage_stop(target_sl, stage_name):
            nonlocal sl_stage, sl_actions
            if target_sl is None or not tracked_positions:
                return

            staged = [row for row in tracked_positions if _needs_sl_update(row.get('sl'), target_sl)]
            if not staged:
                sl_actions.append({'stage': stage_name, 'status': 'no_change_needed', 'target_sl': target_sl})
                return

            stage_results = []
            all_success = True
            for row in staged:
                try:
                    ticket_value = int(row.get('ticket') or 0)
                except Exception:
                    ticket_value = 0
                if ticket_value <= 0:
                    continue

                row_tp = _to_float(row.get('tp'))
                result = mt5_bridge.modify_position_sl_tp(ticket=ticket_value, sl=target_sl, tp=row_tp)
                stage_results.append({
                    'ticket': ticket_value,
                    'from_sl': _to_float(row.get('sl')),
                    'to_sl': target_sl,
                    'success': bool(result.get('success')),
                    'retcode': result.get('retcode'),
                    'error': result.get('error'),
                })
                if not bool(result.get('success')):
                    all_success = False

            sl_actions.append({
                'stage': stage_name,
                'target_sl': target_sl,
                'updated_positions': len(stage_results),
                'all_success': all_success,
                'results': stage_results,
            })
            if all_success and stage_results:
                if stage_name == 'after_tp1_to_entry':
                    sl_stage = max(sl_stage, 1)
                elif stage_name == 'after_tp2_to_tp1':
                    sl_stage = max(sl_stage, 2)

        # Smart stop management:
        # - After first TP is taken (2 tracked positions remain), move remaining SL to entry.
        # - After second TP is taken (1 tracked position remains), move last SL to TP1.
        if has_open_position and open_tracked_count <= 2 and sl_stage < 1:
            _apply_stage_stop(entry_price, 'after_tp1_to_entry')

        if has_open_position and open_tracked_count <= 1 and sl_stage < 2:
            _apply_stage_stop(tp1, 'after_tp2_to_tp1')

        group['updated_at'] = int(time.time())
        group['had_position'] = had_position
        group['pending_tickets'] = pending_open
        group['sl_stage'] = sl_stage
        group['sl_actions'] = sl_actions[-25:]

        if had_position and (not has_open_position) and pending_open:
            cancel_results = [mt5_bridge.cancel_pending_order(ticket) for ticket in pending_open]
            group['status'] = 'closed'
            group['closed_reason'] = 'trade_ended_pending_cancelled'
            group['cancel_results'] = cancel_results
            group['pending_tickets'] = []
            updated.append(group)
            continue

        analysis_ok, analysis_note = _analysis_supports_direction(symbol, interval, side)
        group['analysis_note'] = analysis_note

        if (not analysis_ok) and pending_open:
            cancel_results = [mt5_bridge.cancel_pending_order(ticket) for ticket in pending_open]
            group['status'] = 'closed'
            group['closed_reason'] = 'analysis_invalid_pending_cancelled'
            group['cancel_results'] = cancel_results
            group['pending_tickets'] = []
            updated.append(group)
            continue

        if (not pending_open) and (not has_open_position):
            group['status'] = 'closed'
            group['closed_reason'] = 'completed_no_pending'
            updated.append(group)
            continue

        active_count += 1
        updated.append(group)

    with WATCH_LOCK:
        _save_watch_state({'groups': updated})

    return {'success': True, 'checked': len(groups), 'active': active_count, 'updated': updated}


def _shadow_watchdog_loop() -> None:
    while True:
        try:
            run_shadow_watchdog_once()
        except Exception:
            pass
        time.sleep(WATCH_POLL_SECONDS)


def ensure_shadow_watchdog_started() -> None:
    global WATCH_THREAD_STARTED
    if WATCH_THREAD_STARTED:
        return
    WATCH_THREAD_STARTED = True
    thread = threading.Thread(target=_shadow_watchdog_loop, name='shadow-mt5-watchdog', daemon=True)
    thread.start()

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
    lang = request.args.get('lang', 'ar')
    strong_signals_data = get_strong_signals(symbol, interval, lang=lang)
    return render_template('strong_signals.html', strong_signals=strong_signals_data, **build_selector_context(symbol, interval, include_all_option=True, lang=lang))


@app.route('/api/strong-signals')
def strong_signals_api():
    symbol = request.args.get('symbol', 'ALL')
    interval = request.args.get('interval', '1h')
    lang = request.args.get('lang', 'ar')
    strong_signals_data = get_strong_signals(symbol, interval, lang=lang)
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


@app.route('/api/shadow/mt5/activate-signal', methods=['POST'])
def shadow_activate_signal_mt5():
    data = request.get_json(silent=True) or {}

    symbol = str(data.get('symbol') or '').strip().upper().replace('/', '')
    side = recommendation_to_side(data.get('recommendation') or data.get('signal_type') or data.get('signal'))
    if not symbol:
        return jsonify({'success': False, 'error': 'symbol is required'}), 400
    if not side:
        return jsonify({'success': False, 'error': 'could not infer signal side from recommendation'}), 400

    try:
        mt5_bridge = load_gold_pro_mt5_bridge()
    except Exception as error:
        return jsonify({'success': False, 'error': f'MT5 bridge unavailable: {error}'}), 500

    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return str(raw).strip().lower() in {'1', 'true', 'yes', 'on'}

    # Enforce runtime flags per request to avoid stale disabled state from previous imports/config.
    mt5_bridge.enabled = _env_bool('MT5_ENABLED', True)
    mt5_bridge.allow_site_signals = _env_bool('MT5_ALLOW_SITE_SIGNALS', True)
    mt5_bridge.allow_trading = _env_bool('MT5_ALLOW_TRADING', False)

    try:
        requested_volume = float(data.get('volume') or os.environ.get('SHADOW_SIGNAL_VOLUME', '0.01'))
        requested_dry_run = bool(data.get('dry_run', False))
        requested_interval = str(data.get('interval') or '1h').strip() or '1h'
        tp1 = float(data.get('take_profit1')) if data.get('take_profit1') is not None else None
        tp2 = float(data.get('take_profit2')) if data.get('take_profit2') is not None else None
        tp3 = float(data.get('take_profit3')) if data.get('take_profit3') is not None else None

        if tp1 is None or tp2 is None or tp3 is None:
            return jsonify({'success': False, 'error': 'three take-profit levels are required (TP1/TP2/TP3)'}), 400

        adjusted_volume = requested_volume
        volume_rules = mt5_bridge.get_symbol_volume_rules(symbol)
        if bool(volume_rules.get('success')):
            min_volume = float(volume_rules.get('volume_min') or 0.0)
            step_volume = float(volume_rules.get('volume_step') or 0.0)
            if min_volume > 0 and adjusted_volume < min_volume:
                adjusted_volume = min_volume
            if step_volume > 0:
                adjusted_volume = round(round(adjusted_volume / step_volume) * step_volume, 8)
                if min_volume > 0 and adjusted_volume < min_volume:
                    adjusted_volume = min_volume
        else:
            volume_rules = {'success': False, 'error': str(volume_rules.get('error') or 'volume rules unavailable')}

        payload = {
            'symbol': symbol,
            'signal_type': side,
            'entry_price': float(data.get('entry_price')) if data.get('entry_price') is not None else None,
            'stop_loss': float(data.get('stop_loss')) if data.get('stop_loss') is not None else None,
            'take_profit_1': tp1,
            'take_profit_2': tp2,
            'take_profit_3': tp3,
            'volume': adjusted_volume,
            'split_tp': True,
            'pending_entry': True,
            'dry_run': requested_dry_run,
            'manual_confirm': True,
            'execution_source': 'shadow_signal_card',
        }
    except Exception as error:
        return jsonify({'success': False, 'error': f'invalid numeric payload: {error}'}), 400

    result = mt5_bridge.execute_signal(payload)
    success = bool(result.get('success'))
    error_message = None
    if not success:
        order_errors = [
            str(order.get('error'))
            for order in (result.get('orders') or [])
            if isinstance(order, dict) and order.get('error')
        ]
        error_message = order_errors[0] if order_errors else str(result.get('error') or 'activation failed')

    response_body = {'success': success, 'result': result, 'payload': payload}

    # Include MT5 account context to detect "executed on a different account" confusion.
    try:
        status_info = mt5_bridge.status()
        account_info = status_info.get('account') if isinstance(status_info, dict) else None
        terminal_info = status_info.get('terminal') if isinstance(status_info, dict) else None
        response_body['mt5_context'] = {
            'login': (account_info or {}).get('login') if isinstance(account_info, dict) else None,
            'server': (account_info or {}).get('server') if isinstance(account_info, dict) else None,
            'name': (account_info or {}).get('name') if isinstance(account_info, dict) else None,
            'company': (terminal_info or {}).get('company') if isinstance(terminal_info, dict) else None,
        }
    except Exception:
        pass
    if error_message:
        response_body['error'] = error_message
    if adjusted_volume != requested_volume:
        response_body['warning'] = f'volume adjusted from {requested_volume} to {adjusted_volume} to match broker minimum/step'
    response_body['volume_rules'] = volume_rules

    if success and (not requested_dry_run) and bool(payload.get('pending_entry')) and bool(payload.get('split_tp')):
        # Verify tickets are visible in MT5 immediately after placement.
        placed_tickets = []
        for order in (result.get('orders') or []):
            details = order.get('result') if isinstance(order, dict) else None
            ticket = details.get('order') if isinstance(details, dict) else None
            try:
                tk = int(ticket or 0)
            except Exception:
                tk = 0
            if tk > 0:
                placed_tickets.append(tk)

        visibility = []
        all_visible = True
        for tk in placed_tickets:
            info = mt5_bridge.get_pending_order(tk)
            exists = bool(info.get('success')) and bool(info.get('exists'))

            # A pending order can disappear because it was triggered immediately;
            # in that case, accept open position presence as a valid execution signal.
            position_visible = False
            if not exists:
                pos_info = mt5_bridge.has_open_positions(symbol=symbol, magic=getattr(mt5_bridge, 'magic', None))
                position_visible = bool(pos_info.get('success')) and bool(pos_info.get('has_open'))

            visible = exists or position_visible
            visibility.append({
                'ticket': tk,
                'exists': exists,
                'position_visible': position_visible,
                'visible': visible,
                'error': info.get('error'),
            })
            if not visible:
                all_visible = False

        response_body['mt5_visibility'] = {
            'checked_tickets': placed_tickets,
            'results': visibility,
            'all_visible': all_visible,
        }

        if placed_tickets and (not all_visible):
            response_body['success'] = False
            response_body['error'] = 'orders accepted but not visible in MT5 open orders; check MT5 account/login and symbol suffix'

        watch_group = _register_watch_group(payload, result, requested_interval)
        response_body['watch_group'] = watch_group
        response_body['watchdog'] = run_shadow_watchdog_once()

    return jsonify(response_body), (200 if success else 400)


@app.route('/api/shadow/mt5/watchdog/run-once', methods=['POST'])
def shadow_mt5_watchdog_run_once_api():
    result = run_shadow_watchdog_once()
    return jsonify(result), (200 if result.get('success') else 500)


@app.route('/api/shadow/mt5/watchdog/status', methods=['GET'])
def shadow_mt5_watchdog_status_api():
    with WATCH_LOCK:
        state = _load_watch_state()
    return jsonify({'success': True, 'groups': state.get('groups', [])}), 200

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not bool(os.environ.get('FLASK_DEBUG')):
        ensure_shadow_watchdog_started()
    app.run(debug=False, use_reloader=False, host='127.0.0.1', port=int(os.environ.get('PORT', '5002')))
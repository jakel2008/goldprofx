from __future__ import annotations

from services.advanced_analyzer_engine import (
    SUPPORTED_INTERVALS,
    SUPPORTED_SYMBOLS,
    _confidence_label,
    _download_market_data,
    _price_levels,
    _recommendation_from_gap,
    _round_price,
    _score_market,
    perform_full_analysis,
)


CONTRACT_SPECS = {
    'default': {'contract_size': 100000, 'unit_name': 'وحدة', 'lot_name': 'لوت قياسي'},
    'forex': {'contract_size': 100000, 'unit_name': 'وحدة', 'lot_name': 'لوت قياسي'},
    'metals_gold': {'contract_size': 100, 'unit_name': 'أونصة', 'lot_name': 'لوت ذهب'},
    'metals_silver': {'contract_size': 5000, 'unit_name': 'أونصة', 'lot_name': 'لوت فضة'},
    'indices': {'contract_size': 1, 'unit_name': 'عقد', 'lot_name': 'عقد'},
    'crypto': {'contract_size': 1, 'unit_name': 'وحدة', 'lot_name': 'وحدة'},
}


def _normalize_symbol(symbol: str) -> str:
    return (symbol or '').strip().upper().replace('/', '')


def _normalize_interval(interval: str) -> str:
    return (interval or '').strip().lower()


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _symbol_spec(symbol: str) -> dict:
    if symbol == 'XAUUSD':
        return CONTRACT_SPECS['metals_gold']
    if symbol == 'XAGUSD':
        return CONTRACT_SPECS['metals_silver']
    if symbol in {'US500', 'NAS100', 'US30', 'US2000'}:
        return CONTRACT_SPECS['indices']
    if symbol in {'BTCUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'BNBUSD'}:
        return CONTRACT_SPECS['crypto']
    return CONTRACT_SPECS['forex']


def _trade_direction(recommendation: str) -> int:
    if 'بيع' in recommendation:
        return -1
    if 'شراء' in recommendation:
        return 1
    return 0


def _profit_for_price_move(entry: float, exit_price: float, direction: int, units: float) -> float:
    price_move = (exit_price - entry) * direction
    return price_move * units


def _format_timestamp(timestamp) -> str:
    if hasattr(timestamp, 'strftime'):
        return timestamp.strftime('%Y-%m-%d %H:%M')
    return str(timestamp)


def _build_replay_snapshot(symbol: str, interval: str, replay_bars: int) -> dict:
    if interval not in SUPPORTED_INTERVALS:
        return {'success': False, 'error': 'الإطار الزمني غير مدعوم في إعادة التشغيل التاريخية.'}

    try:
        market_data = _download_market_data(symbol, interval)
    except Exception as exc:
        return {'success': False, 'error': f'تعذر جلب البيانات التاريخية للمحاكاة: {exc}'}

    minimum_required = replay_bars + 60
    if market_data.empty or len(market_data) <= minimum_required:
        return {
            'success': False,
            'error': f'البيانات المتاحة غير كافية لإعادة تشغيل {replay_bars} شموع على هذا الإطار.',
        }

    snapshot = market_data.iloc[:-replay_bars].copy()
    future_data = market_data.iloc[-replay_bars:].copy()
    buy_score, sell_score, details = _score_market(snapshot)
    score_gap = buy_score - sell_score
    recommendation = _recommendation_from_gap(score_gap)
    confidence = _confidence_label(abs(score_gap))
    direction = _trade_direction(recommendation)

    latest = snapshot.iloc[-1]
    entry_price = _round_price(float(latest['Close']), symbol)

    replay = {
        'success': True,
        'signal_time': _format_timestamp(snapshot.index[-1]),
        'replay_start_time': _format_timestamp(future_data.index[0]),
        'replay_end_time': _format_timestamp(future_data.index[-1]),
        'recommendation': recommendation,
        'confidence': confidence,
        'entry_price': entry_price,
        'future_data': future_data,
        'direction': direction,
        'buy_score': buy_score,
        'sell_score': sell_score,
        'bars_requested': replay_bars,
        'atr14': float(details['atr14']),
    }

    if direction == 0:
        replay.update({
            'trade_allowed': False,
            'message': 'الإشارة التاريخية المختارة كانت انتظار، لذلك لا توجد صفقة لإعادة تشغيلها.',
        })
        return replay

    take_profit1, take_profit2, take_profit3, stop_loss = _price_levels(
        entry_price,
        replay['atr14'],
        direction,
        symbol,
        interval,
    )
    replay.update({
        'trade_allowed': True,
        'stop_loss': stop_loss,
        'take_profit1': take_profit1,
        'take_profit2': take_profit2,
        'take_profit3': take_profit3,
    })
    return replay


def _simulate_candle_replay(symbol: str, capital: float, units: float, replay_snapshot: dict) -> dict:
    if not replay_snapshot.get('success'):
        return replay_snapshot
    if not replay_snapshot.get('trade_allowed'):
        return replay_snapshot

    direction = replay_snapshot['direction']
    entry_price = float(replay_snapshot['entry_price'])
    stop_loss = float(replay_snapshot['stop_loss'])
    targets = [
        ('TP1', float(replay_snapshot['take_profit1'])),
        ('TP2', float(replay_snapshot['take_profit2'])),
        ('TP3', float(replay_snapshot['take_profit3'])),
    ]
    future_data = replay_snapshot['future_data']
    reached_targets = []
    timeline = []
    exit_reason = 'لا تزال الصفقة مفتوحة'
    exit_price = None
    realized_profit = None
    trade_closed = False
    max_favorable_profit = float('-inf')
    max_adverse_profit = float('inf')

    for step, (timestamp, candle) in enumerate(future_data.iterrows(), start=1):
        candle_open = float(candle['Open'])
        candle_high = float(candle['High'])
        candle_low = float(candle['Low'])
        candle_close = float(candle['Close'])

        favorable_price = candle_high if direction > 0 else candle_low
        adverse_price = candle_low if direction > 0 else candle_high
        favorable_profit = _profit_for_price_move(entry_price, favorable_price, direction, units)
        adverse_profit = _profit_for_price_move(entry_price, adverse_price, direction, units)
        max_favorable_profit = max(max_favorable_profit, favorable_profit)
        max_adverse_profit = min(max_adverse_profit, adverse_profit)

        if direction > 0:
            stop_hit = candle_low <= stop_loss
            target_hits = [name for name, price in targets if candle_high >= price and name not in reached_targets]
        else:
            stop_hit = candle_high >= stop_loss
            target_hits = [name for name, price in targets if candle_low <= price and name not in reached_targets]

        event_parts = []
        if stop_hit and target_hits:
            exit_reason = 'شمعة متداخلة لامست الهدف والوقف معًا، وتم اعتماد الوقف أولاً بشكل محافظ.'
            exit_price = stop_loss
            realized_profit = _profit_for_price_move(entry_price, exit_price, direction, units)
            trade_closed = True
            event_parts.append('تفعيل وقف الخسارة أولاً')
        elif stop_hit:
            exit_reason = 'تم ضرب وقف الخسارة أثناء إعادة التشغيل.'
            exit_price = stop_loss
            realized_profit = _profit_for_price_move(entry_price, exit_price, direction, units)
            trade_closed = True
            event_parts.append('ضرب وقف الخسارة')
        elif target_hits:
            reached_targets.extend(target_hits)
            event_parts.append(' / '.join(f'تم الوصول إلى {target}' for target in target_hits))
            if 'TP3' in target_hits:
                exit_reason = 'وصلت الصفقة إلى الهدف الثالث أثناء إعادة التشغيل.'
                exit_price = next(price for name, price in targets if name == 'TP3')
                realized_profit = _profit_for_price_move(entry_price, exit_price, direction, units)
                trade_closed = True

        mark_price = exit_price if trade_closed and realized_profit is not None else candle_close
        mark_profit = realized_profit if trade_closed and realized_profit is not None else _profit_for_price_move(entry_price, mark_price, direction, units)
        timeline.append({
            'step': step,
            'time': _format_timestamp(timestamp),
            'open': _round_price(candle_open, symbol),
            'high': _round_price(candle_high, symbol),
            'low': _round_price(candle_low, symbol),
            'close': _round_price(candle_close, symbol),
            'mark_profit': _round(mark_profit, 2),
            'mark_return_pct': _round((mark_profit / capital) * 100, 2),
            'event': ' | '.join(event_parts) if event_parts else 'مراقبة استمرار الصفقة',
            'reached_targets': reached_targets.copy(),
        })

        if trade_closed:
            break

    if not timeline:
        return {'success': False, 'error': 'تعذر إنشاء خط زمني لإعادة التشغيل التاريخية.'}

    last_timeline = timeline[-1]
    final_profit = realized_profit if realized_profit is not None else last_timeline['mark_profit']
    final_return_pct = _round((final_profit / capital) * 100, 2)
    last_close = float(future_data.iloc[min(len(timeline), len(future_data)) - 1]['Close'])

    if trade_closed and exit_price is not None:
        final_status = 'مغلقة'
        final_price = _round_price(exit_price, symbol)
    else:
        final_status = 'مفتوحة'
        final_price = _round_price(last_close, symbol)
        exit_reason = 'انتهت الشموع المتاحة بينما الصفقة ما تزال مفتوحة.'

    return {
        'success': True,
        'trade_allowed': True,
        'signal_time': replay_snapshot['signal_time'],
        'replay_start_time': replay_snapshot['replay_start_time'],
        'replay_end_time': replay_snapshot['replay_end_time'],
        'bars_requested': replay_snapshot['bars_requested'],
        'bars_replayed': len(timeline),
        'recommendation': replay_snapshot['recommendation'],
        'confidence': replay_snapshot['confidence'],
        'entry_price': replay_snapshot['entry_price'],
        'stop_loss': replay_snapshot['stop_loss'],
        'take_profit1': replay_snapshot['take_profit1'],
        'take_profit2': replay_snapshot['take_profit2'],
        'take_profit3': replay_snapshot['take_profit3'],
        'buy_score': replay_snapshot['buy_score'],
        'sell_score': replay_snapshot['sell_score'],
        'final_status': final_status,
        'exit_reason': exit_reason,
        'exit_price': final_price,
        'final_profit': _round(final_profit, 2),
        'final_return_pct': final_return_pct,
        'max_favorable_profit': _round(max_favorable_profit, 2),
        'max_adverse_profit': _round(max_adverse_profit, 2),
        'targets_hit_count': len(reached_targets),
        'highest_target_reached': reached_targets[-1] if reached_targets else 'لا يوجد',
        'timeline': timeline,
        'notes': [
            f"تم بناء الإشارة التاريخية قبل {replay_snapshot['bars_requested']} شموع من آخر شمعة متاحة.",
            'يتم اعتماد وقف الخسارة أولاً إذا لامست الشمعة الهدف والوقف في الوقت نفسه لتجنب التفاؤل غير الواقعي.',
            'تنتهي الإعادة عند الهدف الثالث أو وقف الخسارة أو آخر شمعة متاحة، أيها يحدث أولاً.',
        ],
    }


def simulate_trade(
    symbol: str,
    interval: str,
    capital: float,
    leverage: float,
    risk_percent: float,
    replay_bars: int = 24,
) -> dict:
    normalized_symbol = _normalize_symbol(symbol)
    normalized_interval = _normalize_interval(interval)

    if normalized_symbol not in SUPPORTED_SYMBOLS:
        return {'success': False, 'error': 'الرمز غير مدعوم في محاكي التداول.'}

    if capital <= 0:
        return {'success': False, 'error': 'رأس المال يجب أن يكون أكبر من صفر.'}
    if leverage <= 0:
        return {'success': False, 'error': 'الرافعة يجب أن تكون أكبر من صفر.'}
    if risk_percent <= 0:
        return {'success': False, 'error': 'نسبة المخاطرة يجب أن تكون أكبر من صفر.'}
    if replay_bars < 5:
        return {'success': False, 'error': 'عدد شموع إعادة التشغيل يجب أن يكون 5 شموع على الأقل.'}

    analysis = perform_full_analysis(normalized_symbol, normalized_interval)
    if not analysis.get('success'):
        return {'success': False, 'error': analysis.get('error', 'تعذر جلب إشارة التداول الحالية.')}

    direction = _trade_direction(analysis['recommendation'])
    if direction == 0:
        return {
            'success': True,
            'trade_allowed': False,
            'symbol': normalized_symbol,
            'symbol_label': analysis['symbol_label'],
            'interval': normalized_interval,
            'recommendation': analysis['recommendation'],
            'message': 'الإشارة الحالية هي انتظار، لذلك لا توجد صفقة مباشرة يوصى بمحاكاتها الآن.',
            'analysis': analysis,
        }

    entry_price = float(analysis['entry_point'])
    stop_loss = float(analysis['stop_loss'])
    take_profit1 = float(analysis['take_profit1'])
    take_profit2 = float(analysis['take_profit2'])
    take_profit3 = float(analysis['take_profit3'])
    stop_distance = abs(entry_price - stop_loss)
    if stop_distance == 0:
        return {'success': False, 'error': 'المسافة بين الدخول ووقف الخسارة تساوي صفر، لا يمكن حساب المحاكاة.'}

    risk_amount_target = capital * (risk_percent / 100)
    max_notional = capital * leverage
    units_by_risk = risk_amount_target / stop_distance
    units_by_leverage = max_notional / entry_price
    position_units = min(units_by_risk, units_by_leverage)

    spec = _symbol_spec(normalized_symbol)
    lot_size = position_units / spec['contract_size']
    used_notional = position_units * entry_price
    margin_required = used_notional / leverage
    effective_risk_amount = position_units * stop_distance
    capped_by_leverage = units_by_leverage < units_by_risk

    profit_tp1 = _profit_for_price_move(entry_price, take_profit1, direction, position_units)
    profit_tp2 = _profit_for_price_move(entry_price, take_profit2, direction, position_units)
    profit_tp3 = _profit_for_price_move(entry_price, take_profit3, direction, position_units)
    loss_stop = _profit_for_price_move(entry_price, stop_loss, direction, position_units)
    replay_snapshot = _build_replay_snapshot(normalized_symbol, normalized_interval, int(replay_bars))
    historical_replay = _simulate_candle_replay(
        normalized_symbol,
        capital,
        position_units,
        replay_snapshot,
    )

    def ratio(profit_value: float, loss_value: float) -> float:
        loss_abs = abs(loss_value)
        if loss_abs == 0:
            return 0.0
        return _round(abs(profit_value) / loss_abs, 2)

    return {
        'success': True,
        'trade_allowed': True,
        'symbol': normalized_symbol,
        'symbol_label': analysis['symbol_label'],
        'interval': normalized_interval,
        'recommendation': analysis['recommendation'],
        'direction_label': 'شراء' if direction > 0 else 'بيع',
        'capital': _round(capital, 2),
        'leverage': _round(leverage, 2),
        'risk_percent': _round(risk_percent, 2),
        'contract_size': spec['contract_size'],
        'unit_name': spec['unit_name'],
        'lot_name': spec['lot_name'],
        'entry_price': analysis['entry_point'],
        'stop_loss': analysis['stop_loss'],
        'take_profit1': analysis['take_profit1'],
        'take_profit2': analysis['take_profit2'],
        'take_profit3': analysis['take_profit3'],
        'position_units': _round(position_units, 4),
        'lot_size': _round(lot_size, 4),
        'notional_value': _round(used_notional, 2),
        'margin_required': _round(margin_required, 2),
        'free_margin_after_entry': _round(capital - margin_required, 2),
        'risk_amount_target': _round(risk_amount_target, 2),
        'effective_risk_amount': _round(effective_risk_amount, 2),
        'effective_risk_percent': _round((effective_risk_amount / capital) * 100, 2),
        'capped_by_leverage': capped_by_leverage,
        'replay_bars': int(replay_bars),
        'profits': {
            'take_profit1': _round(profit_tp1, 2),
            'take_profit2': _round(profit_tp2, 2),
            'take_profit3': _round(profit_tp3, 2),
            'stop_loss': _round(loss_stop, 2),
        },
        'returns_pct': {
            'take_profit1': _round((profit_tp1 / capital) * 100, 2),
            'take_profit2': _round((profit_tp2 / capital) * 100, 2),
            'take_profit3': _round((profit_tp3 / capital) * 100, 2),
            'stop_loss': _round((loss_stop / capital) * 100, 2),
        },
        'risk_reward': {
            'take_profit1': ratio(profit_tp1, loss_stop),
            'take_profit2': ratio(profit_tp2, loss_stop),
            'take_profit3': ratio(profit_tp3, loss_stop),
        },
        'notes': [
            f"تم حساب حجم الصفقة بناءً على مخاطرة مستهدفة قدرها {_round(risk_amount_target, 2)} دولار.",
            'تم ربط الحساب مباشرة بإشارة التحليل الحالية للزوج المختار.',
            'إذا قيدت الرافعة حجم الصفقة، فسيتم خفض المخاطرة الفعلية تلقائيًا عن النسبة المستهدفة.' if capped_by_leverage else 'الرافعة الحالية تسمح بتنفيذ حجم الصفقة المطلوب ضمن نسبة المخاطرة المحددة.',
        ],
        'historical_replay': historical_replay,
        'analysis': analysis,
    }
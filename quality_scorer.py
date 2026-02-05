# -*- coding: utf-8 -*-
"""
نظام تقييم جودة التوصيات
"""

def add_quality_score(analysis):
    """
    إضافة درجة جودة للتوصية بناءً على عدة عوامل
    
    معايير الجودة:
    1. قوة RSI (مدى تطرفه)
    2. قوة الترند (trend_strength)
    3. تأكيد MACD
    4. نسبة Risk/Reward
    5. تطابق مع EMA
    
    Returns:
        analysis مع حقل 'quality' و 'quality_score'
    """
    
    if not analysis or 'signal' not in analysis:
        return analysis
    
    score = 0
    max_score = 100
    
    # 1. قوة RSI (20 نقطة)
    rsi = analysis.get('rsi', 50)
    if analysis['signal'] == 'sell':
        # للبيع، كلما كان RSI أعلى كان أفضل
        if rsi >= 80:
            score += 20
        elif rsi >= 75:
            score += 15
        elif rsi >= 70:
            score += 10
    else:  # buy
        # للشراء، كلما كان RSI أقل كان أفضل
        if rsi <= 20:
            score += 20
        elif rsi <= 25:
            score += 15
        elif rsi <= 30:
            score += 10
    
    # 2. قوة الترند (25 نقطة)
    trend_strength = analysis.get('trend_strength', 0)
    if trend_strength >= 0.5:
        score += 25
    elif trend_strength >= 0.4:
        score += 20
    elif trend_strength >= 0.3:
        score += 15
    elif trend_strength >= 0.2:
        score += 10
    
    # 3. تأكيد MACD (15 نقطة)
    macd = analysis.get('macd', 0)
    macd_signal = analysis.get('macd_signal', 0)
    
    if analysis['signal'] == 'sell':
        # للبيع: MACD يجب أن يكون أقل من الإشارة وكلاهما سالب
        if macd < macd_signal and macd < 0:
            score += 15
        elif macd < macd_signal:
            score += 10
    else:  # buy
        # للشراء: MACD يجب أن يكون أعلى من الإشارة وكلاهما موجب
        if macd > macd_signal and macd > 0:
            score += 15
        elif macd > macd_signal:
            score += 10
    
    # 4. نسبة Risk/Reward (25 نقطة)
    entry = analysis.get('entry_price', 0)
    sl = analysis.get('stop_loss', 0)
    tp1 = analysis.get('take_profit', 0)
    
    if entry > 0 and sl > 0 and tp1 > 0:
        risk = abs(entry - sl)
        reward = abs(tp1 - entry)
        
        if risk > 0:
            rr_ratio = reward / risk
            
            if rr_ratio >= 3:
                score += 25
            elif rr_ratio >= 2.5:
                score += 20
            elif rr_ratio >= 2:
                score += 15
            elif rr_ratio >= 1.5:
                score += 10
    
    # 5. تطابق مع EMA (15 نقطة)
    current_price = analysis.get('current_price', 0)
    ema_20 = analysis.get('ema_20', 0)
    ema_50 = analysis.get('ema_50', 0)
    
    if current_price > 0 and ema_20 > 0 and ema_50 > 0:
        if analysis['signal'] == 'sell':
            # للبيع: السعر فوق EMAs والترند هابط
            if current_price > ema_20 > ema_50:
                score += 15
            elif current_price > ema_20:
                score += 10
        else:  # buy
            # للشراء: السعر تحت EMAs والترند صاعد
            if current_price < ema_20 < ema_50:
                score += 15
            elif current_price < ema_20:
                score += 10
    
    # تحديد التصنيف بناءً على النقاط
    if score >= 75:
        quality = 'high'
    elif score >= 50:
        quality = 'medium'
    else:
        quality = 'low'
    
    # إضافة البيانات للتحليل
    analysis['quality_score'] = score
    analysis['quality'] = quality
    
    return analysis

def filter_signals_by_quality(signals, min_quality='medium'):
    """
    تصفية التوصيات حسب الجودة
    
    Args:
        signals: قائمة التوصيات
        min_quality: الحد الأدنى للجودة ('low', 'medium', 'high')
    
    Returns:
        قائمة التوصيات المفلترة
    """
    
    quality_levels = {'low': 0, 'medium': 1, 'high': 2}
    min_level = quality_levels.get(min_quality, 1)
    
    filtered = []
    for signal in signals:
        if not signal or 'quality' not in signal:
            continue
        
        signal_level = quality_levels.get(signal['quality'], 0)
        if signal_level >= min_level:
            filtered.append(signal)
    
    return filtered

def get_quality_threshold_for_plan(plan):
    """
    تحديد الحد الأدنى لجودة التوصيات حسب الخطة
    
    Args:
        plan: نوع الخطة (free, bronze, silver, gold, platinum)
    
    Returns:
        الحد الأدنى للجودة
    """
    
    thresholds = {
        'free': 'high',      # فقط التوصيات عالية الجودة
        'bronze': 'medium',  # متوسطة وأعلى
        'silver': 'medium',  # متوسطة وأعلى
        'gold': 'low',       # جميع التوصيات
        'platinum': 'low'    # جميع التوصيات
    }
    
    return thresholds.get(plan, 'high')

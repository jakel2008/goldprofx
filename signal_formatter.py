# -*- coding: utf-8 -*-
"""
دالة مساعدة لتنسيق الإشارات بالشكل الجديد
"""

def format_signal_message(symbol, signal_type, entry, stop_loss, take_profits, quality_score=85):
    """
    تنسيق رسالة إشارة بالشكل الجديد المحسن
    
    Args:
        symbol: اسم الزوج (EURUSD, GBPUSD, etc)
        signal_type: نوع الإشارة (buy/sell أو شراء/بيع)
        entry: سعر الدخول
        stop_loss: وقف الخسارة
        take_profits: قائمة بأهداف الربح [tp1, tp2, tp3]
        quality_score: درجة الجودة (0-100)
    
    Returns:
        str: رسالة منسقة بالـ Markdown
    """
    # تحديد الرمز والاتجاه
    if 'buy' in str(signal_type).lower() or 'شراء' in str(signal_type):
        direction_emoji = '🟢'
        direction_text = 'شراء'
    else:
        direction_emoji = '🔴'
        direction_text = 'بيع'
    
    # بناء الرسالة
    message = f"""
{direction_emoji} *{symbol}* {direction_text}

💰 الدخول: `{entry:.5f}`
🛑 وقف الخسارة: `{stop_loss:.5f}`
"""
    
    # إضافة الأهداف
    if take_profits and len(take_profits) > 0:
        message += "\n🎯 *الأهداف:*\n"
        for i, tp in enumerate(take_profits, 1):
            if tp:
                message += f"   الهدف {i}: `{tp:.5f}`\n"
    
    # إضافة الجودة والوقت
    from datetime import datetime
    message += f"\n⭐ الجودة: *{quality_score}/100*"
    message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    return message


def format_recommendation_message(symbol, signal_type, entry, stop_loss, take_profits, 
                                   quality_score=85, rsi=50, trend_strength=0):
    """
    تنسيق رسالة توصية بالشكل الجديد المحسن
    
    Args:
        symbol: اسم الزوج
        signal_type: نوع الإشارة
        entry: سعر الدخول المثالي
        stop_loss: وقف الخسارة المحسوب
        take_profits: قائمة بأهداف الربح
        quality_score: درجة الجودة
        rsi: قيمة RSI
        trend_strength: قوة الاتجاه %
    
    Returns:
        str: رسالة توصية منسقة
    """
    # تحديد الاتجاه
    if 'buy' in str(signal_type).lower() or 'شراء' in str(signal_type):
        direction_text = 'شراء'
    else:
        direction_text = 'بيع'
    
    from datetime import datetime
    
    message = f"""
📊 *تحليل {symbol}*
━━━━━━━━━━━━━━━━━━
✅ التوصية: *{direction_text}*
📈 قوة الإشارة: {quality_score}%
💎 نقطة دخول مثالية: `{entry:.5f}`
🛡️ SL محسوب بـ ATR: `{stop_loss:.5f}`

🎯 *أهداف الربح:*
"""
    
    # إضافة الأهداف مع نسب R:R
    if take_profits and len(take_profits) >= 3:
        rr_ratios = ['1:2', '1:3', '1:5']
        for i, (tp, rr) in enumerate(zip(take_profits[:3], rr_ratios), 1):
            if tp:
                message += f"   {i}️⃣ الهدف {['الأول', 'الثاني', 'الثالث'][i-1]}: `{tp:.5f}` (R:R {rr})\n"
    
    # إضافة معلومات فنية
    message += f"\n🔬 RSI: {rsi:.2f}"
    if trend_strength:
        message += f"\n📊 قوة الاتجاه: {trend_strength:.1f}%"
    message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    return message


if __name__ == "__main__":
    # اختبار التنسيقات
    print("=" * 50)
    print("اختبار تنسيق الإشارة:")
    print("=" * 50)
    signal_msg = format_signal_message(
        symbol="EURUSD",
        signal_type="buy",
        entry=1.18624,
        stop_loss=1.18324,
        take_profits=[1.19124, 1.19424, 1.19924],
        quality_score=95
    )
    print(signal_msg)
    
    print("\n" + "=" * 50)
    print("اختبار تنسيق التوصية:")
    print("=" * 50)
    rec_msg = format_recommendation_message(
        symbol="EURUSD",
        signal_type="buy",
        entry=1.18500,
        stop_loss=1.18200,
        take_profits=[1.19100, 1.19400, 1.20000],
        quality_score=85,
        rsi=28.5,
        trend_strength=78.3
    )
    print(rec_msg)

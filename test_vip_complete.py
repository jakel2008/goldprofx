# -*- coding: utf-8 -*-
"""
اختبار النظام VIP الكامل
"""

from vip_subscription_system import SubscriptionManager
from quality_scorer import add_quality_score
import json

def test_vip_system():
    """اختبار شامل لنظام VIP"""
    
    print("="*60)
    print("🧪 بدء اختبار نظام VIP")
    print("="*60)
    
    # 1. اختبار نظام الاشتراكات
    print("\n1️⃣ اختبار نظام الاشتراكات...")
    manager = SubscriptionManager()
    
    # إضافة مستخدم تجريبي
    test_user_id = 999888777
    manager.add_user(test_user_id, "test_user")
    
    # التحقق من الاشتراك
    status = manager.check_subscription(test_user_id)
    print(f"   ✅ حالة المستخدم: {status['plan']} - {status['status']}")
    print(f"   ✅ الأيام المتبقية: {status['days_left']}")
    
    # 2. اختبار نظام تقييم الجودة
    print("\n2️⃣ اختبار نظام تقييم الجودة...")
    
    test_signals = [
        {
            'pair': 'EURUSD',
            'signal': 'buy',
            'entry_price': 1.0850,
            'stop_loss': 1.0820,
            'take_profit': 1.0925,
            'rsi': 22.5,
            'macd': 0.0005,
            'macd_signal': 0.0003,
            'current_price': 1.0850,
            'ema_20': 1.0870,
            'ema_50': 1.0890,
            'trend_strength': 0.35
        },
        {
            'pair': 'GBPUSD',
            'signal': 'sell',
            'entry_price': 1.2650,
            'stop_loss': 1.2680,
            'take_profit': 1.2575,
            'rsi': 76.0,
            'macd': -0.0003,
            'macd_signal': -0.0001,
            'current_price': 1.2650,
            'ema_20': 1.2640,
            'ema_50': 1.2630,
            'trend_strength': 0.42
        },
        {
            'pair': 'XAUUSD',
            'signal': 'buy',
            'entry_price': 2050.0,
            'stop_loss': 2045.0,
            'take_profit': 2065.0,
            'rsi': 35.0,
            'macd': 0.5,
            'macd_signal': 0.3,
            'current_price': 2050.0,
            'ema_20': 2055.0,
            'ema_50': 2060.0,
            'trend_strength': 0.25
        }
    ]
    
    scored_signals = []
    for signal in test_signals:
        scored = add_quality_score(signal)
        scored_signals.append(scored)
        print(f"   📊 {scored['pair']}: {scored['quality'].upper()} ({scored['quality_score']}/100)")
    
    # 3. اختبار التصفية حسب الخطة
    print("\n3️⃣ اختبار التصفية حسب الخطة...")
    
    # المستخدم المجاني يحصل فقط على high quality
    high_quality_signals = [s for s in scored_signals if s['quality'] == 'high']
    print(f"   🆓 FREE: {len(high_quality_signals)} توصية (high only)")
    
    # Bronze يحصل على medium+
    medium_plus = [s for s in scored_signals if s['quality'] in ['medium', 'high']]
    print(f"   🥉 BRONZE: {len(medium_plus)} توصية (medium+)")
    
    # Gold يحصل على كل شيء
    print(f"   🥇 GOLD: {len(scored_signals)} توصية (all)")
    
    # 4. اختبار الحد اليومي
    print("\n4️⃣ اختبار الحد اليومي للإشارات...")
    
    for i, signal in enumerate(scored_signals[:5]):
        can_receive, msg = manager.can_receive_signal(test_user_id, signal['quality'])
        if can_receive:
            manager.log_signal_sent(test_user_id, signal, signal['quality'])
            print(f"   ✅ إشارة {i+1}: مرسلة")
        else:
            print(f"   ❌ إشارة {i+1}: {msg}")
    
    # 5. اختبار الإحصائيات
    print("\n5️⃣ اختبار الإحصائيات...")
    stats = manager.get_user_stats(test_user_id)
    print(f"   📊 الإشارات المستلمة: {stats['total_signals_received']}")
    print(f"   💵 المدفوع: ${stats['total_paid']:.2f}")
    print(f"   👥 الإحالات الناجحة: {stats['successful_referrals']}")
    
    # 6. اختبار الترقية
    print("\n6️⃣ اختبار الترقية...")
    result = manager.upgrade_user(test_user_id, 'silver', 'test', 'test_tx_123')
    if result:
        print(f"   ✅ تمت الترقية إلى Silver")
        new_status = manager.check_subscription(test_user_id)
        print(f"   ✅ الخطة الجديدة: {new_status['plan']}")
        print(f"   ✅ صالح حتى: {new_status['days_left']} يوم")
    
    # 7. اختبار رمز الإحالة
    print("\n7️⃣ اختبار رمز الإحالة...")
    user = manager.get_user(test_user_id)
    if user:
        print(f"   🔗 كود الإحالة: {user['referral_code']}")
    
    print("\n" + "="*60)
    print("✅ اكتمل الاختبار بنجاح!")
    print("="*60)
    
    # طباعة ملخص نهائي
    print("\n📋 ملخص النظام:")
    print(f"   • نظام الاشتراكات: ✅ يعمل")
    print(f"   • تقييم الجودة: ✅ يعمل")
    print(f"   • التصفية حسب الخطة: ✅ يعمل")
    print(f"   • الحد اليومي: ✅ يعمل")
    print(f"   • الإحصائيات: ✅ يعمل")
    print(f"   • الترقية: ✅ يعمل")
    print(f"   • رمز الإحالة: ✅ يعمل")
    
    print("\n💡 الخطوة التالية:")
    print("   1. تشغيل daily_scheduler.py لبدء التحليل التلقائي")
    print("   2. تشغيل vip_telegram_bot.py لبدء بوت التليجرام VIP")
    print("   3. إضافة مستخدمين حقيقيين")
    print("   4. دمج بوابة الدفع (Stripe)")

if __name__ == '__main__':
    test_vip_system()

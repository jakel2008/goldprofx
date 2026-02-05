"""
سكريبت اختبار النظام الموحد VIP
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """اختبار استيراد المكتبات"""
    print("\n🧪 اختبار الاستيرادات...")
    
    try:
        import requests
        print("   ✅ requests")
    except ImportError:
        print("   ❌ requests - قم بتثبيتها: pip install requests")
        return False
    
    try:
        import pandas
        print("   ✅ pandas")
    except ImportError:
        print("   ❌ pandas - قم بتثبيتها: pip install pandas")
        return False
    
    try:
        import ta
        print("   ✅ ta")
    except ImportError:
        print("   ❌ ta - قم بتثبيتها: pip install ta")
        return False
    
    try:
        import yfinance
        print("   ✅ yfinance")
    except ImportError:
        print("   ❌ yfinance - قم بتثبيتها: pip install yfinance")
        return False
    
    return True


def test_subscription_system():
    """اختبار نظام الاشتراكات"""
    print("\n🧪 اختبار نظام الاشتراكات...")
    
    try:
        from vip_subscription_system import SubscriptionManager
        
        sm = SubscriptionManager()
        print("   ✅ تم تحميل SubscriptionManager")
        
        # اختبار الحصول على المستخدمين النشطين
        active_users = sm.get_all_active_users()
        print(f"   ℹ️  المستخدمون النشطون: {len(active_users)}")
        
        # اختبار إنشاء مستخدم تجريبي
        test_user_id = 999999999
        success = sm.add_user(
            user_id=test_user_id,
            username="test_user",
            first_name="Test User"
        )
        
        if success:
            print("   ✅ تم إنشاء مستخدم تجريبي")
            
            # حذف المستخدم التجريبي
            import sqlite3
            conn = sqlite3.connect('vip_subscriptions.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = ?", (test_user_id,))
            conn.commit()
            conn.close()
            print("   ✅ تم حذف المستخدم التجريبي")
        else:
            print("   ⚠️  لم يتم إنشاء المستخدم (قد يكون موجوداً بالفعل)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return False


def test_quality_scorer():
    """اختبار نظام تقييم الجودة"""
    print("\n🧪 اختبار نظام تقييم الجودة...")
    
    try:
        from quality_scorer import add_quality_score, get_quality_threshold_for_plan
        
        # اختبار توصية وهمية
        test_signal = {
            'symbol': 'EURUSD',
            'recommendation': 'شراء قوي',
            'entry': 1.12345,
            'stop_loss': 1.12000,
            'take_profit': 1.13000,
            'rsi': 30,
            'macd': 0.0005,
            'macd_signal': 0.0003,
            'trend': 'صاعد',
            'trend_strength': 0.5,
            'ema_20': 1.12300,
            'ema_50': 1.12200,
            'close_price': 1.12345
        }
        
        scored_signal = add_quality_score(test_signal)
        quality_score = scored_signal.get('quality_score', 0)
        quality_level = scored_signal.get('quality_level', 'UNKNOWN')
        
        print(f"   ✅ تقييم الجودة: {quality_score}/100 ({quality_level})")
        
        # اختبار الحدود للخطط
        for plan in ['bronze', 'silver', 'gold', 'platinum']:
            threshold = get_quality_threshold_for_plan(plan)
            print(f"   ℹ️  {plan.upper()}: حد أدنى {threshold}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return False


def test_unified_bot():
    """اختبار البوت الموحد"""
    print("\n🧪 اختبار البوت الموحد...")
    
    try:
        from unified_vip_bot import (
            get_start_message,
            get_plans_message,
            format_signal_message,
            BOT_TOKEN
        )
        
        print(f"   ✅ تم تحميل البوت")
        print(f"   🔐 التوكن: {BOT_TOKEN[:20]}...")
        
        # اختبار توليد الرسائل
        start_msg = get_start_message()
        if start_msg and len(start_msg) > 0:
            print("   ✅ رسالة البداية: OK")
        
        plans_msg = get_plans_message()
        if plans_msg and "Bronze" in plans_msg:
            print("   ✅ رسالة الخطط: OK")
        
        # اختبار تنسيق التوصية
        test_signal = {
            'symbol': 'EURUSD',
            'rec': 'شراء قوي',
            'entry': 1.12345,
            'sl': 1.12000,
            'tp1': 1.12700,
            'tp2': 1.13000,
            'tp3': 1.13300,
            'tf': '1H',
            'rr': 2.5
        }
        
        formatted = format_signal_message(test_signal, 85, 'gold')
        if formatted and 'EURUSD' in formatted:
            print("   ✅ تنسيق التوصية: OK")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return False


def test_analyzer():
    """اختبار المحلل"""
    print("\n🧪 اختبار المحلل...")
    
    try:
        from auto_pairs_analyzer import analyze_pair
        
        print("   ⏳ جاري تحليل EURUSD (قد يستغرق بعض الوقت)...")
        
        analysis = analyze_pair('EURUSD', '1h')
        
        if analysis:
            print(f"   ✅ التحليل: {analysis.get('recommendation', 'N/A')}")
            print(f"   ℹ️  السعر: {analysis.get('entry', 0):.5f}")
        else:
            print("   ⚠️  لم يتم توليد توصية (قد يكون السوق في وضع حياد)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return False


def test_database():
    """اختبار قاعدة البيانات"""
    print("\n🧪 اختبار قاعدة البيانات...")
    
    try:
        import sqlite3
        import os
        
        db_path = 'vip_subscriptions.db'
        
        if os.path.exists(db_path):
            print(f"   ✅ قاعدة البيانات موجودة: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # عدد المستخدمين
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"   ℹ️  إجمالي المستخدمين: {user_count}")
            
            # عدد التوصيات المرسلة
            cursor.execute("SELECT COUNT(*) FROM signals_sent")
            signal_count = cursor.fetchone()[0]
            print(f"   ℹ️  إجمالي التوصيات المرسلة: {signal_count}")
            
            conn.close()
        else:
            print(f"   ⚠️  قاعدة البيانات غير موجودة - سيتم إنشاؤها عند أول تشغيل")
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return False


def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*60)
    print("🔬 بدء اختبار النظام الموحد VIP")
    print("="*60)
    
    results = {
        'Imports': test_imports(),
        'Subscription System': test_subscription_system(),
        'Quality Scorer': test_quality_scorer(),
        'Unified Bot': test_unified_bot(),
        'Analyzer': test_analyzer(),
        'Database': test_database()
    }
    
    print("\n" + "="*60)
    print("📊 نتائج الاختبار")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n" + "="*60)
    print(f"📈 النتيجة النهائية: {passed}/{total} نجح")
    print("="*60)
    
    if passed == total:
        print("\n🎉 جميع الاختبارات نجحت! النظام جاهز للعمل")
    else:
        print("\n⚠️  بعض الاختبارات فشلت - راجع الأخطاء أعلاه")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    
    input("\n\n اضغط Enter للخروج...")
    
    sys.exit(0 if success else 1)

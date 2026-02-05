"""
اختبار سريع لنظام بث الإشارات
يختبر جميع المكونات للتأكد من عملها بشكل صحيح
"""

import os
import json
from datetime import datetime
from pathlib import Path

def test_1_check_files():
    """التحقق من وجود الملفات الضرورية"""
    print("\n" + "="*60)
    print("🔍 اختبار 1: التحقق من الملفات")
    print("="*60)
    
    required_files = [
        'vip_bot_simple.py',
        'daily_scheduler.py',
        'signal_broadcaster.py',
        'auto_pairs_analyzer.py',
        'quality_scorer.py',
        'vip_subscription_system.py'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - غير موجود")
            missing.append(file)
    
    if missing:
        print(f"\n⚠️ ملفات مفقودة: {len(missing)}")
        return False
    else:
        print("\n✅ جميع الملفات موجودة")
        return True


def test_2_check_signals_dir():
    """التحقق من مجلد الإشارات"""
    print("\n" + "="*60)
    print("🔍 اختبار 2: مجلد الإشارات")
    print("="*60)
    
    signals_dir = Path('signals')
    
    if signals_dir.exists():
        signals = list(signals_dir.glob('*.json'))
        print(f"✅ المجلد موجود")
        print(f"📊 عدد الإشارات المحفوظة: {len(signals)}")
        
        if signals:
            # عرض أحدث 3 إشارات
            recent = sorted(signals, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
            print("\n📋 آخر 3 إشارات:")
            for sig in recent:
                mtime = datetime.fromtimestamp(sig.stat().st_mtime)
                print(f"   • {sig.name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("⚠️ لا توجد إشارات محفوظة حالياً")
            print("💡 سيتم إنشاء الإشارات عند تشغيل المحلل التلقائي")
        
        return True
    else:
        print(f"❌ المجلد غير موجود")
        print("💡 سيتم إنشاءه تلقائياً عند تشغيل المحلل")
        os.makedirs(signals_dir)
        print("✅ تم إنشاء المجلد")
        return True


def test_3_create_test_signal():
    """إنشاء إشارة تجريبية"""
    print("\n" + "="*60)
    print("🔍 اختبار 3: إنشاء إشارة تجريبية")
    print("="*60)
    
    test_signal = {
        'symbol': 'EURUSD',
        'rec': 'BUY',
        'entry': 1.0850,
        'sl': 1.0800,
        'tp1': 1.0900,
        'tp2': 1.0950,
        'tp3': 1.1000,
        'tf': '5m',
        'timestamp': datetime.now().isoformat(),
        'recommendation': 'شراء قوي'
    }
    
    signals_dir = Path('signals')
    signals_dir.mkdir(exist_ok=True)
    
    test_file = signals_dir / f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_signal, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم إنشاء إشارة تجريبية")
        print(f"📁 الملف: {test_file}")
        print(f"📊 البيانات:")
        print(f"   • الزوج: {test_signal['symbol']}")
        print(f"   • النوع: {test_signal['rec']}")
        print(f"   • الدخول: {test_signal['entry']}")
        print(f"   • وقف الخسارة: {test_signal['sl']}")
        print(f"   • أهداف الربح: {test_signal['tp1']}, {test_signal['tp2']}, {test_signal['tp3']}")
        return True
    except Exception as e:
        print(f"❌ فشل إنشاء الإشارة: {e}")
        return False


def test_4_check_sent_signals():
    """التحقق من سجل الإشارات المرسلة"""
    print("\n" + "="*60)
    print("🔍 اختبار 4: سجل الإشارات المرسلة")
    print("="*60)
    
    sent_file = Path('sent_signals.json')
    
    if sent_file.exists():
        try:
            with open(sent_file, 'r', encoding='utf-8') as f:
                sent = json.load(f)
            
            print(f"✅ السجل موجود")
            print(f"📊 عدد الإشارات المرسلة: {len(sent)}")
            
            if sent:
                # عرض آخر 3 إشارات مرسلة
                recent = sent[-3:]
                print("\n📋 آخر 3 إشارات مرسلة:")
                for sig in recent:
                    print(f"   • {sig['signal_id']}")
                    print(f"     وقت الإرسال: {sig['sent_at']}")
            else:
                print("ℹ️ لم يتم إرسال أي إشارات بعد")
            
            return True
        except Exception as e:
            print(f"⚠️ خطأ في قراءة السجل: {e}")
            return False
    else:
        print("ℹ️ السجل غير موجود (سيتم إنشاءه عند أول إرسال)")
        return True


def test_5_check_database():
    """التحقق من قاعدة البيانات"""
    print("\n" + "="*60)
    print("🔍 اختبار 5: قاعدة بيانات الاشتراكات")
    print("="*60)
    
    db_file = Path('vip_subscriptions.db')
    
    if db_file.exists():
        print(f"✅ قاعدة البيانات موجودة")
        
        try:
            from vip_subscription_system import SubscriptionManager
            sm = SubscriptionManager()
            users = sm.get_all_active_users()
            
            print(f"📊 عدد المشتركين النشطين: {len(users)}")
            
            # إحصائيات حسب الخطة
            plans_count = {}
            for user_data in users:
                if isinstance(user_data, dict):
                    plan = user_data.get('plan', 'free')
                else:
                    plan = user_data[1] if len(user_data) > 1 else 'free'
                
                plans_count[plan] = plans_count.get(plan, 0) + 1
            
            if plans_count:
                print("\n📊 توزيع الخطط:")
                for plan, count in plans_count.items():
                    print(f"   • {plan}: {count} مشترك")
            
            return True
        except Exception as e:
            print(f"⚠️ خطأ في قراءة قاعدة البيانات: {e}")
            return False
    else:
        print("ℹ️ قاعدة البيانات غير موجودة (سيتم إنشاءها عند أول مشترك)")
        return True


def test_6_check_imports():
    """التحقق من المكتبات المطلوبة"""
    print("\n" + "="*60)
    print("🔍 اختبار 6: المكتبات المطلوبة")
    print("="*60)
    
    required_modules = [
        'requests',
        'pandas',
        'ta',
        'schedule',
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - غير مثبت")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️ مكتبات مفقودة: {len(missing)}")
        print(f"💡 لتثبيتها: pip install {' '.join(missing)}")
        return False
    else:
        print("\n✅ جميع المكتبات مثبتة")
        return True


def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*60)
    print("🧪 اختبار نظام بث الإشارات الكامل")
    print("="*60)
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tests = [
        test_1_check_files,
        test_2_check_signals_dir,
        test_3_create_test_signal,
        test_4_check_sent_signals,
        test_5_check_database,
        test_6_check_imports
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    # النتيجة النهائية
    print("\n" + "="*60)
    print("📊 النتيجة النهائية")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ نجح: {passed}/{total}")
    print(f"❌ فشل: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 جميع الاختبارات نجحت!")
        print("\n✨ النظام جاهز للعمل:")
        print("   1. شغل المحلل التلقائي: daily_scheduler.py")
        print("   2. شغل البوت: START_VIP_BOT.bat")
        print("   3. شغل بث الإشارات: START_SIGNAL_BROADCASTER.bat")
        print("\n   أو استخدم: START_ALL_SYSTEMS.bat لتشغيل كل شيء معاً")
    else:
        print("\n⚠️ بعض الاختبارات فشلت")
        print("💡 راجع الأخطاء أعلاه وصححها")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n❌ تم إيقاف الاختبار")
    except Exception as e:
        print(f"\n\n❌ خطأ غير متوقع: {e}")
    
    input("\n\nاضغط Enter للإغلاق...")

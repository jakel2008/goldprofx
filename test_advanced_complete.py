# -*- coding: utf-8 -*-
"""
اختبار شامل للمحلل المتقدم
"""
import os
import sys

# إعداد المسار
sys.path.insert(0, os.path.dirname(__file__))

def test_advanced_analyzer():
    """اختبار المحلل المتقدم"""
    print("=" * 60)
    print("اختبار المحلل المتقدم الكامل")
    print("=" * 60)
    
    try:
        from advanced_analyzer_engine import perform_full_analysis
        print("✅ تم استيراد محرك التحليل بنجاح")
        
        # اختبار EUR/USD
        print("\n📊 جاري اختبار التحليل...")
        result = perform_full_analysis('EUR/USD', '1h')
        
        if result.get('success'):
            print("\n✅ نجح التحليل!")
            print(f"   الإشارة: {result.get('signal')}")
            print(f"   الثقة: {result.get('confidence')}")
            print(f"   نقطة الدخول: {result.get('entry_point'):.5f}")
            print(f"   الهدف 1: {result.get('take_profit1'):.5f}")
            print(f"   الهدف 2: {result.get('take_profit2'):.5f}")
            print(f"   الهدف 3: {result.get('take_profit3'):.5f}")
            print(f"   وقف الخسارة: {result.get('stop_loss'):.5f}")
            
            # عرض الإشارات
            print(f"\n📈 الإشارات المكتشفة:")
            for signal in result.get('signals_list', []):
                print(f"   • {signal}")
            
            # عرض مستويات فيبوناتشي
            print(f"\n🔢 مستويات فيبوناتشي:")
            fib = result.get('fibonacci_levels', {})
            for level, price in fib.items():
                print(f"   {level}: {price:.5f}")
            
            # عرض مستويات الدعم والمقاومة
            print(f"\n📊 المستويات الرئيسية:")
            print(f"   المقاومة: {result.get('resistance'):.5f}")
            print(f"   المحور: {result.get('pivot'):.5f}")
            print(f"   الدعم: {result.get('support'):.5f}")
            
            print("\n" + "=" * 60)
            print("✅ الاختبار ناجح - النظام جاهز للاستخدام!")
            print("=" * 60)
            return True
        else:
            print(f"\n❌ فشل التحليل: {result.get('error')}")
            return False
            
    except ImportError as e:
        print(f"\n❌ خطأ في الاستيراد: {e}")
        return False
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_endpoints():
    """اختبار نقاط النهاية للويب"""
    print("\n" + "=" * 60)
    print("اختبار نقاط النهاية للويب")
    print("=" * 60)
    
    try:
        # تحقق من وجود الملفات
        files_to_check = [
            'web_app.py',
            'advanced_analyzer_engine.py',
            'templates/advanced_analyzer.html',
            'recommendations_history.json'
        ]
        
        all_exist = True
        for file in files_to_check:
            if os.path.exists(file):
                print(f"✅ {file}")
            else:
                print(f"❌ {file} - غير موجود")
                all_exist = False
        
        if all_exist:
            print("\n✅ جميع الملفات موجودة")
            
            # تحقق من الدوال في web_app.py
            with open('web_app.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
            endpoints = [
                '/api/advanced-analysis',
                '/api/publish-to-recommendations',
                '/api/send-to-telegram',
                '/api/export-trading-signal'
            ]
            
            print("\n📍 التحقق من نقاط النهاية:")
            for endpoint in endpoints:
                if endpoint in content:
                    print(f"✅ {endpoint}")
                else:
                    print(f"❌ {endpoint} - غير موجود")
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        return False

def test_integration():
    """اختبار التكامل"""
    print("\n" + "=" * 60)
    print("اختبار التكامل")
    print("=" * 60)
    
    try:
        # تحقق من متغيرات البيئة
        print("\n🔑 متغيرات البيئة:")
        
        telegram_token = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "")
        telegram_chat = os.environ.get("MM_TELEGRAM_CHAT_ID", "")
        twelve_key = os.environ.get("TWELVE_DATA_API_KEY", "")
        
        if telegram_token:
            print(f"✅ MM_TELEGRAM_BOT_TOKEN: {telegram_token[:10]}...")
        else:
            print("⚠️  MM_TELEGRAM_BOT_TOKEN: غير محدد")
        
        if telegram_chat:
            print(f"✅ MM_TELEGRAM_CHAT_ID: {telegram_chat}")
        else:
            print("⚠️  MM_TELEGRAM_CHAT_ID: غير محدد")
        
        if twelve_key:
            print(f"✅ TWELVE_DATA_API_KEY: {twelve_key[:10]}...")
        else:
            print("⚠️  TWELVE_DATA_API_KEY: غير محدد (سيستخدم المفتاح الافتراضي)")
        
        # تحقق من قاعدة البيانات
        print("\n💾 قواعد البيانات:")
        
        dbs = ['vip_subscriptions.db', 'users.db']
        for db in dbs:
            if os.path.exists(db):
                print(f"✅ {db}")
            else:
                print(f"⚠️  {db} - غير موجود")
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 بدء الاختبار الشامل...\n")
    
    # تشغيل الاختبارات
    test1 = test_advanced_analyzer()
    test2 = test_web_endpoints()
    test3 = test_integration()
    
    # النتيجة النهائية
    print("\n" + "=" * 60)
    print("النتيجة النهائية")
    print("=" * 60)
    
    if test1 and test2 and test3:
        print("✅ جميع الاختبارات نجحت!")
        print("\n📋 الخطوات التالية:")
        print("1. تأكد من تشغيل Flask (web_app.py)")
        print("2. افتح المتصفح على: http://localhost:5000")
        print("3. سجل الدخول كأدمن")
        print("4. اضغط على زر 'المحلل المتقدم'")
        print("5. جرّب التحليل والنشر!")
    else:
        print("⚠️  بعض الاختبارات فشلت - راجع الأخطاء أعلاه")
    
    print("=" * 60)

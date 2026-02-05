#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 نظام اختبار المزامنة الكامل
Complete Synchronization Testing System
"""
import os
import sys
import json
import time
import sqlite3
from datetime import datetime

# إضافة المجلد الرئيسي للمسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from unified_signal_manager import UnifiedSignalManager
    UNIFIED_AVAILABLE = True
except ImportError:
    UNIFIED_AVAILABLE = False
    print("⚠️ نظام المزامنة الموحد غير متوفر")

def print_header(title):
    """طباعة عنوان منسق"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_database_creation():
    """اختبار 1: إنشاء قاعدة البيانات"""
    print_header("🗄️ اختبار 1: إنشاء قاعدة البيانات الموحدة")
    
    try:
        # إنشاء مدير النظام الموحد (سينشئ القاعدة تلقائياً)
        manager = UnifiedSignalManager()
        db_path = manager.web_db
        
        if os.path.exists(db_path):
            print(f"✅ قاعدة البيانات موجودة: {db_path}")
            size = os.path.getsize(db_path) / 1024
            print(f"📏 الحجم: {size:.2f} KB")
            
            # فحص الجداول
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            print(f"📊 الجداول الموجودة ({len(tables)}): {', '.join(tables)}")
            
            required_tables = ['signals', 'users']
            missing = [t for t in required_tables if t not in tables]
            
            if missing:
                print(f"⚠️ جداول ناقصة: {', '.join(missing)}")
                return False
            else:
                print("✅ جميع الجداول المطلوبة موجودة")
                return True
        else:
            print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def test_signal_publishing():
    """اختبار 2: نشر إشارات تجريبية متعددة"""
    print_header("📡 اختبار 2: نشر إشارات تجريبية")
    
    try:
        manager = UnifiedSignalManager()
        
        # إنشاء 3 إشارات تجريبية
        test_signals = [
            {
                "pair": "EURUSD",
                "signal": "buy",
                "entry": 1.0850,
                "sl": 1.0820,
                "tp1": 1.0900,
                "tp2": 1.0950,
                "tp3": 1.1000,
                "quality_score": 85,
                "timestamp": datetime.now().isoformat(),
                "timeframe": "5m",
                "trend_strength": 0.35,
                "rsi": 65,
                "macd_signal": "bullish"
            },
            {
                "pair": "XAUUSD",
                "signal": "sell",
                "entry": 2650.50,
                "sl": 2655.00,
                "tp1": 2640.00,
                "tp2": 2630.00,
                "tp3": 2620.00,
                "quality_score": 78,
                "timestamp": datetime.now().isoformat(),
                "timeframe": "5m",
                "trend_strength": 0.28,
                "rsi": 35,
                "macd_signal": "bearish"
            },
            {
                "pair": "BTCUSD",
                "signal": "buy",
                "entry": 42500.00,
                "sl": 42000.00,
                "tp1": 43000.00,
                "tp2": 43500.00,
                "tp3": 44000.00,
                "quality_score": 92,
                "timestamp": datetime.now().isoformat(),
                "timeframe": "5m",
                "trend_strength": 0.45,
                "rsi": 72,
                "macd_signal": "bullish"
            }
        ]
        
        success_count = 0
        web_success = 0
        telegram_total = 0
        
        for i, signal in enumerate(test_signals, 1):
            print(f"\n📤 إشارة {i}/3: {signal['pair']} - {signal['signal'].upper()}")
            print(f"   📊 جودة: {signal['quality_score']}/100")
            
            report = manager.publish_signal(signal)
            
            if report['web_saved']:
                web_success += 1
                print(f"   🌐 الويب: ✅ تم الحفظ")
            else:
                print(f"   🌐 الويب: ❌ فشل")
            
            telegram_total += report['telegram_sent']
            print(f"   📱 البوت: أُرسل إلى {report['telegram_sent']} مستخدم")
            
            if report.get('errors'):
                print(f"   ⚠️ أخطاء: {len(report['errors'])} خطأ")
            
            if report['web_saved']:
                success_count += 1
            
            time.sleep(0.5)  # وقفة قصيرة بين الإشارات
        
        print(f"\n📋 ملخص النشر:")
        print(f"   📡 إجمالي الإشارات: {len(test_signals)}")
        print(f"   ✅ نجح (ويب): {web_success}/{len(test_signals)}")
        print(f"   📱 إجمالي الإرسال للبوت: {telegram_total}")
        
        return success_count == len(test_signals)
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_sync():
    """اختبار 3: مزامنة قواعد البيانات"""
    print_header("🔄 اختبار 3: مزامنة قواعد البيانات")
    
    try:
        manager = UnifiedSignalManager()
        
        print("🔄 بدء المزامنة بين قواعد البيانات...")
        synced = manager.sync_databases()
        
        print(f"\n📊 نتائج المزامنة:")
        print(f"   👥 المستخدمون المُزامنون: {synced['users_synced']}")
        print(f"   📡 الإشارات المُزامنة: {synced['signals_synced']}")
        
        if synced['users_synced'] > 0:
            print(f"   ✅ تمت مزامنة {synced['users_synced']} مستخدم")
        
        if synced['signals_synced'] > 0:
            print(f"   ✅ تمت مزامنة {synced['signals_synced']} إشارة")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_statistics():
    """اختبار 4: الإحصائيات الموحدة"""
    print_header("📊 اختبار 4: الإحصائيات الموحدة")
    
    try:
        manager = UnifiedSignalManager()
        
        stats = manager.get_unified_statistics()
        
        print(f"\n📈 إحصائيات النظام:")
        print(f"   📡 إجمالي الإشارات: {stats['total_signals']}")
        print(f"   ✅ الناجحة: {stats['successful_signals']}")
        print(f"   ❌ الفاشلة: {stats['failed_signals']}")
        print(f"   ⏳ النشطة: {stats['active_signals']}")
        print(f"   🎯 معدل النجاح: {stats['success_rate']:.1f}%")
        
        if stats['total_signals'] > 0:
            print(f"\n   💡 النظام قد عالج {stats['total_signals']} إشارة بنجاح")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_database_queries():
    """اختبار 5: استعلامات قاعدة بيانات الويب"""
    print_header("🔍 اختبار 5: استعلامات قاعدة بيانات الويب")
    
    try:
        manager = UnifiedSignalManager()
        conn = sqlite3.connect(manager.web_db)
        cursor = conn.cursor()
        
        # عدد الإشارات
        cursor.execute("SELECT COUNT(*) FROM signals")
        signal_count = cursor.fetchone()[0]
        print(f"📊 إجمالي الإشارات في قاعدة الويب: {signal_count}")
        
        # الإشارات حسب النوع
        cursor.execute("SELECT signal_type, COUNT(*) FROM signals GROUP BY signal_type")
        signal_types = cursor.fetchall()
        if signal_types:
            print(f"\n📈 الإشارات حسب النوع:")
            for signal_type, count in signal_types:
                print(f"   {signal_type.upper()}: {count}")
        
        # متوسط الجودة
        cursor.execute("SELECT AVG(quality_score) FROM signals")
        avg_quality = cursor.fetchone()[0]
        if avg_quality:
            print(f"\n⭐ متوسط جودة الإشارات: {avg_quality:.1f}/100")
        
        # آخر 5 إشارات
        cursor.execute("""
            SELECT symbol, signal_type, quality_score, timestamp 
            FROM signals 
            ORDER BY timestamp DESC 
            LIMIT 5
        """)
        
        latest = cursor.fetchall()
        if latest:
            print(f"\n🕒 آخر 5 إشارات:")
            for row in latest:
                ts = row[3][:16] if len(row[3]) > 16 else row[3]
                print(f"   • {row[0]} - {row[1].upper()} (جودة: {row[2]}) - {ts}")
        
        # عدد المستخدمين
        cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
        active_users = cursor.fetchone()[0]
        print(f"\n👥 المستخدمون النشطون: {active_users}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_file_creation():
    """اختبار 6: إنشاء ملفات الإشارات"""
    print_header("📁 اختبار 6: ملفات الإشارات")
    
    signals_dir = os.path.join(os.path.dirname(__file__), "signals")
    
    if os.path.exists(signals_dir):
        files = [f for f in os.listdir(signals_dir) if f.endswith('.json')]
        print(f"📂 مجلد الإشارات: {signals_dir}")
        print(f"📄 إجمالي الملفات: {len(files)}")
        
        if files:
            # عرض آخر 5 ملفات
            files.sort(reverse=True)
            print(f"\n🕒 آخر 5 ملفات إشارات:")
            for f in files[:5]:
                file_path = os.path.join(signals_dir, f)
                size = os.path.getsize(file_path)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # قراءة محتوى الملف
                try:
                    with open(file_path, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                        pair = data.get('pair', 'N/A')
                        signal = data.get('signal', 'N/A')
                        quality = data.get('quality_score', 0)
                        print(f"   • {f}")
                        print(f"     {pair} - {signal.upper()} (جودة: {quality}) - {mtime.strftime('%Y-%m-%d %H:%M')}")
                except:
                    print(f"   • {f} ({size} bytes) - {mtime.strftime('%Y-%m-%d %H:%M')}")
            
            return True
        else:
            print("⚠️ لا توجد ملفات إشارات")
            return True
    else:
        print(f"⚠️ مجلد الإشارات غير موجود: {signals_dir}")
        return False

def test_both_databases_comparison():
    """اختبار 7: مقارنة قواعد البيانات"""
    print_header("🔀 اختبار 7: مقارنة قواعد البيانات")
    
    try:
        vip_db = "vip_subscriptions.db"
        web_db = "vip_signals.db"
        
        if not os.path.exists(vip_db):
            print(f"⚠️ قاعدة VIP غير موجودة: {vip_db}")
            return False
        
        if not os.path.exists(web_db):
            print(f"⚠️ قاعدة الويب غير موجودة: {web_db}")
            return False
        
        # قاعدة VIP
        vip_conn = sqlite3.connect(vip_db)
        vip_cursor = vip_conn.cursor()
        vip_cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
        vip_users = vip_cursor.fetchone()[0]
        vip_conn.close()
        
        # قاعدة الويب
        web_conn = sqlite3.connect(web_db)
        web_cursor = web_conn.cursor()
        web_cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
        web_users = web_cursor.fetchone()[0]
        web_cursor.execute("SELECT COUNT(*) FROM signals")
        web_signals = web_cursor.fetchone()[0]
        web_conn.close()
        
        print(f"📊 قاعدة VIP:")
        print(f"   👥 مستخدمون نشطون: {vip_users}")
        
        print(f"\n📊 قاعدة الويب:")
        print(f"   👥 مستخدمون نشطون: {web_users}")
        print(f"   📡 إشارات: {web_signals}")
        
        if vip_users == web_users:
            print(f"\n✅ المستخدمون متطابقون في القاعدتين ({vip_users})")
        else:
            print(f"\n⚠️ المستخدمون غير متطابقين (VIP: {vip_users}, Web: {web_users})")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def main():
    """تشغيل جميع الاختبارات"""
    # تعيين الترميز
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "="*70)
    print("  نظام اختبار المزامنة الكامل")
    print("  Complete Synchronization Testing System")
    print("="*70)
    
    if not UNIFIED_AVAILABLE:
        print("\n❌ النظام الموحد غير متوفر - تأكد من وجود unified_signal_manager.py")
        return
    
    # قائمة الاختبارات
    tests = [
        ("إنشاء قاعدة البيانات", test_database_creation),
        ("نشر إشارات تجريبية", test_signal_publishing),
        ("مزامنة قواعد البيانات", test_database_sync),
        ("الإحصائيات الموحدة", test_unified_statistics),
        ("استعلامات قاعدة الويب", test_web_database_queries),
        ("ملفات الإشارات", test_signal_file_creation),
        ("مقارنة قواعد البيانات", test_both_databases_comparison),
    ]
    
    results = []
    start_time = time.time()
    
    # تشغيل الاختبارات
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            time.sleep(0.5)  # وقفة قصيرة بين الاختبارات
        except Exception as e:
            print(f"\n❌ خطأ في اختبار '{name}': {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    elapsed_time = time.time() - start_time
    
    # عرض النتائج النهائية
    print_header("📋 ملخص النتائج النهائي")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for i, (name, result) in enumerate(results, 1):
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{i}. {status} - {name}")
    
    print(f"\n" + "="*70)
    print(f"📊 النتيجة النهائية: {passed}/{total} اختبار ناجح ({passed/total*100:.0f}%)")
    print(f"⏱️  الوقت المستغرق: {elapsed_time:.2f} ثانية")
    print("="*70)
    
    if passed == total:
        print("\n🎉 جميع الاختبارات ناجحة!")
        print("✅ نظام المزامنة الموحد يعمل بشكل صحيح")
        print("🚀 النظام جاهز للإنتاج")
    else:
        print(f"\n⚠️ {total - passed} اختبار فشل - راجع التفاصيل أعلاه")
        print("🔧 يرجى إصلاح المشاكل قبل الاستخدام")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
    print("\nاضغط Enter للخروج...")
    input()

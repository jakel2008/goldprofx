# -*- coding: utf-8 -*-
"""
جدولة التقارير الدورية التلقائية
Automatic Periodic Reports Scheduler
"""

import os
import time
import schedule
from datetime import datetime
from periodic_reports import PeriodicReports

os.system('chcp 65001 > nul')

# إنشاء مولد التقارير
reports_gen = PeriodicReports()

def send_hourly_summary():
    """إرسال ملخص ساعي للإشارات النشطة"""
    from datetime import timedelta
    import sqlite3
    
    now = datetime.now()
    print(f"\n{'='*70}")
    print(f"📊 ملخص ساعي للنظام - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        conn = sqlite3.connect('vip_signals.db')
        c = conn.cursor()
        
        # إحصائيات آخر ساعة
        one_hour_ago = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        c.execute('SELECT COUNT(*) FROM signals WHERE created_at >= ?', (one_hour_ago,))
        signals_last_hour = c.fetchone()[0]
        
        # إحصائيات اليوم
        today = now.strftime('%Y-%m-%d')
        c.execute('SELECT COUNT(*), AVG(quality_score) FROM signals WHERE DATE(created_at) = ?', (today,))
        today_count, today_avg_quality = c.fetchone()
        today_avg_quality = today_avg_quality or 0
        
        conn.close()
        
        print(f"""
📊 ملخص آخر ساعة:
  🆕 إشارات جديدة: {signals_last_hour}
  
📅 إحصائيات اليوم:
  📈 إجمالي الإشارات: {today_count or 0}
  ⭐ متوسط الجودة: {today_avg_quality:.1f}/100
  
✅ النظام يعمل بشكل طبيعي
""")
        print("\n✅ تم توليد الملخص بنجاح\n")
    except Exception as e:
        print(f"\n❌ خطأ في الملخص الساعي: {e}\n")

def send_daily_report():
    """إرسال التقرير اليومي"""
    print(f"\n{'='*70}")
    print(f"📊 توليد التقرير اليومي - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        report = reports_gen.generate_daily_report()
        print(report)
        print("\n✅ تم توليد التقرير اليومي بنجاح\n")
    except Exception as e:
        print(f"\n❌ خطأ في التقرير اليومي: {e}\n")

def send_weekly_report():
    """إرسال التقرير الأسبوعي"""
    print(f"\n{'='*70}")
    print(f"📊 توليد التقرير الأسبوعي - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        report = reports_gen.generate_weekly_report()
        print(report)
        print("\n✅ تم توليد التقرير الأسبوعي بنجاح\n")
    except Exception as e:
        print(f"\n❌ خطأ في التقرير الأسبوعي: {e}\n")

def main():
    """البرنامج الرئيسي"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           📊 جدولة التقارير الدورية التلقائية            ║
║                                                            ║
║  ⏰ التقرير الساعي: كل ساعة في الدقيقة 55                ║
║  📅 التقرير اليومي: كل يوم الساعة 23:55                  ║
║  📆 التقرير الأسبوعي: كل أحد الساعة 23:50                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    print("🚀 بدء نظام التقارير الدورية...\n")
    
    # جدولة التقارير
    schedule.every().hour.at(":55").do(send_hourly_summary)  # كل ساعة في الدقيقة 55
    schedule.every().day.at("23:55").do(send_daily_report)  # كل يوم الساعة 23:55
    schedule.every().sunday.at("23:50").do(send_weekly_report)  # كل أحد الساعة 23:50
    
    print("✅ تم جدولة التقارير:")
    print("  ⏰ ملخص ساعي: كل ساعة في :55")
    print("  📅 اليومي: كل يوم 23:55")
    print("  📆 الأسبوعي: كل أحد 23:50\n")
    
    # إرسال ملخص فوري عند البدء
    print("⚡ إرسال ملخص فوري الآن...\n")
    send_hourly_summary()
    
    print("\n🔄 النظام يعمل الآن... اضغط Ctrl+C للإيقاف\n")
    
    # حلقة لا نهائية لتشغيل المهام المجدولة
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # فحص كل 30 ثانية
            
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف نظام التقارير الدورية")
        print(f"🕒 وقت الإيقاف: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    main()

"""
سكريبت جدولة التحليل التلقائي الشامل يومياً
يعمل في الخلفية ويحلل جميع الأزواج تلقائياً ويراقب الصفقات
"""

import schedule
import time
import sys
from datetime import datetime
from auto_pairs_analyzer import run_daily_analysis, run_hourly_5min_analysis
from monitor_trades import monitor_and_report

# معالجة الترميز
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def continuous_job():
    """تشغيل التحليل المستمر (كل 5 دقائق)"""
    run_hourly_5min_analysis()

def monitor_job():
    """تشغيل المراقبة"""
    try:
        monitor_and_report()
    except Exception as e:
        print(f"خطأ في المراقبة: {e}")

def hourly_report_job():
    """تقرير الصفقات المنتهية كل ساعة"""
    try:
        send_hourly_closed_report()
    except Exception as e:
        print(f"خطأ في تقرير الساعة: {e}")

def daily_job():
    """المهمة المجدولة اليومية"""
    print(f"[{datetime.now()}] جاري تشغيل التحليل الشامل...")
    run_daily_analysis()
    print(f"[{datetime.now()}] انتهى التحليل")

def start_scheduler():
    """بدء جدولة المهام"""
    # تشغيل التحليل يومياً في الساعة 22:00 (افتتاح السوق)
    schedule.every().day.at("22:00").do(daily_job)

    # تشغيل تحليل فريم 5 دقائق لكل الأزواج كل 5 دقائق (تحليل مستمر)
    schedule.every(5).minutes.do(continuous_job)
    
    # تشغيل المراقبة بشكل دائم (كل 5 دقائق) لتحديث موقف الصفقات وإرسال التقرير
    schedule.every(5).minutes.do(monitor_job)
    
    print("جدولة التحليل والمراقبة:")
    print("يومياً في 22:00 UTC - تحليل شامل")
    print("كل 5 دقائق - تحليل 5 دقائق + حفظ توصيات")
    print("كل 5 دقائق - مراقبة الصفقات وتحديثات الحالة + تقرير")
    print(f"تاريخ البدء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # تشغيل التحليل مرة واحدة عند البدء
    print("\nتشغيل التحليل الأولي...")
    try:
        run_hourly_5min_analysis()
        print("تم التحليل الأولي بنجاح")
    except Exception as e:
        print(f"خطأ في التحليل الأولي: {e}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # تحقق كل دقيقة

if __name__ == "__main__":
    try:
        start_scheduler()
    except KeyboardInterrupt:
        print("\n❌ تم إيقاف الجدولة")

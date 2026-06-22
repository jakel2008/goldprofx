"""
سكريبت جدولة التحليل التلقائي الشامل يومياً
يعمل في الخلفية ويحلل جميع الأزواج تلقائياً ويراقب الصفقات
"""

import schedule
import time
import sys
import os
import atexit
import ctypes
from datetime import datetime
from auto_pairs_analyzer import run_daily_analysis, run_hourly_5min_analysis
from monitor_trades import monitor_and_report, send_hourly_closed_report

# معالجة الترميز
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

LOCK_FILE = os.path.join(os.path.dirname(__file__), "daily_scheduler.lock")
MUTEX_NAME = "Global\\GOLD_PRO_DAILY_SCHEDULER"
_MUTEX_HANDLE = None


def _pid_is_running(pid: int) -> bool:
    """التحقق إذا كانت العملية ما زالت تعمل."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _release_lock() -> None:
    """تحرير قفل التشغيل عند الإغلاق."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass


def _release_mutex() -> None:
    """تحرير Mutex في ويندوز عند الإغلاق."""
    global _MUTEX_HANDLE
    try:
        if _MUTEX_HANDLE:
            ctypes.windll.kernel32.CloseHandle(_MUTEX_HANDLE)
            _MUTEX_HANDLE = None
    except Exception:
        pass


def acquire_single_instance_lock() -> bool:
    """منع تشغيل أكثر من نسخة من المجدول في نفس الوقت."""
    global _MUTEX_HANDLE

    # على ويندوز: Mutex النظام أكثر موثوقية من ملف القفل.
    if os.name == 'nt':
        try:
            _MUTEX_HANDLE = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
            already_exists = ctypes.GetLastError() == 183  # ERROR_ALREADY_EXISTS
            if already_exists:
                print("❌ المجدول يعمل بالفعل (mutex lock)")
                return False
            atexit.register(_release_mutex)
            return True
        except Exception as e:
            print(f"⚠️ فشل mutex lock، الرجوع لملف القفل: {e}")

    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r', encoding='utf-8') as f:
                old_pid = int((f.read() or "0").strip())
            if _pid_is_running(old_pid):
                print(f"❌ المجدول يعمل بالفعل (PID={old_pid})")
                return False
        except Exception:
            pass

        try:
            os.remove(LOCK_FILE)
        except Exception:
            print("❌ تعذر إزالة ملف القفل القديم")
            return False

    try:
        with open(LOCK_FILE, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"❌ تعذر إنشاء ملف القفل: {e}")
        return False

    atexit.register(_release_lock)
    return True

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
        if not acquire_single_instance_lock():
            raise SystemExit(1)
        start_scheduler()
    except KeyboardInterrupt:
        print("\n❌ تم إيقاف الجدولة")
    finally:
        _release_lock()

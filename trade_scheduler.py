# -*- coding: utf-8 -*-
"""
جدولة الصيانة التلقائية للصفقات
يعمل في الخلفية ويدير الصفقات حسب أوقات الأسواق
"""

import os
import schedule
import time
from datetime import datetime
from smart_trade_manager import SmartTradeManager
from market_hours import MarketHours

os.system('chcp 65001 > nul')

class TradeScheduler:
    """مجدول الصيانة التلقائية"""
    
    def __init__(self):
        self.manager = SmartTradeManager()
        self.market_hours = MarketHours()
    
    def daily_maintenance_job(self):
        """وظيفة الصيانة اليومية"""
        print(f"\n{'='*70}")
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        self.manager.daily_maintenance()
    
    def weekly_reset_job(self):
        """وظيفة إعادة التعيين الأسبوعية"""
        print(f"\n{'='*70}")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        self.manager.weekly_reset()
    
    def market_open_check(self):
        """فحص افتتاح الأسواق وإعادة تنشيط الصفقات"""
        # فحص الفوركس
        if self.market_hours.is_forex_open():
            stats = self.manager.reactivate_market_open_trades()
            if stats['reactivated_count'] > 0:
                print(f"▶️  تم إعادة تنشيط {stats['reactivated_count']} صفقة فوركس")
        
        # فحص الأسهم الأمريكية
        if self.market_hours.is_us_stock_market_open():
            print("✅ سوق الأسهم الأمريكية مفتوح")
    
    def market_close_check(self):
        """فحص إغلاق الأسواق وتعليق الصفقات"""
        stats = self.manager.suspend_closed_market_trades()
        if stats['suspended_count'] > 0:
            print(f"⏸️  تم تعليق {stats['suspended_count']} صفقة (أسواق مغلقة)")
    
    def setup_schedule(self):
        """إعداد الجدول الزمني"""
        
        # الصيانة اليومية - كل يوم الساعة 00:05
        schedule.every().day.at("00:05").do(self.daily_maintenance_job)
        
        # إعادة التعيين الأسبوعية - كل أحد الساعة 22:05 GMT
        schedule.every().sunday.at("22:05").do(self.weekly_reset_job)
        
        # فحص افتتاح الفوركس - الأحد 22:10 GMT
        schedule.every().sunday.at("22:10").do(self.market_open_check)
        
        # فحص إغلاق الفوركس - الجمعة 22:00 GMT
        schedule.every().friday.at("22:00").do(self.market_close_check)
        
        # فحص افتتاح سوق الأسهم - الإثنين-الجمعة 09:35 EST
        schedule.every().monday.at("09:35").do(self.market_open_check)
        schedule.every().tuesday.at("09:35").do(self.market_open_check)
        schedule.every().wednesday.at("09:35").do(self.market_open_check)
        schedule.every().thursday.at("09:35").do(self.market_open_check)
        schedule.every().friday.at("09:35").do(self.market_open_check)
        
        # فحص إغلاق سوق الأسهم - الإثنين-الجمعة 16:05 EST
        schedule.every().monday.at("16:05").do(self.market_close_check)
        schedule.every().tuesday.at("16:05").do(self.market_close_check)
        schedule.every().wednesday.at("16:05").do(self.market_close_check)
        schedule.every().thursday.at("16:05").do(self.market_close_check)
        schedule.every().friday.at("16:05").do(self.market_close_check)
        
        # فحص دوري كل 4 ساعات
        schedule.every(4).hours.do(self.market_open_check)
    
    def run(self):
        """تشغيل المجدول"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         ⏰ جدولة الصيانة التلقائية للصفقات                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

📋 الجدول الزمني:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔹 صيانة يومية: كل يوم الساعة 00:05
  🔹 إعادة تعيين أسبوعية: الأحد 22:05 GMT
  🔹 فحص افتتاح الفوركس: الأحد 22:10 GMT
  🔹 فحص إغلاق الفوركس: الجمعة 22:00 GMT
  🔹 فحص افتتاح الأسهم: الإثنين-الجمعة 09:35 EST
  🔹 فحص إغلاق الأسهم: الإثنين-الجمعة 16:05 EST
  🔹 فحص دوري: كل 4 ساعات

🚀 النظام يعمل الآن...
اضغط Ctrl+C للإيقاف
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
        # إعداد الجدول
        self.setup_schedule()
        
        # تنفيذ الصيانة الأولى فوراً
        print("\n⚡ تنفيذ الصيانة الأولية...\n")
        self.daily_maintenance_job()
        
        print(f"\n✅ الجدول الزمني نشط - التحديث التالي في: {schedule.next_run()}\n")
        
        # حلقة التنفيذ
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # فحص كل دقيقة
        except KeyboardInterrupt:
            print("\n\n⏹️  تم إيقاف جدولة الصيانة")
            print(f"🕒 وقت الإيقاف: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    scheduler = TradeScheduler()
    scheduler.run()

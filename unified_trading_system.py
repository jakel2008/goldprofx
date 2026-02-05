"""
النظام الموحد للتداول والتقارير
Unified Trading & Reporting System
"""

import schedule
import time
import threading
from datetime import datetime
from trade_statistics import TradeStatistics
from periodic_reports import PeriodicReports
import json
from pathlib import Path

class UnifiedTradingSystem:
    def __init__(self):
        self.stats = TradeStatistics()
        self.reports = PeriodicReports()
        self.is_running = False
        self.scheduler_thread = None
        self.bot_thread = None
        self.analyzer_thread = None
        self.broadcaster_thread = None
        print("🚀 النظام الموحد للتداول والتقارير")
        print("=" * 60)

        # استيراد الأنظمة الفرعية
        import importlib
        self.bot_module = importlib.import_module("vip_bot_simple")
        self.analyzer_module = importlib.import_module("auto_pairs_analyzer")
        self.broadcaster_module = importlib.import_module("signal_broadcaster")

    def run_bot(self):
        # تشغيل البوت VIP
        try:
            self.bot_module.main()
        except Exception as e:
            print(f"❌ خطأ في تشغيل البوت: {e}")

    def run_analyzer(self):
        # تشغيل المحلل التلقائي
        try:
            if hasattr(self.analyzer_module, "main"):
                self.analyzer_module.main()
            elif hasattr(self.analyzer_module, "run_hourly_5min_analysis"):
                self.analyzer_module.run_hourly_5min_analysis()
            else:
                print("⚠️ لا توجد دالة رئيسية للمحلل")
        except Exception as e:
            print(f"❌ خطأ في تشغيل المحلل: {e}")

    def run_broadcaster(self):
        # تشغيل نظام البث
        try:
            if hasattr(self.broadcaster_module, "main"):
                self.broadcaster_module.main()
            elif hasattr(self.broadcaster_module, "broadcast_signals"):
                self.broadcaster_module.broadcast_signals()
            else:
                print("⚠️ لا توجد دالة رئيسية للبث")
        except Exception as e:
            print(f"❌ خطأ في تشغيل البث: {e}")
    
    def start(self):
        """تشغيل النظام"""
        self.is_running = True
        # جدولة التقارير
        self.schedule_reports()
        # بدء المجدول في خيط منفصل
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        # بدء البوت في خيط منفصل
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()

        # بدء المحلل في خيط منفصل
        self.analyzer_thread = threading.Thread(target=self.run_analyzer, daemon=True)
        self.analyzer_thread.start()

        # بدء البث في خيط منفصل
        self.broadcaster_thread = threading.Thread(target=self.run_broadcaster, daemon=True)
        self.broadcaster_thread.start()

        print("✅ تم تشغيل النظام الموحد وجميع الأنظمة الفرعية!")
        print("\n📅 جدولة التقارير:")
        print("  • التقرير اليومي: كل يوم الساعة 23:00")
        print("  • التقرير الأسبوعي: كل يوم أحد الساعة 22:00")
        print("  • التقرير الشهري: أول يوم من كل شهر الساعة 00:00")
        print("\n⌨️  الأوامر المتاحة:")
        print("  • 'report daily' - توليد التقرير اليومي")
        print("  • 'report weekly' - توليد التقرير الأسبوعي")
        print("  • 'report monthly' - توليد التقرير الشهري")
        print("  • 'report all' - توليد جميع التقارير")
        print("  • 'stats' - عرض الإحصائيات الحالية")
        print("  • 'trades' - عرض الصفقات المفتوحة")
        print("  • 'add' - إضافة صفقة جديدة")
        print("  • 'close' - إغلاق صفقة")
        print("  • 'export' - تصدير البيانات")
        print("  • 'quit' - إيقاف النظام")
        print("=" * 60)
    
    def schedule_reports(self):
        """جدولة التقارير الدورية"""
        # تقرير يومي الساعة 11 مساءً
        schedule.every().day.at("23:00").do(self.generate_daily_report)
        
        # تقرير أسبوعي كل يوم أحد الساعة 10 مساءً
        schedule.every().sunday.at("22:00").do(self.generate_weekly_report)
        
        # تقرير شهري أول كل شهر (سيتم التحقق يومياً)
        schedule.every().day.at("00:00").do(self.check_monthly_report)
    
    def _run_scheduler(self):
        """تشغيل المجدول في الخلفية"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # فحص كل دقيقة
    
    def generate_daily_report(self):
        """توليد التقرير اليومي"""
        print("\n📊 جاري توليد التقرير اليومي...")
        filename = self.reports.generate_daily_report()
        print(f"✅ تم حفظ التقرير: {filename}")
        return filename
    
    def generate_weekly_report(self):
        """توليد التقرير الأسبوعي"""
        print("\n📊 جاري توليد التقرير الأسبوعي...")
        filename = self.reports.generate_weekly_report()
        print(f"✅ تم حفظ التقرير: {filename}")
        return filename
    
    def generate_monthly_report(self):
        """توليد التقرير الشهري"""
        print("\n📊 جاري توليد التقرير الشهري...")
        filename = self.reports.generate_monthly_report()
        print(f"✅ تم حفظ التقرير: {filename}")
        return filename
    
    def check_monthly_report(self):
        """التحقق من الحاجة لتوليد تقرير شهري"""
        today = datetime.now()
        if today.day == 1:  # أول يوم من الشهر
            self.generate_monthly_report()
    
    def show_statistics(self, days=30):
        """عرض الإحصائيات"""
        stats = self.stats.get_statistics(days=days)
        
        print(f"\n{'='*60}")
        print(f"📊 إحصائيات آخر {days} يوم")
        print(f"{'='*60}")
        print(f"✅ إجمالي الصفقات: {stats['total_trades']}")
        print(f"🎯 الصفقات الرابحة: {stats['winning_trades']} ({stats['win_rate']:.2f}%)")
        print(f"❌ الصفقات الخاسرة: {stats['losing_trades']}")
        print(f"⚖️  صفقات التعادل: {stats['break_even_trades']}")
        print(f"\n💰 الربح الإجمالي: ${stats['total_profit']:.2f}")
        print(f"💸 الخسارة الإجمالية: ${stats['total_loss']:.2f}")
        print(f"📊 صافي الربح: ${stats['net_profit']:.2f}")
        print(f"\n⚖️  عامل الربح: {stats['profit_factor']:.2f}")
        print(f"💹 متوسط الربح: ${stats['avg_win']:.2f}")
        print(f"📉 متوسط الخسارة: ${stats['avg_loss']:.2f}")
        print(f"🌟 أفضل صفقة: ${stats['best_trade']:.2f}")
        print(f"⚠️  أسوأ صفقة: ${stats['worst_trade']:.2f}")
        
        if stats['by_symbol']:
            print(f"\n{'='*60}")
            print("📊 الأداء حسب العملة:")
            print(f"{'='*60}")
            for item in stats['by_symbol']:
                print(f"{item['symbol']}: {item['total_trades']} صفقة | "
                      f"نجاح {item['win_rate']:.1f}% | "
                      f"ربح ${item['net_profit']:.2f}")
        
        print(f"{'='*60}\n")
    
    def show_open_trades(self):
        """عرض الصفقات المفتوحة"""
        trades = self.stats.get_open_trades()
        
        print(f"\n{'='*60}")
        print("💼 الصفقات المفتوحة")
        print(f"{'='*60}")
        
        if not trades:
            print("✅ لا توجد صفقات مفتوحة حالياً")
        else:
            for trade in trades:
                direction_emoji = "📈" if trade['direction'].lower() == 'buy' else "📉"
                print(f"\n{direction_emoji} الصفقة #{trade['id']} - {trade['symbol']} {trade['direction'].upper()}")
                print(f"  💵 الدخول: {trade['entry_price']:.5f}")
                print(f"  🛑 وقف الخسارة: {trade['stop_loss']:.5f}")
                print(f"  🎯 TP1: {trade['take_profit_1']:.5f} | TP2: {trade['take_profit_2']:.5f} | TP3: {trade['take_profit_3']:.5f}")
                print(f"  ⏰ الوقت: {trade['entry_time']}")
                print(f"  📊 {trade['strategy']} | {trade['timeframe']}")
        
        print(f"{'='*60}\n")
    
    def add_trade_interactive(self):
        """إضافة صفقة بشكل تفاعلي"""
        print("\n📝 إضافة صفقة جديدة")
        print("="*60)
        
        try:
            symbol = input("العملة (مثال: XAUUSD): ").strip().upper()
            direction = input("الاتجاه (buy/sell): ").strip().lower()
            entry_price = float(input("سعر الدخول: "))
            stop_loss = float(input("وقف الخسارة: "))
            tp1 = float(input("الهدف الأول TP1: "))
            tp2 = float(input("الهدف الثاني TP2: "))
            tp3 = float(input("الهدف الثالث TP3: "))
            volume = float(input("حجم الصفقة (lot): ") or "1.0")
            strategy = input("الاستراتيجية (مثال: ICT): ").strip() or "ICT"
            timeframe = input("الإطار الزمني (مثال: 1H): ").strip() or "1H"
            notes = input("ملاحظات (اختياري): ").strip()
            
            # حساب نسبة المخاطرة للعائد
            risk = abs(entry_price - stop_loss)
            reward = abs(tp3 - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            trade_data = {
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit_1': tp1,
                'take_profit_2': tp2,
                'take_profit_3': tp3,
                'volume': volume,
                'strategy': strategy,
                'timeframe': timeframe,
                'risk_reward_ratio': rr_ratio,
                'notes': notes
            }
            
            trade_id = self.stats.add_trade(trade_data)
            
            print(f"\n✅ تم إضافة الصفقة #{trade_id} بنجاح!")
            print(f"📊 نسبة المخاطرة للعائد: 1:{rr_ratio:.2f}")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ خطأ في إضافة الصفقة: {e}")
    
    def close_trade_interactive(self):
        """إغلاق صفقة بشكل تفاعلي"""
        self.show_open_trades()
        
        try:
            trade_id = int(input("\nرقم الصفقة المراد إغلاقها: "))
            exit_price = float(input("سعر الخروج: "))
            notes = input("ملاحظات (اختياري): ").strip()
            
            result = self.stats.close_trade(trade_id, exit_price, notes)
            
            if result['success']:
                status_emoji = "✅" if result['status'] == 'win' else "❌" if result['status'] == 'loss' else "⚖️"
                print(f"\n{status_emoji} تم إغلاق الصفقة #{trade_id}")
                print(f"💰 النتيجة: ${result['profit_loss']:.2f} ({result['profit_percentage']:.2f}%)")
                print(f"📊 الحالة: {result['status'].upper()}")
                print("="*60)
            else:
                print(f"\n❌ خطأ: {result['error']}")
                
        except Exception as e:
            print(f"\n❌ خطأ في إغلاق الصفقة: {e}")
    
    def export_data(self):
        """تصدير البيانات"""
        print("\n📤 جاري تصدير البيانات...")
        filename = self.stats.export_to_json()
        print(f"✅ تم التصدير: {filename}")
    
    def stop(self):
        """إيقاف النظام"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        print("\n👋 تم إيقاف النظام. وداعاً!")

def main():
    """الدالة الرئيسية"""
    system = UnifiedTradingSystem()
    system.start()
    
    # حلقة الأوامر التفاعلية
    while system.is_running:
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                system.stop()
                break
            
            elif command == 'report daily':
                system.generate_daily_report()
            
            elif command == 'report weekly':
                system.generate_weekly_report()
            
            elif command == 'report monthly':
                system.generate_monthly_report()
            
            elif command == 'report all':
                print("\n📊 جاري توليد جميع التقارير...")
                reports = system.reports.generate_all_reports()
                print(f"✅ التقرير اليومي: {reports['daily']}")
                print(f"✅ التقرير الأسبوعي: {reports['weekly']}")
                print(f"✅ التقرير الشهري: {reports['monthly']}")
            
            elif command == 'stats':
                days = input("عدد الأيام (افتراضي 30): ").strip()
                days = int(days) if days else 30
                system.show_statistics(days)
            
            elif command == 'trades':
                system.show_open_trades()
            
            elif command == 'add':
                system.add_trade_interactive()
            
            elif command == 'close':
                system.close_trade_interactive()
            
            elif command == 'export':
                system.export_data()
            
            elif command == 'help':
                print("\n⌨️  الأوامر المتاحة:")
                print("  • 'report daily' - توليد التقرير اليومي")
                print("  • 'report weekly' - توليد التقرير الأسبوعي")
                print("  • 'report monthly' - توليد التقرير الشهري")
                print("  • 'report all' - توليد جميع التقارير")
                print("  • 'stats' - عرض الإحصائيات")
                print("  • 'trades' - عرض الصفقات المفتوحة")
                print("  • 'add' - إضافة صفقة جديدة")
                print("  • 'close' - إغلاق صفقة")
                print("  • 'export' - تصدير البيانات")
                print("  • 'quit' - إيقاف النظام")
            
            elif command:
                print("❌ أمر غير معروف. اكتب 'help' للمساعدة.")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  تم إيقاف النظام بواسطة المستخدم")
            system.stop()
            break
        except Exception as e:
            print(f"\n❌ خطأ: {e}")

if __name__ == "__main__":
    main()

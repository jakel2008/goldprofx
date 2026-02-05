# -*- coding: utf-8 -*-
"""
نظام التشغيل المركزي الشامل - MONEY MAKER VIP
يدير جميع مكونات النظام بشكل احترافي
"""

import os
import sys
import time
import threading
import schedule
import json
from datetime import datetime
import subprocess
import signal

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(__file__))

class MasterSystem:
    """نظام التشغيل المركزي"""
    
    def __init__(self):
        self.running = True
        self.processes = {}
        self.status = {
            'web_app': 'stopped',
            'vip_bot': 'stopped',
            'signal_broadcaster': 'stopped',
            'auto_analyzer': 'stopped',
            'scheduler': 'stopped'
        }
        self.config = self.load_config()
        
    def load_config(self):
        """تحميل الإعدادات"""
        config_file = 'master_config.json'
        default_config = {
            'pairs': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'XAU/USD', 'BTC/USD'],
            'intervals': ['1h', '4h'],
            'analysis_schedule': '*/30 * * * *',  # كل 30 دقيقة
            'broadcast_schedule': '*/15 * * * *',  # كل 15 دقيقة
            'report_schedule': '0 0 * * *',  # يومياً عند منتصف الليل
            'auto_start': {
                'web_app': True,
                'vip_bot': True,
                'signal_broadcaster': True,
                'auto_analyzer': True
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except:
                pass
        else:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
        
        return default_config
    
    def log(self, message, level='INFO'):
        """تسجيل الرسائل"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # حفظ في ملف
        with open('master_system.log', 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def start_web_app(self):
        """تشغيل تطبيق الويب"""
        try:
            self.log("🌐 بدء تشغيل تطبيق الويب...")
            # تشغيل في خيط منفصل
            from web_app import app
            thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
            thread.daemon = True
            thread.start()
            self.status['web_app'] = 'running'
            self.log("✅ تطبيق الويب يعمل على المنفذ 5000", 'SUCCESS')
        except Exception as e:
            self.log(f"❌ خطأ في تشغيل تطبيق الويب: {e}", 'ERROR')
            self.status['web_app'] = 'error'
    
    def start_vip_bot(self):
        """تشغيل بوت VIP"""
        try:
            self.log("🤖 بدء تشغيل بوت VIP...")
            import vip_bot_simple
            # البوت سيعمل في نفس العملية
            # يمكن تشغيله في thread منفصل إذا لزم الأمر
            self.status['vip_bot'] = 'running'
            self.log("✅ بوت VIP جاهز", 'SUCCESS')
        except Exception as e:
            self.log(f"⚠️ تحذير في بوت VIP: {e}", 'WARNING')
            self.status['vip_bot'] = 'warning'
    
    def run_analysis(self):
        """تشغيل التحليل التلقائي"""
        try:
            self.log("📊 بدء التحليل التلقائي...")
            from auto_pairs_analyzer import run_daily_analysis
            
            # تشغيل التحليل
            run_daily_analysis()
            
            self.log("✅ انتهى التحليل التلقائي", 'SUCCESS')
        except Exception as e:
            self.log(f"⚠️ تحذير في التحليل: {e}", 'WARNING')
    
    def broadcast_signals(self):
        """بث الإشارات"""
        try:
            self.log("📡 بدء بث الإشارات...")
            from signal_broadcaster import broadcast_latest_signals
            broadcast_latest_signals()
            self.log("✅ تم بث الإشارات", 'SUCCESS')
        except Exception as e:
            self.log(f"❌ خطأ في بث الإشارات: {e}", 'ERROR')
    
    def generate_daily_report(self):
        """إنشاء التقرير اليومي"""
        try:
            self.log("📈 إنشاء التقرير اليومي...")
            from periodic_reports import generate_daily_report
            generate_daily_report()
            self.log("✅ تم إنشاء التقرير اليومي", 'SUCCESS')
        except Exception as e:
            self.log(f"❌ خطأ في إنشاء التقرير: {e}", 'ERROR')
    
    def update_active_trades(self):
        """تحديث الصفقات النشطة"""
        try:
            # قراءة الصفقات النشطة
            if os.path.exists('active_trades.json'):
                with open('active_trades.json', 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                
                updated_trades = []
                for trade in trades:
                    # تحديث حالة الصفقة
                    # يمكن إضافة منطق للتحقق من الأسعار الحالية
                    updated_trades.append(trade)
                
                with open('active_trades.json', 'w', encoding='utf-8') as f:
                    json.dump(updated_trades, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"⚠️ خطأ في تحديث الصفقات: {e}", 'WARNING')
    
    def setup_scheduler(self):
        """إعداد الجدولة التلقائية"""
        self.log("⏰ إعداد الجدولة التلقائية...")
        
        # تحليل تلقائي كل 30 دقيقة
        schedule.every(30).minutes.do(self.run_analysis)
        
        # بث الإشارات كل 15 دقيقة
        schedule.every(15).minutes.do(self.broadcast_signals)
        
        # تحديث الصفقات كل 5 دقائق
        schedule.every(5).minutes.do(self.update_active_trades)
        
        # تقرير يومي في الساعة 23:00
        schedule.every().day.at("23:00").do(self.generate_daily_report)
        
        self.status['scheduler'] = 'running'
        self.log("✅ تم إعداد الجدولة التلقائية", 'SUCCESS')
    
    def run_scheduler(self):
        """تشغيل نظام الجدولة"""
        self.log("🔄 بدء نظام الجدولة...")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(10)  # فحص كل 10 ثوانٍ
            except Exception as e:
                self.log(f"⚠️ خطأ في الجدولة: {e}", 'WARNING')
                time.sleep(60)
    
    def get_system_status(self):
        """الحصول على حالة النظام"""
        return {
            'timestamp': datetime.now().isoformat(),
            'status': self.status,
            'config': self.config
        }
    
    def save_status(self):
        """حفظ حالة النظام"""
        try:
            with open('system_status.json', 'w', encoding='utf-8') as f:
                json.dump(self.get_system_status(), f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"⚠️ خطأ في حفظ الحالة: {e}", 'WARNING')
    
    def start_all(self):
        """تشغيل جميع المكونات"""
        self.log("=" * 60)
        self.log("🚀 MONEY MAKER VIP - نظام التشغيل المركزي")
        self.log("=" * 60)
        
        # تشغيل المكونات
        if self.config['auto_start'].get('web_app', True):
            self.start_web_app()
            time.sleep(2)
        
        if self.config['auto_start'].get('vip_bot', True):
            self.start_vip_bot()
            time.sleep(2)
        
        # إعداد الجدولة
        self.setup_scheduler()
        
        # تشغيل التحليل الأولي
        self.log("📊 تشغيل التحليل الأولي...")
        self.run_analysis()
        
        # بدء نظام الجدولة
        scheduler_thread = threading.Thread(target=self.run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        self.log("=" * 60)
        self.log("✅ جميع الأنظمة تعمل بنجاح!")
        self.log("=" * 60)
        
        # حفظ الحالة
        self.save_status()
        
        # إبقاء البرنامج يعمل
        try:
            while self.running:
                time.sleep(30)  # حفظ الحالة كل 30 ثانية
                self.save_status()
        except KeyboardInterrupt:
            self.log("\n⚠️ تم إيقاف النظام من قبل المستخدم", 'WARNING')
            self.running = False
    
    def stop_all(self):
        """إيقاف جميع المكونات"""
        self.log("⏹️ إيقاف جميع المكونات...")
        self.running = False
        self.save_status()
        self.log("✅ تم إيقاف النظام بنجاح")

def main():
    """الدالة الرئيسية"""
    system = MasterSystem()
    
    # معالجة إشارة الإيقاف
    def signal_handler(sig, frame):
        system.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # تشغيل النظام
    system.start_all()

if __name__ == "__main__":
    main()

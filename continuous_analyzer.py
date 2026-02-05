"""
نظام التحليل المستمر وعرض الإشارات
Continuous Analysis and Signal Display System
"""

import os
import time
import sqlite3
import subprocess
from datetime import datetime

def clear_screen():
    """مسح الشاشة"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_signals():
    """عرض آخر الإشارات"""
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # جلب الإشارات اليوم
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT symbol, signal_type, entry_price, stop_loss, 
                   take_profit_1, take_profit_2, take_profit_3,
                   quality_score, status, result, created_at
            FROM signals 
            WHERE DATE(created_at) = ?
            ORDER BY created_at DESC 
            LIMIT 20
        ''', (today,))
        
        signals = c.fetchall()
        conn.close()
        
        clear_screen()
        print("=" * 80)
        print("📊 نظام الإشارات المباشرة - GOLD PRO VIP SYSTEM")
        print("=" * 80)
        print(f"⏰ التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 عدد الإشارات اليوم: {len(signals)}")
        print("=" * 80)
        
        if not signals:
            print("\n⚠️ لا توجد إشارات لهذا اليوم")
            print("💡 سيتم التحليل التلقائي بعد قليل...")
        else:
            for i, sig in enumerate(signals, 1):
                # تحديد اللون حسب النوع
                direction = "🔺 شراء BUY" if sig['signal_type'] == 'buy' else "🔻 بيع SELL"
                
                # تحديد الحالة
                status_emoji = {
                    'pending': '⏳ معلقة',
                    'active': '⚡ نشطة',
                    'closed': '☑️ مغلقة'
                }.get(sig['status'], '❓ غير معروف')
                
                # تحديد النتيجة
                result_text = ""
                if sig['result'] == 'win':
                    result_text = "🏆 رابحة"
                elif sig['result'] == 'loss':
                    result_text = "❌ خاسرة"
                
                print(f"\n{'='*80}")
                print(f"#{i} | {sig['symbol']} | {direction} | جودة: ⭐ {sig['quality_score']}")
                print(f"{'='*80}")
                print(f"💰 سعر الدخول: {sig['entry_price']:.5f}")
                print(f"🛑 وقف الخسارة: {sig['stop_loss']:.5f}")
                print(f"🎯 الأهداف: TP1={sig['take_profit_1']:.5f} | TP2={sig['take_profit_2']:.5f} | TP3={sig['take_profit_3']:.5f}")
                print(f"📊 الحالة: {status_emoji} {result_text}")
                print(f"🕐 الوقت: {sig['created_at']}")
        
        print("\n" + "=" * 80)
        print("🔄 التحديث التلقائي كل 60 ثانية...")
        print("❌ اضغط Ctrl+C للإيقاف")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ خطأ في عرض الإشارات: {e}")

def main():
    """البرنامج الرئيسي"""
    print("🚀 بدء نظام التحليل المستمر...")
    print("=" * 80)
    
    interval = 60  # التحديث كل دقيقة
    
    try:
        while True:
            try:
                # عرض الإشارات الحالية
                display_signals()
                
                # انتظار 60 ثانية
                time.sleep(interval)
                
                # إجراء تحليل جديد
                print("\n🔄 جاري التحليل...")
                subprocess.run(['python', 'auto_pairs_analyzer.py'], check=False)
                
            except KeyboardInterrupt:
                print("\n\n⛔ تم إيقاف النظام بواسطة المستخدم")
                break
            except Exception as e:
                print(f"\n❌ خطأ: {e}")
                print("⏳ إعادة المحاولة بعد 10 ثواني...")
                time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n\n👋 إيقاف النظام...")
    
    print("✅ تم إيقاف نظام التحليل المستمر")

if __name__ == '__main__':
    os.system('chcp 65001 > nul')  # دعم العربية في Windows
    main()

# -*- coding: utf-8 -*-
"""
لوحة تحكم تفاعلية متقدمة مع عرض الصفقات المنتهية والتحديث التلقائي
"""
import sqlite3
import yfinance as yf
from datetime import datetime
import os
import sys
import time
import threading
from msvcrt import kbhit, getch
import time
import threading

YF_SYMBOLS = {
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'XAUUSD': 'GC=F',
    'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD'
}

def clear_screen():
    """مسح الشاشة"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_current_price(symbol):
    """جلب السعر الحالي"""
    try:
        yf_symbol = YF_SYMBOLS.get(symbol)
        if not yf_symbol:
            return None
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(period='1d', interval='5m')
        if data.empty:
            return None
        return float(data['Close'].iloc[-1])
    except:
        return None

def calculate_pips(symbol, entry, current, signal_type):
    """حساب النقاط"""
    if symbol in ['EURUSD', 'GBPUSD', 'AUDUSD', 'USDJPY']:
        multiplier = 10000 if symbol != 'USDJPY' else 100
    else:
        multiplier = 1
    
    if signal_type == 'buy':
        return (current - entry) * multiplier
    else:
        return (entry - current) * multiplier

def show_dashboard(show_all_closed=False):
    """عرض لوحة التحكم التفاعلية"""
    clear_screen()
    
    print("╔" + "═" * 88 + "╗")
    print("║" + " 📊 لوحة تحكم الصفقات المباشرة ".center(88) + "║")
    print("╚" + "═" * 88 + "╝")
    
    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    
    # جلب جميع الإشارات
    c.execute('''
        SELECT id, symbol, signal_type, entry_price, stop_loss, 
               take_profit_1, take_profit_2, take_profit_3,
               quality_score, status, result, created_at, close_price
        FROM signals
        ORDER BY 
            CASE status 
                WHEN 'active' THEN 1 
                WHEN 'partial_win' THEN 2 
                ELSE 3 
            END,
            created_at DESC
    ''')
    
    signals = c.fetchall()
    
    active_signals = []
    closed_signals = []
    
    print(f"\n⏰ الوقت الحالي: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # معالجة الإشارات
    for sig in signals:
        id, symbol, sig_type, entry, sl, tp1, tp2, tp3, quality, status, result, created, close_price = sig
        
        if status in ['active', 'partial_win']:
            current_price = get_current_price(symbol)
            if current_price:
                pips = calculate_pips(symbol, entry, current_price, sig_type)
                distance_to_tp1 = abs(tp1 - current_price) if tp1 else 999999
                distance_to_sl = abs(sl - current_price)
                progress = (distance_to_sl / (distance_to_sl + distance_to_tp1) * 100) if (distance_to_sl + distance_to_tp1) > 0 else 0
                
                active_signals.append({
                    'symbol': symbol, 'type': sig_type, 'entry': entry,
                    'current': current_price, 'sl': sl, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                    'pips': pips, 'quality': quality, 'progress': progress, 'created': created
                })
        else:
            if close_price:
                pips = calculate_pips(symbol, entry, close_price, sig_type)
                closed_signals.append({
                    'symbol': symbol, 'type': sig_type, 'entry': entry,
                    'current': close_price, 'sl': sl, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                    'pips': pips, 'quality': quality, 'result': result, 'created': created
                })
    
    # عرض الصفقات النشطة
    print("┌" + "─" * 88 + "┐")
    print("│" + " ⏳ الصفقات النشطة ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    
    if active_signals:
        for sig in active_signals:
            direction = '🟢 شراء' if sig['type'] == 'buy' else '🔴 بيع'
            pips_display = f"✅ +{sig['pips']:.1f}" if sig['pips'] > 0 else f"❌ {sig['pips']:.1f}" if sig['pips'] < 0 else f"⚪ {sig['pips']:.1f}"
            progress_bar_length = 20
            filled = int(sig['progress'] / 100 * progress_bar_length)
            bar = "█" * filled + "░" * (progress_bar_length - filled)
            
            print(f"│ {direction} {sig['symbol']:10} │ الدخول: {sig['entry']:>10.5f} │ الحالي: {sig['current']:>10.5f} │")
            print(f"│   النقاط: {pips_display:15} │ التقدم: [{bar}] {sig['progress']:.0f}%    │")
            print(f"│   SL: {sig['sl']:>10.5f} │ TP1: {sig['tp1']:>10.5f} │ الجودة: {sig['quality']}/100 │")
            print("├" + "─" * 88 + "┤")
    else:
        print("│" + " لا توجد صفقات نشطة ".center(88) + "│")
        print("├" + "─" * 88 + "┤")
    
    print("└" + "─" * 88 + "┘")
    
    # عرض الصفقات المنتهية
    print("\n┌" + "─" * 88 + "┐")
    print("│" + " ✅ الصفقات المنتهية ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    
    if closed_signals:
        wins = [s for s in closed_signals if s['result'] == 'win']
        losses = [s for s in closed_signals if s['result'] == 'loss']
        total_closed = len(closed_signals)
        win_rate = (len(wins) / total_closed * 100) if total_closed > 0 else 0
        
        # ملخص الإحصائيات
        print(f"│  💰 رابحة: {len(wins):2}  │  💸 خاسرة: {len(losses):2}  │  📊 نسبة النجاح: {win_rate:5.1f}%  │  📈 الإجمالي: {total_closed:2}  │")
        print("├" + "─" * 88 + "┤")
        
        # عدد الصفقات للعرض
        display_count = len(closed_signals) if show_all_closed else min(10, len(closed_signals))
        
        # عرض الصفقات الرابحة
        if wins:
            wins_to_show = wins if show_all_closed else wins[:5]
            if wins_to_show:
                print("│" + f" ✅ صفقات رابحة ({len(wins)}): ".ljust(88) + "│")
                for sig in wins_to_show:
                    direction = '🟢' if sig['type'] == 'buy' else '🔴'
                    # تحديد الهدف
                    if abs(sig['current'] - sig['tp3']) < 0.1:
                        target = "TP3 🎯🎯🎯"
                    elif abs(sig['current'] - sig['tp2']) < 0.1:
                        target = "TP2 🎯🎯"
                    else:
                        target = "TP1 🎯"
                    
                    print(f"│  {direction} {sig['symbol']:10} │ +{sig['pips']:>7.1f} نقطة │ {target:12} │ الجودة: {sig['quality']}/100 │ {sig['created'][:10]} │")
                
                if not show_all_closed and len(wins) > 5:
                    print(f"│  ... وهناك {len(wins) - 5} صفقة رابحة أخرى ".ljust(88) + "│")
                print("├" + "─" * 88 + "┤")
        
        # عرض الصفقات الخاسرة
        if losses:
            losses_to_show = losses if show_all_closed else losses[:5]
            if losses_to_show:
                print("│" + f" ❌ صفقات خاسرة ({len(losses)}): ".ljust(88) + "│")
                for sig in losses_to_show:
                    direction = '🟢' if sig['type'] == 'buy' else '🔴'
                    print(f"│  {direction} {sig['symbol']:10} │ {sig['pips']:>7.1f} نقطة │ ضرب SL      │ الجودة: {sig['quality']}/100 │ {sig['created'][:10]} │")
                
                if not show_all_closed and len(losses) > 5:
                    print(f"│  ... وهناك {len(losses) - 5} صفقة خاسرة أخرى ".ljust(88) + "│")
                print("├" + "─" * 88 + "┤")
        
        # رابط لعرض الكل/تصغير
        if total_closed > 10:
            if show_all_closed:
                print("│" + " 📉 لإخفاء الصفقات: اضغط Enter ".center(88) + "│")
            else:
                print("│" + f" 📋 لعرض الكل ({total_closed} صفقة): اكتب 'all' واضغط Enter ".center(88) + "│")
            print("├" + "─" * 88 + "┤")
    else:
        print("│" + " لا توجد صفقات منتهية بعد ".center(88) + "│")
        print("├" + "─" * 88 + "┤")
    
    print("└" + "─" * 88 + "┘")
    
    # الإحصائيات العامة
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'active'")
    active_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND result = 'win'")
    wins_total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND result = 'loss'")
    losses_total = c.fetchone()[0]
    
    total = wins_total + losses_total
    overall_win_rate = (wins_total / total * 100) if total > 0 else 0
    
    print("\n┌" + "─" * 88 + "┐")
    print("│" + " 📊 الإحصائيات الإجمالية ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    print(f"│  ⏳ صفقات نشطة: {active_count:3}  │  ✅ رابحة: {wins_total:3}  │  ❌ خاسرة: {losses_total:3}  │  📈 نسبة النجاح: {overall_win_rate:5.1f}%  │")
    print("└" + "─" * 88 + "┘")
    
    conn.close()
    
    print("\n💡 الأوامر: Enter=تحديث الآن | all=عرض كل المنتهية | auto=تحديث تلقائي | q=خروج")

def auto_refresh_dashboard(interval=30, show_all=False):
    """تحديث تلقائي للوحة التحكم"""
    print(f"\n🔄 وضع التحديث التلقائي نشط (كل {interval} ثانية)")
    print("⚠️  للإيقاف: اضغط Ctrl+C\n")
    
    try:
        while True:
            show_dashboard(show_all_closed=show_all)
            print(f"\n⏱️  التحديث التالي بعد {interval} ثانية... (Ctrl+C للإيقاف)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف التحديث التلقائي")
        return False
    
    return True

if __name__ == "__main__":
    show_all = False
    auto_mode = False
    
    # عرض القائمة الرئيسية
    while True:
        if not auto_mode:
            show_dashboard(show_all_closed=show_all)
        
        try:
            user_input = input("\n👉 اختيارك: ").strip().lower()
            
            if user_input == 'q' or user_input == 'خروج' or user_input == 'exit':
                print("\n👋 شكراً لاستخدامك لوحة التحكم!")
                break
            
            elif user_input == 'all' or user_input == 'الكل':
                show_all = not show_all
                continue
            
            elif user_input == 'auto' or user_input == 'تلقائي':
                # طلب المدة الزمنية
                print("\n⏱️  كم ثانية بين كل تحديث؟")
                interval_input = input("👉 المدة (الافتراضي 30 ثانية): ").strip()
                
                try:
                    interval = int(interval_input) if interval_input else 30
                    if interval < 5:
                        interval = 5
                        print("⚠️  الحد الأدنى 5 ثوانٍ")
                except:
                    interval = 30
                    print("⚠️  قيمة خاطئة، استخدام 30 ثانية")
                
                # بدء التحديث التلقائي
                auto_refresh_dashboard(interval, show_all)
                # بعد الإيقاف، العودة للوضع اليدوي
                auto_mode = False
                continue
            
            else:
                # تحديث عادي (Enter)
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 تم الإغلاق!")
            break
        except EOFError:
            print("\n\n👋 تم الإغلاق!")
            break

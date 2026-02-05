# -*- coding: utf-8 -*-
"""
لوحة تحكم متقدمة لتتبع الصفقات
"""
import sqlite3
import yfinance as yf
from datetime import datetime
import os

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

def show_dashboard():
    """عرض لوحة التحكم"""
    clear_screen()
    
    print("╔" + "═" * 88 + "╗")
    print("║" + " " * 25 + "📊 لوحة تحكم الصفقات المباشرة" + " " * 32 + "║")
    print("╚" + "═" * 88 + "╝")
    
    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    
    # جلب جميع الإشارات
    c.execute('''
        SELECT id, symbol, signal_type, entry_price, stop_loss, 
               take_profit_1, take_profit_2, take_profit_3,
               quality_score, status, result, created_at
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
        id, symbol, sig_type, entry, sl, tp1, tp2, tp3, quality, status, result, created = sig
        
        current_price = get_current_price(symbol)
        
        if current_price:
            pips = calculate_pips(symbol, entry, current_price, sig_type)
            
            # تحديد حالة الصفقة
            distance_to_tp1 = abs(tp1 - current_price) if tp1 else 999999
            distance_to_sl = abs(sl - current_price)
            progress = (distance_to_sl / (distance_to_sl + distance_to_tp1) * 100) if (distance_to_sl + distance_to_tp1) > 0 else 0
            
            signal_data = {
                'id': id,
                'symbol': symbol,
                'type': sig_type,
                'entry': entry,
                'current': current_price,
                'sl': sl,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'pips': pips,
                'quality': quality,
                'status': status,
                'result': result,
                'progress': progress,
                'created': created
            }
            
            if status in ['active', 'partial_win']:
                active_signals.append(signal_data)
            else:
                closed_signals.append(signal_data)
    
    # عرض الصفقات النشطة
    print("┌" + "─" * 88 + "┐")
    print("│" + " ⏳ الصفقات النشطة ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    
    if active_signals:
        for sig in active_signals:
            direction = '🟢 شراء' if sig['type'] == 'buy' else '🔴 بيع'
            
            # تحديد اللون حسب الربح/الخسارة
            if sig['pips'] > 0:
                pips_display = f"✅ +{sig['pips']:.1f}"
            elif sig['pips'] < 0:
                pips_display = f"❌ {sig['pips']:.1f}"
            else:
                pips_display = f"⚪ {sig['pips']:.1f}"
            
            # شريط التقدم
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
    
    # عرض الصفقات المنتهية بشكل تفاعلي
    print("\n┌" + "─" * 88 + "┐")
    print("│" + " ✅ الصفقات المنتهية ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    
    if closed_signals:
        # تصنيف حسب النتيجة
        wins = [s for s in closed_signals if s['result'] == 'win']
        losses = [s for s in closed_signals if s['result'] == 'loss']
        
        # عرض الإحصائيات
        print(f"│  💰 رابحة: {len(wins):2}  │  💸 خاسرة: {len(losses):2}  │  📊 النسبة: {(len(wins)/len(closed_signals)*100):.0f}%  │")
        print("├" + "─" * 88 + "┤")
        
        # عرض الصفقات الرابحة
        if wins:
            print("│" + " ✅ الصفقات الرابحة: ".ljust(88) + "│")
            for sig in wins[:5]:  # آخر 5 صفقات رابحة
                direction = '🟢 شراء' if sig['type'] == 'buy' else '🔴 بيع'
                
                # تحديد أي هدف تم الوصول إليه
                if sig['current'] == sig['tp3']:
                    target = "TP3 🎯🎯🎯"
                elif sig['current'] == sig['tp2']:
                    target = "TP2 🎯🎯"
                else:
                    target = "TP1 🎯"
                
                print(f"│  {direction} {sig['symbol']:10} │ ربح: +{sig['pips']:>6.1f} نقطة │ {target:15} │ {sig['created'][:10]} │")
            print("├" + "─" * 88 + "┤")
        
        # عرض الصفقات الخاسرة
        if losses:
            print("│" + " ❌ الصفقات الخاسرة: ".ljust(88) + "│")
            for sig in losses[:5]:  # آخر 5 صفقات خاسرة
                direction = '🟢 شراء' if sig['type'] == 'buy' else '🔴 بيع'
                
                print(f"│  {direction} {sig['symbol']:10} │ خسارة: {sig['pips']:>6.1f} نقطة │ ضرب SL        │ {sig['created'][:10]} │")
            print("├" + "─" * 88 + "┤")
        
        # رابط لعرض الكل
        if len(closed_signals) > 10:
            print("│" + f" 📋 عرض الكل: python show_closed_signals.py ({len(closed_signals)} صفقة) ".center(88) + "│")
            print("├" + "─" * 88 + "┤")
    else:
        print("│" + " لا توجد صفقات منتهية بعد ".center(88) + "│")
        print("├" + "─" * 88 + "┤")
    
    print("└" + "─" * 88 + "┘")
    
    # الإحصائيات
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'active'")
    active_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND result = 'win'")
    wins = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND result = 'loss'")
    losses = c.fetchone()[0]
    
    total_closed = wins + losses
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
    
    print("\n┌" + "─" * 88 + "┐")
    print("│" + " 📊 الإحصائيات ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    print(f"│  ⏳ صفقات نشطة: {active_count:3}  │  ✅ رابحة: {wins:3}  │  ❌ خاسرة: {losses:3}  │  📈 نسبة النجاح: {win_rate:5.1f}%  │")
    print("└" + "─" * 88 + "┘")
    
    conn.close()
    
    print("\n💡 نصيحة: استخدم هذا السكريبت بشكل دوري لتتبع الصفقات")
    print("🔄 للتحديث التلقائي: python track_signals_status.py")

if __name__ == "__main__":
    show_dashboard()

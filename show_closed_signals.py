# -*- coding: utf-8 -*-
"""
عرض الصفقات المنتهية بشكل تفصيلي
"""
import sqlite3
from datetime import datetime, timedelta

def show_closed_signals():
    """عرض جميع الصفقات المنتهية"""
    print("╔" + "═" * 88 + "╗")
    print("║" + " 📊 الصفقات المنتهية - تقرير شامل ".center(88) + "║")
    print("╚" + "═" * 88 + "╝")
    
    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    
    # جلب الصفقات المنتهية
    c.execute('''
        SELECT symbol, signal_type, entry_price, close_price, 
               stop_loss, take_profit_1, take_profit_2, take_profit_3,
               quality_score, result, created_at, close_time
        FROM signals
        WHERE status = 'closed'
        ORDER BY close_time DESC
    ''')
    
    closed_signals = c.fetchall()
    
    if not closed_signals:
        print("\n⚠️  لا توجد صفقات منتهية حتى الآن")
        conn.close()
        return
    
    print(f"\n📈 إجمالي الصفقات المنتهية: {len(closed_signals)}\n")
    
    # تصنيف حسب النتيجة
    wins = [s for s in closed_signals if s[9] == 'win']
    losses = [s for s in closed_signals if s[9] == 'loss']
    
    print("=" * 90)
    print(f"✅ صفقات رابحة: {len(wins)}")
    print(f"❌ صفقات خاسرة: {len(losses)}")
    print(f"📊 نسبة النجاح: {(len(wins) / len(closed_signals) * 100):.1f}%")
    print("=" * 90)
    
    # عرض الصفقات الرابحة
    if wins:
        print("\n┌" + "─" * 88 + "┐")
        print("│" + " ✅ الصفقات الرابحة ".center(88) + "│")
        print("├" + "─" * 88 + "┤")
        
        for sig in wins:
            symbol, sig_type, entry, close, sl, tp1, tp2, tp3, quality, result, created, close_time = sig
            
            direction = '🟢 شراء' if sig_type == 'buy' else '🔴 بيع'
            
            # حساب النقاط
            if symbol in ['EURUSD', 'GBPUSD', 'AUDUSD']:
                multiplier = 10000
            elif symbol == 'USDJPY':
                multiplier = 100
            else:
                multiplier = 1
            
            if sig_type == 'buy':
                pips = (close - entry) * multiplier
            else:
                pips = (entry - close) * multiplier
            
            # تحديد أي هدف تم الوصول إليه
            target_reached = "TP3 🎯🎯🎯" if close == tp3 else "TP2 🎯🎯" if close == tp2 else "TP1 🎯"
            
            print(f"│ {direction} {symbol:10} │ الدخول: {entry:>10.5f} │ الإغلاق: {close:>10.5f} │")
            print(f"│   الربح: +{pips:>6.1f} نقطة │ الهدف: {target_reached:15} │ الجودة: {quality}/100 │")
            print(f"│   📅 الدخول: {created[:16] if created else 'N/A':16} │ الإغلاق: {close_time[:16] if close_time else 'N/A':16} │")
            print("├" + "─" * 88 + "┤")
        
        print("└" + "─" * 88 + "┘")
    
    # عرض الصفقات الخاسرة
    if losses:
        print("\n┌" + "─" * 88 + "┐")
        print("│" + " ❌ الصفقات الخاسرة ".center(88) + "│")
        print("├" + "─" * 88 + "┤")
        
        for sig in losses:
            symbol, sig_type, entry, close, sl, tp1, tp2, tp3, quality, result, created, close_time = sig
            
            direction = '🟢 شراء' if sig_type == 'buy' else '🔴 بيع'
            
            # حساب النقاط
            if symbol in ['EURUSD', 'GBPUSD', 'AUDUSD']:
                multiplier = 10000
            elif symbol == 'USDJPY':
                multiplier = 100
            else:
                multiplier = 1
            
            if sig_type == 'buy':
                pips = (close - entry) * multiplier
            else:
                pips = (entry - close) * multiplier
            
            print(f"│ {direction} {symbol:10} │ الدخول: {entry:>10.5f} │ الإغلاق: {close:>10.5f} │")
            print(f"│   الخسارة: {pips:>6.1f} نقطة │ ضرب SL: {sl:>10.5f}      │ الجودة: {quality}/100 │")
            print(f"│   📅 الدخول: {created[:16] if created else 'N/A':16} │ الإغلاق: {close_time[:16] if close_time else 'N/A':16} │")
            print("├" + "─" * 88 + "┤")
        
        print("└" + "─" * 88 + "┘")
    
    # إحصائيات إضافية
    print("\n┌" + "─" * 88 + "┐")
    print("│" + " 📊 إحصائيات تفصيلية ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    
    # حساب إجمالي النقاط
    total_pips = 0
    for sig in closed_signals:
        symbol, sig_type, entry, close = sig[0], sig[1], sig[2], sig[3]
        
        if symbol in ['EURUSD', 'GBPUSD', 'AUDUSD']:
            multiplier = 10000
        elif symbol == 'USDJPY':
            multiplier = 100
        else:
            multiplier = 1
        
        if sig_type == 'buy':
            pips = (close - entry) * multiplier
        else:
            pips = (entry - close) * multiplier
        
        total_pips += pips
    
    avg_pips = total_pips / len(closed_signals) if closed_signals else 0
    
    print(f"│  📈 إجمالي النقاط: {total_pips:>8.1f}  │  📊 متوسط النقاط: {avg_pips:>8.1f}  │")
    print("└" + "─" * 88 + "┘")
    
    # تصنيف حسب الأزواج
    print("\n┌" + "─" * 88 + "┐")
    print("│" + " 📊 الأداء حسب الأزواج ".center(88) + "│")
    print("├" + "─" * 88 + "┤")
    
    symbols = {}
    for sig in closed_signals:
        symbol = sig[0]
        result = sig[9]
        
        if symbol not in symbols:
            symbols[symbol] = {'wins': 0, 'losses': 0}
        
        if result == 'win':
            symbols[symbol]['wins'] += 1
        else:
            symbols[symbol]['losses'] += 1
    
    for symbol, stats in sorted(symbols.items()):
        total = stats['wins'] + stats['losses']
        win_rate = (stats['wins'] / total * 100) if total > 0 else 0
        
        print(f"│  {symbol:10} │ ✅ {stats['wins']:2} │ ❌ {stats['losses']:2} │ 📈 {win_rate:5.1f}% │")
    
    print("└" + "─" * 88 + "┘")
    
    conn.close()

if __name__ == "__main__":
    show_closed_signals()

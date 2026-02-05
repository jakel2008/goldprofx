# -*- coding: utf-8 -*-
"""
عرض الإشارات النهائية بعد التنظيف
"""
import sqlite3
from signal_formatter import format_signal_message

print("📊 الإشارات النهائية في قاعدة البيانات\n")
print("=" * 70)

conn = sqlite3.connect('vip_signals.db')
c = conn.cursor()

c.execute('''
    SELECT symbol, signal_type, entry_price, stop_loss, 
           take_profit_1, take_profit_2, take_profit_3, 
           quality_score, timeframe, created_at 
    FROM signals 
    ORDER BY created_at DESC
''')

signals = c.fetchall()

print(f"\n✅ إجمالي الإشارات: {len(signals)}\n")

for i, (symbol, sig_type, entry, sl, tp1, tp2, tp3, quality, tf, time) in enumerate(signals, 1):
    print(f"\n{'='*70}")
    print(f"إشارة {i} - {symbol}")
    print(f"{'='*70}")
    
    # عرض بالتنسيق الجديد
    formatted = format_signal_message(
        symbol=symbol,
        signal_type=sig_type,
        entry=entry,
        stop_loss=sl,
        take_profits=[tp1, tp2, tp3],
        quality_score=quality
    )
    
    print(formatted)

conn.close()

print("\n" + "="*70)
print("\n🌐 لعرض الإشارات في المتصفح:")
print("   http://localhost:5000/signals")
print("\n📱 لإرسالها عبر التليجرام:")
print("   python signal_broadcaster.py")

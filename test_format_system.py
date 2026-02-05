# -*- coding: utf-8 -*-
"""
اختبار نظام البث بالتنسيق الجديد
"""
import json
import os
from datetime import datetime
import sqlite3

# إنشاء إشارة تجريبية في قاعدة البيانات
print("📊 إنشاء إشارة تجريبية بالتنسيق الجديد...")

conn = sqlite3.connect('vip_signals.db')
c = conn.cursor()

# إشارة XAUUSD (الذهب) - بيع
signal_data = {
    'signal_id': f"XAUUSD_SELL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    'symbol': 'XAUUSD',
    'signal_type': 'sell',
    'entry_price': 5079.20,
    'stop_loss': 5089.20,
    'take_profit_1': 5069.20,
    'take_profit_2': 5059.20,
    'take_profit_3': 5044.20,
    'quality_score': 92,
    'timeframe': '5m',
    'status': 'active',
    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

c.execute('''
    INSERT INTO signals 
    (signal_id, symbol, signal_type, entry_price, stop_loss, 
     take_profit_1, take_profit_2, take_profit_3, 
     quality_score, timeframe, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    signal_data['signal_id'],
    signal_data['symbol'],
    signal_data['signal_type'],
    signal_data['entry_price'],
    signal_data['stop_loss'],
    signal_data['take_profit_1'],
    signal_data['take_profit_2'],
    signal_data['take_profit_3'],
    signal_data['quality_score'],
    signal_data['timeframe'],
    signal_data['status'],
    signal_data['created_at']
))

conn.commit()
conn.close()

print("✅ تم إضافة الإشارة إلى قاعدة البيانات")

# عرض الإشارة
print("\n" + "=" * 60)
print("📋 تفاصيل الإشارة:")
print("=" * 60)
for key, value in signal_data.items():
    print(f"{key:20}: {value}")

print("\n📡 الآن يمكنك:")
print("1. فتح المتصفح: http://localhost:5000/signals")
print("2. تشغيل البث: python signal_broadcaster.py")
print("3. التحقق من التليجرام")

print("\n✨ التنسيق المتوقع:")
print("-" * 60)

from signal_formatter import format_signal_message

formatted = format_signal_message(
    symbol=signal_data['symbol'],
    signal_type=signal_data['signal_type'],
    entry=signal_data['entry_price'],
    stop_loss=signal_data['stop_loss'],
    take_profits=[
        signal_data['take_profit_1'],
        signal_data['take_profit_2'],
        signal_data['take_profit_3']
    ],
    quality_score=signal_data['quality_score']
)

print(formatted)

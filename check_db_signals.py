#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص الإشارات في قاعدة البيانات"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('vip_signals.db')
c = conn.cursor()

# إجمالي الإشارات
c.execute('SELECT COUNT(*) FROM signals')
total = c.fetchone()[0]
print(f"📊 إجمالي الإشارات في القاعدة: {total}")

# إشارات اليوم
c.execute("SELECT COUNT(*) FROM signals WHERE date(created_at) = date('now')")
today = c.fetchone()[0]
print(f"📅 إشارات اليوم (26 يناير 2026): {today}")

# آخر 10 إشارات
print("\n🕒 آخر 10 إشارات:")
c.execute('''
    SELECT symbol, signal_type, quality_score, created_at 
    FROM signals 
    ORDER BY created_at DESC 
    LIMIT 10
''')

for i, row in enumerate(c.fetchall(), 1):
    symbol, signal_type, quality, timestamp = row
    ts_short = timestamp[:19] if len(timestamp) > 19 else timestamp
    print(f"{i}. {symbol} - {signal_type.upper()} (جودة: {quality}) - {ts_short}")

# إشارات حسب النوع
print("\n📈 الإشارات حسب النوع:")
c.execute("SELECT signal_type, COUNT(*) FROM signals GROUP BY signal_type")
for signal_type, count in c.fetchall():
    print(f"  {signal_type.upper()}: {count}")

# متوسط الجودة
c.execute("SELECT AVG(quality_score) FROM signals")
avg_quality = c.fetchone()[0]
if avg_quality:
    print(f"\n⭐ متوسط جودة الإشارات: {avg_quality:.1f}/100")

conn.close()

print("\n" + "="*50)
print("✅ الفحص مكتمل")

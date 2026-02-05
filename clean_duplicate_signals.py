# -*- coding: utf-8 -*-
"""
فحص وتنظيف الإشارات المكررة
"""
import sqlite3
from datetime import datetime

print("🔍 فحص الإشارات المكررة...\n")

conn = sqlite3.connect('vip_signals.db')
c = conn.cursor()

# عرض الإشارات المكررة
c.execute('''
    SELECT symbol, signal_type, entry_price, COUNT(*) as count 
    FROM signals 
    GROUP BY symbol, signal_type, entry_price 
    HAVING COUNT(*) > 1
''')

duplicates = c.fetchall()
print(f"📊 عدد الإشارات المكررة: {len(duplicates)}\n")

for dup in duplicates:
    print(f"  {dup[0]} - {dup[1]} - السعر: {dup[2]} - مكرر {dup[3]} مرة")

# حذف الإشارات المكررة (الاحتفاظ بالأحدث فقط)
print("\n🧹 حذف النسخ المكررة...\n")

c.execute('''
    DELETE FROM signals 
    WHERE id NOT IN (
        SELECT MAX(id) 
        FROM signals 
        GROUP BY symbol, signal_type, entry_price, DATE(created_at)
    )
''')

deleted = c.rowcount
conn.commit()

print(f"✅ تم حذف {deleted} إشارة مكررة")

# عرض الإحصائيات بعد التنظيف
c.execute('SELECT COUNT(*) FROM signals')
total = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM signals WHERE DATE(created_at) = DATE('now')")
today = c.fetchone()[0]

print(f"\n📊 الإحصائيات بعد التنظيف:")
print(f"  📈 إجمالي الإشارات: {total}")
print(f"  📅 إشارات اليوم: {today}")

conn.close()
print("\n✅ اكتمل التنظيف بنجاح!")

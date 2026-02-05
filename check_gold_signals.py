# -*- coding: utf-8 -*-
"""
فحص وتنظيف الإشارات المكررة للذهب
"""
import sqlite3
from datetime import datetime

print("📊 فحص الإشارات في قاعدة البيانات...\n")

conn = sqlite3.connect('vip_signals.db')
c = conn.cursor()

# جلب جميع الإشارات
c.execute('''
    SELECT id, symbol, signal_type, entry_price, quality_score, created_at 
    FROM signals 
    ORDER BY created_at DESC
''')
signals = c.fetchall()

print(f"إجمالي الإشارات: {len(signals)}\n")
print("=" * 80)

# عرض جميع الإشارات
xauusd_count = 0
for i, (id, symbol, sig_type, entry, quality, time) in enumerate(signals, 1):
    print(f"{i}. ID:{id:3} | {symbol:10} | {sig_type:4} | السعر: {entry:>12.5f} | الجودة: {quality}/100 | {time}")
    if symbol == 'XAUUSD':
        xauusd_count += 1

print("=" * 80)
print(f"\n⚠️ عدد إشارات الذهب (XAUUSD): {xauusd_count}")

if xauusd_count > 1:
    print(f"\n🔍 وجدنا {xauusd_count} إشارة للذهب!")
    
    # عرض تفاصيل إشارات الذهب
    c.execute('''
        SELECT id, signal_type, entry_price, stop_loss, 
               take_profit_1, quality_score, created_at 
        FROM signals 
        WHERE symbol = 'XAUUSD'
        ORDER BY created_at DESC
    ''')
    gold_signals = c.fetchall()
    
    print("\n📋 تفاصيل إشارات الذهب:")
    print("-" * 80)
    for i, (id, sig, entry, sl, tp1, quality, time) in enumerate(gold_signals, 1):
        print(f"\nإشارة {i} (ID: {id}):")
        print(f"  النوع: {sig}")
        print(f"  الدخول: {entry:.5f}")
        print(f"  SL: {sl:.5f}")
        print(f"  TP1: {tp1:.5f}")
        print(f"  الجودة: {quality}/100")
        print(f"  الوقت: {time}")
    
    # سؤال المستخدم
    print("\n" + "=" * 80)
    print("❓ هل تريد حذف الإشارات المكررة للذهب؟")
    print("   سيتم الاحتفاظ بأحدث إشارة فقط")
    print("\n✅ نعم - سيتم حذف الإشارات القديمة")
    print("❌ لا - سيتم إلغاء العملية")
    
    choice = input("\nاختيارك (نعم/لا): ").strip().lower()
    
    if choice in ['نعم', 'yes', 'y']:
        # حذف الإشارات القديمة، الاحتفاظ بالأحدث
        c.execute('''
            DELETE FROM signals 
            WHERE symbol = 'XAUUSD' 
            AND id NOT IN (
                SELECT id FROM signals 
                WHERE symbol = 'XAUUSD' 
                ORDER BY created_at DESC 
                LIMIT 1
            )
        ''')
        deleted = c.rowcount
        conn.commit()
        print(f"\n✅ تم حذف {deleted} إشارة قديمة للذهب")
        print("✅ تم الاحتفاظ بأحدث إشارة فقط")
    else:
        print("\n❌ تم إلغاء العملية")

conn.close()

print("\n✨ انتهى الفحص!")

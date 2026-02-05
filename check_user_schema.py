#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

# فحص هيكل جدول users
conn = sqlite3.connect('goldpro_system.db')
c = conn.cursor()

print("╔════════════════════════════════════════╗")
print("║   بنية جدول users                   ║")
print("╚════════════════════════════════════════╝\n")

c.execute("PRAGMA table_info(users)")
rows = c.fetchall()

for row in rows:
    column_id, name, type_, notnull, default, pk = row
    print(f"  {name}: {type_} (PK: {pk}, NOT NULL: {notnull})")

print("\n╔════════════════════════════════════════╗")
print("║   بيانات المستخدمين الحالية          ║")
print("╚════════════════════════════════════════╝\n")

c.execute("SELECT * FROM users")
rows = c.fetchall()

for row in rows:
    print(f"  ID: {row[0]}")
    print(f"  البريد: {row[1]}")
    print(f"  الاسم: {row[2]}")
    print(f"  الكلمة: {row[3][:20]}...")
    print(f"  نشط: {row[4]}")
    print(f"  الخطة: {row[5]}")
    print(f"  التاريخ: {row[6]}")
    print()

conn.close()

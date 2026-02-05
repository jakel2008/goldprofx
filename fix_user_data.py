#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import hashlib

# إصلاح بيانات المستخدم
conn = sqlite3.connect('goldpro_system.db')
c = conn.cursor()

print("╔════════════════════════════════════════════════╗")
print("║   إصلاح بيانات المستخدم الاختبار              ║")
print("╚════════════════════════════════════════════════╝\n")

email = 'test@goldpro.com'
password = 'Test123'
full_name = 'Test User'

# حساب الهاش الصحيح
password_hash = hashlib.sha256(password.encode()).hexdigest()

print(f"البريد: {email}")
print(f"الكلمة: {password}")
print(f"الهاش الصحيح: {password_hash}")
print(f"الاسم: {full_name}\n")

# تحديث البيانات
c.execute("""
    UPDATE users 
    SET password_hash = ?, full_name = ?
    WHERE email = ?
""", (password_hash, full_name, email))

conn.commit()

# التحقق
c.execute("SELECT id, email, password_hash, full_name, is_active FROM users WHERE email = ?", (email,))
row = c.fetchone()

if row:
    print("✅ تم التحديث بنجاح!\n")
    print(f"  ID: {row[0]}")
    print(f"  البريد: {row[1]}")
    print(f"  الهاش: {row[2][:20]}...")
    print(f"  الاسم: {row[3]}")
    print(f"  نشط: {row[4]}")
else:
    print("❌ لم يتم العثور على المستخدم")

conn.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح بنية قاعدة البيانات لإضافة chat_id
"""
import sqlite3
import os
import sys

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

DB_PATH = 'vip_subscriptions.db'

def fix_schema():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # فحص إذا كان العمود موجود
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'chat_id' not in columns:
            print("✓ إضافة عمود chat_id...")
            c.execute("ALTER TABLE users ADD COLUMN chat_id TEXT DEFAULT NULL")
            print("✓ تم إضافة chat_id")
        
        if 'telegram_id' not in columns:
            print("✓ إضافة عمود telegram_id...")
            c.execute("ALTER TABLE users ADD COLUMN telegram_id INTEGER DEFAULT NULL")
            print("✓ تم إضافة telegram_id")
            
        conn.commit()
        print("✓ تم تحديث قاعدة البيانات بنجاح!")
        
        # عرض الأعمدة الحالية
        c.execute("PRAGMA table_info(users)")
        print("\nأعمدة جدول المستخدمين الحالية:")
        for col in c.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()

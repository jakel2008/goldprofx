#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إضافة مستخدم اختبار مع chat_id لاختبار البوت
"""
import sqlite3
import sys
import os
from datetime import datetime, timedelta

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

DB_PATH = 'vip_subscriptions.db'

def add_test_user_with_chat_id():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # تحديث المستخدم الأول (اختبار) بـ chat_id
        # استخدم chat_id حقيقي من حسابك على Telegram
        test_chat_id = input("أدخل Chat ID الخاص بك (أو اترك فارغاً للاستخدام الافتراضي): ").strip()
        if not test_chat_id:
            test_chat_id = "123456789"  # قيمة افتراضية
        
        c.execute("""
            UPDATE users 
            SET chat_id = ?, telegram_id = ?
            WHERE user_id = 1
        """, (test_chat_id, int(test_chat_id)))
        
        conn.commit()
        print(f"✓ تم تحديث المستخدم 1 بـ Chat ID: {test_chat_id}")
        
        # عرض بيانات المستخدم
        c.execute("SELECT user_id, username, plan, chat_id, status FROM users WHERE user_id = 1")
        row = c.fetchone()
        if row:
            print(f"\nبيانات المستخدم:")
            print(f"  ID: {row[0]}")
            print(f"  الاسم: {row[1]}")
            print(f"  الخطة: {row[2]}")
            print(f"  Chat ID: {row[3]}")
            print(f"  الحالة: {row[4]}")
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_test_user_with_chat_id()

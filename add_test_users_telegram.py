#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إضافة مستخدمي اختبار حقيقيين مع Chat IDs
"""
import sqlite3
import sys
import os
from datetime import datetime, timedelta

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

DB_PATH = 'vip_subscriptions.db'

def add_test_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # قائمة مستخدمي اختبار مع Chat IDs
        test_users = [
            {
                'username': 'ahmed_trader',
                'chat_id': 123456789,
                'plan': 'gold',
                'first_name': 'أحمد'
            },
            {
                'username': 'fatima_investor',
                'chat_id': 987654321,
                'plan': 'silver',
                'first_name': 'فاطمة'
            },
            {
                'username': 'محمد_برو',
                'chat_id': 555555555,
                'plan': 'platinum',
                'first_name': 'محمد'
            }
        ]
        
        # إضافة أو تحديث المستخدمين
        for user in test_users:
            # فحص إذا كان المستخدم موجود
            c.execute("SELECT user_id FROM users WHERE username = ?", (user['username'],))
            existing = c.fetchone()
            
            if existing:
                # تحديث المستخدم الموجود
                c.execute("""
                    UPDATE users 
                    SET chat_id = ?, telegram_id = ?, plan = ?
                    WHERE username = ?
                """, (str(user['chat_id']), user['chat_id'], user['plan'], user['username']))
                print(f"✓ تحديث المستخدم: {user['username']}")
            else:
                # إضافة مستخدم جديد
                now = datetime.now()
                end_date = now + timedelta(days=30)
                c.execute("""
                    INSERT INTO users 
                    (username, first_name, plan, chat_id, telegram_id, 
                     subscription_start, subscription_end, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['username'],
                    user['first_name'],
                    user['plan'],
                    str(user['chat_id']),
                    user['chat_id'],
                    now.isoformat(),
                    end_date.isoformat(),
                    'active',
                    now.isoformat()
                ))
                print(f"✓ إضافة المستخدم: {user['username']}")
        
        conn.commit()
        
        # عرض بيانات المستخدمين
        print("\n" + "="*60)
        print("📊 بيانات المستخدمين المضافة:")
        print("="*60)
        
        c.execute("SELECT user_id, username, plan, chat_id, status FROM users ORDER BY user_id DESC LIMIT 5")
        rows = c.fetchall()
        for row in rows:
            print(f"ID: {row[0]:3} | الاسم: {row[1]:20} | الخطة: {row[2]:10} | Chat ID: {row[3]:15} | الحالة: {row[4]}")
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_test_users()

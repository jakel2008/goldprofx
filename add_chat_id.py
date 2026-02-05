#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سكريبت لإضافة Chat ID الخاص بك إلى المستخدمين
"""

import sqlite3
from datetime import datetime

def add_user_with_chat_id(chat_id):
    """إضافة مستخدم مع Chat ID"""
    conn = sqlite3.connect('vip_subscriptions.db')
    c = conn.cursor()
    
    # التحقق من وجود المستخدم
    c.execute('SELECT user_id FROM users WHERE chat_id = ?', (str(chat_id),))
    if c.fetchone():
        print(f"❌ Chat ID {chat_id} موجود بالفعل")
        conn.close()
        return False
    
    # إضافة مستخدم جديد
    user_id = int(chat_id)  # استخدام Chat ID كـ user_id
    username = f"user_{user_id}"
    
    try:
        c.execute('''
            INSERT INTO users 
            (user_id, username, chat_id, telegram_id, plan, status, 
             subscription_start, subscription_end)
            VALUES (?, ?, ?, ?, 'platinum', 'active', datetime('now'), 
                   datetime('now', '+1 year'))
        ''', (user_id, username, str(chat_id), user_id))
        
        conn.commit()
        print(f"✅ تم إضافة المستخدم بنجاح!")
        print(f"   Chat ID: {chat_id}")
        print(f"   المخطط: Platinum (مدفوع)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.close()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("إضافة Chat ID الخاص بك")
    print("=" * 50)
    
    chat_id = input("\nأدخل Chat ID الخاص بك (أو اتركه فارغاً لاستخدام الافتراضي): ").strip()
    
    if not chat_id:
        chat_id = "7657829546"  # الافتراضي
        print(f"استخدام الافتراضي: {chat_id}")
    
    add_user_with_chat_id(chat_id)
    
    print("\n✅ اختبر البث الآن!")
    print("   سيتم إرسال الإشارات إلى هذا الرقم")

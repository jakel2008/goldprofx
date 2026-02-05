#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عرض تفاصيل مستخدم واحد
"""
import sqlite3
import sys
import os
from datetime import datetime
import io

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = 'vip_subscriptions.db'

def show_user_details(user_id=None):
    """عرض تفاصيل مستخدم"""
    
    try:
        if user_id is None:
            user_id = input("أدخل معرف المستخدم (ID أو username): ").strip()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # محاولة البحث بـ ID أو username
        if user_id.isdigit():
            c.execute("SELECT * FROM users WHERE user_id = ?", (int(user_id),))
        else:
            c.execute("SELECT * FROM users WHERE username = ?", (user_id,))
        
        user = c.fetchone()
        
        if not user:
            print(f"\n❌ المستخدم '{user_id}' غير موجود")
            conn.close()
            return
        
        # الحصول على أسماء الأعمدة
        cursor = c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print("\n" + "="*70)
        print(f"👤 تفاصيل المستخدم: {user[columns.index('username')]}")
        print("="*70)
        
        # عرض البيانات
        for i, col_name in enumerate(columns):
            value = user[i]
            
            # تنسيق خاص للحقول المهمة
            if col_name == 'chat_id':
                if value:
                    print(f"\n📱 {col_name:.<30} {value}")
                else:
                    print(f"\n📱 {col_name:.<30} لم يسجل بعد")
            elif col_name == 'plan':
                emoji = {'free': '🆓', 'bronze': '🥉', 'silver': '🥈', 'gold': '🥇', 'platinum': '👑'}.get(value, '📋')
                print(f"\n{emoji} {col_name:.<30} {value}")
            elif col_name == 'status':
                emoji = '✅' if value == 'active' else '⏸️' if value == 'inactive' else '⚠️'
                print(f"\n{emoji} {col_name:.<30} {value}")
            elif 'subscription' in col_name or 'created' in col_name:
                if value:
                    dt = datetime.fromisoformat(value)
                    formatted = dt.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"📅 {col_name:.<30} {formatted}")
            elif col_name == 'total_paid':
                print(f"💰 {col_name:.<30} ${value:.2f}" if value else f"💰 {col_name:.<30} $0")
            else:
                print(f"   {col_name:.<30} {value if value else 'بدون'}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    show_user_details()

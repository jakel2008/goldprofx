#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عرض تفاعلي لبيانات المستخدمين
"""
import sqlite3
import sys
import os
import io

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = 'vip_subscriptions.db'

def interactive_user_manager():
    """مدير المستخدمين التفاعلي"""
    
    while True:
        print("\n" + "="*70)
        print("📋 مدير المستخدمين")
        print("="*70)
        print("""
1. عرض جميع المستخدمين
2. عرض تفاصيل مستخدم معين
3. البحث عن مستخدم
4. عرض المستخدمين بخطة معينة
5. عرض المستخدمين بدون Chat ID
6. إضافة Chat ID لمستخدم
7. خروج
        """)
        
        choice = input("اختر رقماً (1-7): ").strip()
        
        if choice == "1":
            show_all_users()
        elif choice == "2":
            user_id = input("أدخل معرف المستخدم (ID أو الاسم): ").strip()
            show_user_details(user_id)
        elif choice == "3":
            search_users()
        elif choice == "4":
            plan = input("أدخل اسم الخطة (free, bronze, silver, gold, platinum): ").strip()
            show_users_by_plan(plan)
        elif choice == "5":
            show_users_without_chat_id()
        elif choice == "6":
            add_chat_id()
        elif choice == "7":
            print("👋 وداعاً!")
            break
        else:
            print("❌ خيار غير صحيح")

def show_all_users():
    """عرض جميع المستخدمين"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT user_id, username, plan, status, chat_id FROM users ORDER BY user_id DESC")
        users = c.fetchall()
        
        print(f"\n{'ID':<8} | {'الاسم':<20} | {'الخطة':<12} | {'الحالة':<10} | {'Chat ID':<15}")
        print("-"*75)
        
        for user in users:
            user_id, username, plan, status, chat_id = user
            status_icon = "✅" if status == "active" else "⏸️"
            chat_display = chat_id if chat_id else "لم يسجل"
            print(f"{user_id:<8} | {username:<20} | {plan:<12} | {status_icon} {status:<8} | {str(chat_display):<15}")
        
        print(f"\n✓ إجمالي المستخدمين: {len(users)}")
        conn.close()
    except Exception as e:
        print(f"❌ خطأ: {e}")

def show_user_details(user_id):
    """عرض تفاصيل مستخدم"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if user_id.isdigit():
            c.execute("SELECT * FROM users WHERE user_id = ?", (int(user_id),))
        else:
            c.execute("SELECT * FROM users WHERE username = ?", (user_id,))
        
        user = c.fetchone()
        
        if not user:
            print(f"❌ المستخدم '{user_id}' غير موجود")
        else:
            cursor = c.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"\n{'='*60}")
            print(f"👤 تفاصيل المستخدم")
            print(f"{'='*60}")
            
            for i, col_name in enumerate(columns):
                value = user[i]
                if value:
                    print(f"{col_name:<20}: {value}")
        
        conn.close()
    except Exception as e:
        print(f"❌ خطأ: {e}")

def search_users():
    """البحث عن مستخدمين"""
    try:
        keyword = input("أدخل كلمة للبحث (في الاسم أو الاسم الأول): ").strip()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT user_id, username, first_name, plan, status 
            FROM users 
            WHERE username LIKE ? OR first_name LIKE ?
            ORDER BY user_id DESC
        """, (f"%{keyword}%", f"%{keyword}%"))
        
        users = c.fetchall()
        
        if not users:
            print(f"❌ لم يتم العثور على مستخدمين يطابقون '{keyword}'")
        else:
            print(f"\n{'ID':<8} | {'الاسم':<20} | {'الاسم الأول':<15} | {'الخطة':<12} | {'الحالة':<10}")
            print("-"*75)
            
            for user in users:
                print(f"{user[0]:<8} | {user[1]:<20} | {user[2]:<15} | {user[3]:<12} | {user[4]:<10}")
            
            print(f"\n✓ النتائج: {len(users)} مستخدم")
        
        conn.close()
    except Exception as e:
        print(f"❌ خطأ: {e}")

def show_users_by_plan(plan):
    """عرض المستخدمين بخطة معينة"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT user_id, username, first_name, status, chat_id, subscription_start, subscription_end 
            FROM users 
            WHERE plan = ?
            ORDER BY user_id DESC
        """, (plan,))
        
        users = c.fetchall()
        
        if not users:
            print(f"❌ لا توجد مستخدمون في خطة '{plan}'")
        else:
            print(f"\n{'='*70}")
            print(f"📋 المستخدمون في خطة: {plan} ({len(users)} مستخدم)")
            print(f"{'='*70}")
            
            print(f"\n{'ID':<8} | {'الاسم':<20} | {'الحالة':<10} | {'Chat ID':<15}")
            print("-"*60)
            
            for user in users:
                user_id, username, first_name, status, chat_id, start, end = user
                status_icon = "✅" if status == "active" else "⏸️"
                chat_display = chat_id if chat_id else "لم يسجل"
                print(f"{user_id:<8} | {username:<20} | {status_icon} {status:<8} | {str(chat_display):<15}")
        
        conn.close()
    except Exception as e:
        print(f"❌ خطأ: {e}")

def show_users_without_chat_id():
    """عرض المستخدمين بدون Chat ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT user_id, username, first_name, plan, status 
            FROM users 
            WHERE chat_id IS NULL OR chat_id = ''
            ORDER BY user_id DESC
        """)
        
        users = c.fetchall()
        
        if not users:
            print("✅ جميع المستخدمين لديهم Chat ID")
        else:
            print(f"\n{'='*70}")
            print(f"📱 المستخدمون بدون Chat ID ({len(users)} مستخدم)")
            print(f"{'='*70}")
            
            print(f"\n{'ID':<8} | {'الاسم':<20} | {'الخطة':<12} | {'الحالة':<10}")
            print("-"*60)
            
            for user in users:
                user_id, username, first_name, plan, status = user
                status_icon = "✅" if status == "active" else "⏸️"
                print(f"{user_id:<8} | {username:<20} | {plan:<12} | {status_icon} {status:<8}")
        
        conn.close()
    except Exception as e:
        print(f"❌ خطأ: {e}")

def add_chat_id():
    """إضافة Chat ID لمستخدم"""
    try:
        user_id = input("أدخل معرف المستخدم: ").strip()
        chat_id = input("أدخل Chat ID الجديد: ").strip()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("UPDATE users SET chat_id = ?, telegram_id = ? WHERE user_id = ?", 
                  (chat_id, int(chat_id) if chat_id.isdigit() else None, int(user_id)))
        
        conn.commit()
        print(f"✅ تم تحديث Chat ID للمستخدم {user_id}")
        
        conn.close()
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    interactive_user_manager()

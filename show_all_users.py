#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عرض جميع المستخدمين في النظام
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

def show_all_users():
    """عرض جميع المستخدمين"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        print("\n" + "="*100)
        print("👥 قائمة جميع المستخدمين في النظام")
        print("="*100)
        
        # جلب جميع المستخدمين
        c.execute("""
            SELECT user_id, username, first_name, plan, status, chat_id, 
                   subscription_start, subscription_end, total_paid
            FROM users
            ORDER BY user_id DESC
        """)
        
        users = c.fetchall()
        
        if not users:
            print("❌ لا توجد مستخدمون في النظام")
            return
        
        print(f"\n📊 إجمالي المستخدمين: {len(users)}\n")
        
        # رأس الجدول
        print(f"{'ID':<8} | {'الاسم':<20} | {'الخطة':<12} | {'الحالة':<10} | {'Chat ID':<15} | {'الدفع':<10}")
        print("-" * 100)
        
        # عرض البيانات
        for user in users:
            user_id = user[0]
            username = user[1][:20] if user[1] else "بدون اسم"
            first_name = user[2] if user[2] else ""
            plan = user[3] if user[3] else "بدون"
            status = user[4] if user[4] else "معلق"
            chat_id = user[5] if user[5] else "لم يسجل"
            total_paid = f"${user[8]:.2f}" if user[8] else "$0"
            
            # تحديد رمز الحالة
            status_icon = "✅" if status == "active" else "⏸️" if status == "inactive" else "⚠️"
            
            print(f"{user_id:<8} | {username:<20} | {plan:<12} | {status_icon} {status:<8} | {str(chat_id):<15} | {total_paid:<10}")
        
        # إحصائيات
        print("\n" + "="*100)
        print("📈 الإحصائيات:")
        print("="*100)
        
        c.execute("SELECT status, COUNT(*) FROM users GROUP BY status")
        status_stats = c.fetchall()
        
        print("\nتوزيع الحالات:")
        for status, count in status_stats:
            status_emoji = "✅" if status == "active" else "⏸️" if status == "inactive" else "⚠️"
            print(f"  {status_emoji} {status}: {count} مستخدم")
        
        c.execute("SELECT plan, COUNT(*) FROM users GROUP BY plan ORDER BY plan")
        plan_stats = c.fetchall()
        
        print("\nتوزيع الخطط:")
        for plan, count in plan_stats:
            print(f"  📋 {plan}: {count} مستخدم")
        
        c.execute("SELECT COUNT(*) FROM users WHERE chat_id IS NOT NULL")
        chat_count = c.fetchone()[0]
        print(f"\nالمستخدمون بـ Chat ID: {chat_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    show_all_users()

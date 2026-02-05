#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار نظام الأدمن والمستخدمين
Test Admin & User System
"""

import os
import sys
from datetime import datetime

# Encoding fix
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from vip_subscription_system import SubscriptionManager
from admin_panel import AdminPanel

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_add_users():
    """اختبار إضافة المستخدمين"""
    print_header("✅ اختبار 1: إضافة المستخدمين")
    
    sm = SubscriptionManager()
    
    # مستخدمين تجريبيين
    test_users = [
        (7657829546, "admin_user", "Admin User"),
        (123456789, "first_user", "First User"),
        (987654321, "second_user", "Second User"),
    ]
    
    for user_id, username, first_name in test_users:
        success, msg = sm.add_user(user_id, username, first_name)
        status = "✅" if success else "❌"
        print(f"  {status} {user_id} -> {msg}")
    
    print("\n✅ انتهى اختبار الإضافة")

def test_enable_admins():
    """اختبار تفعيل الأدمن"""
    print_header("✅ اختبار 2: تفعيل الأدمن")
    
    admin = AdminPanel()
    
    # تفعيل أدمن
    admin_ids = [7657829546, 123456789]
    
    for admin_id in admin_ids:
        admin.add_admin(admin_id)
        is_admin = admin.is_admin(admin_id)
        print(f"  ✅ {admin_id} -> أدمن: {'✅ نعم' if is_admin else '❌ لا'}")
    
    print("\n✅ انتهى اختبار تفعيل الأدمن")

def test_list_admins():
    """اختبار عرض الأدمن"""
    print_header("✅ اختبار 3: عرض قائمة الأدمن")
    
    admin = AdminPanel()
    admin.list_admins()
    
    print("✅ انتهى اختبار العرض")

def test_upgrade_users():
    """اختبار ترقية المستخدمين"""
    print_header("✅ اختبار 4: ترقية المستخدمين")
    
    sm = SubscriptionManager()
    
    upgrades = [
        (123456789, 'bronze'),
        (987654321, 'silver'),
    ]
    
    for user_id, plan in upgrades:
        success, msg = sm.upgrade_user(user_id, plan, payment_method='admin_test')
        status = "✅" if success else "❌"
        print(f"  {status} {user_id} -> {plan}: {msg}")
    
    print("\n✅ انتهى اختبار الترقية")

def test_view_users():
    """اختبار عرض بيانات المستخدمين"""
    print_header("✅ اختبار 5: عرض بيانات المستخدمين")
    
    sm = SubscriptionManager()
    admin = AdminPanel()
    
    user_ids = [7657829546, 123456789, 987654321]
    
    for user_id in user_ids:
        print(f"\n  👤 المستخدم: {user_id}")
        admin.view_user(user_id)

def test_list_all():
    """اختبار عرض جميع المستخدمين"""
    print_header("✅ اختبار 6: عرض جميع المستخدمين")
    
    admin = AdminPanel()
    admin.list_all_users()

def test_check_admin():
    """اختبار التحقق من الأدمن"""
    print_header("✅ اختبار 7: التحقق من صلاحيات الأدمن")
    
    admin = AdminPanel()
    
    check_ids = [7657829546, 123456789, 999999999]
    
    for user_id in check_ids:
        is_admin = admin.is_admin(user_id)
        status = "👑 أدمن" if is_admin else "👤 مستخدم عادي"
        print(f"  {user_id}: {status}")

def show_summary():
    """عرض ملخص النظام"""
    print_header("📊 ملخص النظام")
    
    sm = SubscriptionManager()
    admin = AdminPanel()
    
    import sqlite3
    conn = sqlite3.connect(sm.db_path)
    c = conn.cursor()
    
    # عد المستخدمين
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    
    # عد الأدمن
    total_admins = len(admin.admins)
    
    # عد الاشتراكات النشطة
    c.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
    active_subs = c.fetchone()[0]
    
    # إجمالي المدفوع
    c.execute('SELECT SUM(total_paid) FROM users')
    total_paid = c.fetchone()[0] or 0
    
    conn.close()
    
    print(f"  📊 إجمالي المستخدمين: {total_users}")
    print(f"  👑 عدد الأدمن: {total_admins}")
    print(f"  ✅ الاشتراكات النشطة: {active_subs}")
    print(f"  💰 إجمالي المدفوع: ${total_paid:.2f}")

def main():
    """البرنامج الرئيسي"""
    
    print("""
================================================
    Test Admin & User System
================================================
    """)
    
    try:
        # تنفيذ الاختبارات
        test_add_users()
        input("اضغط Enter للمتابعة...")
        
        test_enable_admins()
        input("اضغط Enter للمتابعة...")
        
        test_list_admins()
        input("اضغط Enter للمتابعة...")
        
        test_upgrade_users()
        input("اضغط Enter للمتابعة...")
        
        test_view_users()
        input("اضغط Enter للمتابعة...")
        
        test_list_all()
        input("اضغط Enter للمتابعة...")
        
        test_check_admin()
        input("اضغط Enter للمتابعة...")
        
        show_summary()
        
        print_header("✅ انتهت جميع الاختبارات بنجاح!")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ تم الإيقاف من قبل المستخدم")
        sys.exit(0)

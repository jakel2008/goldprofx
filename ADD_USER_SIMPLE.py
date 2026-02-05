#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
أداة سريعة لإضافة مستخدم واحد
Quick Tool: Add Single User
"""

import sys
import os

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from vip_subscription_system import SubscriptionManager
from admin_panel import AdminPanel

def quick_add_user():
    """إضافة سريعة"""
    print("""
================================================
   أداة إضافة مستخدم سريعة
================================================
    """)
    
    sm = SubscriptionManager()
    admin = AdminPanel()
    
    # طلب البيانات
    print("\n📝 الرجاء إدخال بيانات المستخدم الجديد:")
    print("─" * 50)
    
    user_id = input("🔑 معرف المستخدم (User ID): ").strip()
    username = input("👤 اسم المستخدم (Username): ").strip()
    first_name = input("📛 الاسم الأول (First Name - اختياري): ").strip()
    
    if not user_id or not username:
        print("❌ معرف المستخدم والاسم مطلوبان!")
        return
    
    try:
        user_id = int(user_id)
    except ValueError:
        print("❌ معرف المستخدم يجب أن يكون رقم!")
        return
    
    # إضافة المستخدم
    print("\n⏳ جاري الإضافة...")
    success, msg = sm.add_user(user_id, username, first_name)
    
    if success:
        print(f"✅ {msg}")
        
        # خيار تفعيل كأدمن
        print("\n" + "─" * 50)
        make_admin = input("هل تريد تفعيل هذا المستخدم كأدمن؟ (y/n): ").strip().lower()
        
        if make_admin == 'y':
            admin.add_admin(user_id)
            print(f"✅ تم تفعيل الأدمن!")
        
        # خيار الترقية
        print("\n" + "─" * 50)
        upgrade = input("هل تريد ترقية المستخدم لباقة مدفوعة؟ (y/n): ").strip().lower()
        
        if upgrade == 'y':
            print("\nالباقات المتاحة:")
            print("  1. bronze   - $29")
            print("  2. silver   - $69")
            print("  3. gold     - $199")
            print("  4. platinum - $499")
            
            plan_choice = input("\nاختر رقم الباقة (1-4): ").strip()
            plans = {'1': 'bronze', '2': 'silver', '3': 'gold', '4': 'platinum'}
            
            if plan_choice in plans:
                plan = plans[plan_choice]
                success, msg = sm.upgrade_user(user_id, plan, payment_method='admin')
                
                if success:
                    print(f"✅ {msg}")
                else:
                    print(f"❌ {msg}")
        
        # عرض ملخص
        print("\n" + "=" * 50)
        print("📊 ملخص المستخدم:")
        print("=" * 50)
        admin.view_user(user_id)
        
    else:
        print(f"❌ {msg}")

if __name__ == "__main__":
    try:
        quick_add_user()
    except KeyboardInterrupt:
        print("\n\n❌ تم الإيقاف من قبل المستخدم")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        sys.exit(1)

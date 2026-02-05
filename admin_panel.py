#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
لوحة التحكم الإدارية - إضافة مستخدمين وتفعيل الأدمن
Admin Control Panel
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Encoding fix for Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from vip_subscription_system import SubscriptionManager

# ============================================
# إدارة المستخدمين والأدمن
# ============================================

class AdminPanel:
    def __init__(self):
        self.sm = SubscriptionManager()
        self.admin_file = "admin_users.json"
        self.admins = self.load_admins()
    
    def load_admins(self):
        """تحميل قائمة الأدمن"""
        import json
        try:
            if os.path.exists(self.admin_file):
                with open(self.admin_file, 'r') as f:
                    return set(json.load(f))
        except:
            pass
        return set()
    
    def save_admins(self):
        """حفظ قائمة الأدمن"""
        import json
        try:
            with open(self.admin_file, 'w') as f:
                json.dump(list(self.admins), f, indent=2)
            return True
        except Exception as e:
            print(f"❌ خطأ في الحفظ: {e}")
            return False
    
    def add_admin(self, user_id):
        """تفعيل الأدمن"""
        self.admins.add(user_id)
        if self.save_admins():
            print(f"✅ تم تفعيل الأدمن {user_id}")
            return True
        return False
    
    def remove_admin(self, user_id):
        """إزالة الأدمن"""
        if user_id in self.admins:
            self.admins.remove(user_id)
            self.save_admins()
            print(f"✅ تم إزالة الأدمن {user_id}")
            return True
        print(f"❌ الأدمن {user_id} غير موجود")
        return False
    
    def is_admin(self, user_id):
        """التحقق من أنه أدمن"""
        return user_id in self.admins
    
    def list_admins(self):
        """عرض قائمة الأدمن"""
        if not self.admins:
            print("❌ لا توجد أدمن")
            return
        print(f"\n{'='*50}")
        print(f"قائمة الأدمن ({len(self.admins)})")
        print(f"{'='*50}")
        for admin_id in sorted(self.admins):
            print(f"  • {admin_id}")
        print(f"{'='*50}\n")
    
    def add_new_user(self, user_id, username, first_name=""):
        """إضافة مستخدم جديد"""
        success, message = self.sm.add_user(user_id, username, first_name)
        
        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False
    
    def upgrade_user(self, user_id, plan):
        """ترقية مستخدم لباقة محددة"""
        valid_plans = ['bronze', 'silver', 'gold', 'platinum']
        
        if plan not in valid_plans:
            print(f"❌ باقة غير صحيحة. الباقات المتاحة: {', '.join(valid_plans)}")
            return False
        
        success, message = self.sm.upgrade_user(user_id, plan, payment_method='admin')
        
        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False
    
    def view_user(self, user_id):
        """عرض بيانات المستخدم"""
        sub_info = self.sm.check_subscription(user_id)
        
        if not sub_info.get('exists'):
            print(f"❌ المستخدم {user_id} غير موجود")
            return
        
        print(f"\n{'='*50}")
        print(f"بيانات المستخدم {user_id}")
        print(f"{'='*50}")
        print(f"الباقة: {sub_info.get('plan', 'unknown').upper()}")
        print(f"الحالة: {sub_info.get('status', 'unknown')}")
        print(f"نشط: {'✅ نعم' if sub_info.get('is_active') else '❌ لا'}")
        print(f"أيام متبقية: {sub_info.get('days_left', 0)}")
        print(f"تاريخ البدء: {sub_info.get('start_date', 'N/A')}")
        print(f"تاريخ الانتهاء: {sub_info.get('end_date', 'N/A')}")
        print(f"كود الإحالة: {sub_info.get('referral_code', 'N/A')}")
        print(f"{'='*50}\n")
    
    def list_all_users(self):
        """عرض جميع المستخدمين"""
        conn = sqlite3.connect(self.sm.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT user_id, username, first_name, plan, status, 
                   subscription_end
            FROM users
            ORDER BY created_at DESC
        ''')
        
        users = c.fetchall()
        conn.close()
        
        if not users:
            print("❌ لا توجد مستخدمين")
            return
        
        print(f"\n{'='*80}")
        print(f"جميع المستخدمين ({len(users)})")
        print(f"{'='*80}")
        print(f"{'المعرف':<15} {'الاسم':<20} {'الباقة':<12} {'الحالة':<12}")
        print(f"{'─'*80}")
        
        for user_id, username, first_name, plan, status, end_date in users:
            print(f"{user_id:<15} {username:<20} {plan:<12} {status:<12}")
        
        print(f"{'='*80}\n")
    
    def delete_user(self, user_id):
        """حذف مستخدم"""
        conn = sqlite3.connect(self.sm.db_path)
        c = conn.cursor()
        
        c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ تم حذف المستخدم {user_id}")
    
    def export_users_report(self):
        """تصدير تقرير المستخدمين"""
        conn = sqlite3.connect(self.sm.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT user_id, username, first_name, plan, status, 
                   subscription_end, total_paid, created_at
            FROM users
            ORDER BY created_at DESC
        ''')
        
        users = c.fetchall()
        conn.close()
        
        # إنشاء ملف التقرير
        filename = f"users_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("تقرير المستخدمين\n")
            f.write("="*80 + "\n")
            f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"إجمالي المستخدمين: {len(users)}\n")
            f.write("="*80 + "\n\n")
            
            for user_id, username, first_name, plan, status, end_date, paid, created in users:
                f.write(f"المعرف: {user_id}\n")
                f.write(f"الاسم: {username} ({first_name})\n")
                f.write(f"الباقة: {plan}\n")
                f.write(f"الحالة: {status}\n")
                f.write(f"المدفوع: ${paid}\n")
                f.write(f"تاريخ التسجيل: {created}\n")
                f.write("─"*80 + "\n")
        
        print(f"✅ تم تصدير التقرير: {filename}")

# ============================================
# القائمة الرئيسية
# ============================================

def show_menu():
    """عرض القائمة الرئيسية"""
    print("\n" + "="*50)
    print("لوحة التحكم الإدارية - VIP Bot")
    print("="*50)
    print("1. إضافة مستخدم جديد")
    print("2. تفعيل الأدمن")
    print("3. إزالة الأدمن")
    print("4. عرض قائمة الأدمن")
    print("5. ترقية مستخدم")
    print("6. عرض بيانات مستخدم")
    print("7. عرض جميع المستخدمين")
    print("8. حذف مستخدم")
    print("9. تصدير تقرير")
    print("0. خروج")
    print("="*50)

def main():
    """البرنامج الرئيسي"""
    admin = AdminPanel()
    
    while True:
        show_menu()
        choice = input("اختر خيار (0-9): ").strip()
        
        if choice == '1':
            # إضافة مستخدم جديد
            print("\n--- إضافة مستخدم جديد ---")
            user_id = input("معرف المستخدم (User ID): ").strip()
            username = input("اسم المستخدم (Username): ").strip()
            first_name = input("الاسم الأول (اختياري): ").strip()
            
            if user_id and username:
                try:
                    admin.add_new_user(int(user_id), username, first_name)
                except ValueError:
                    print("❌ معرف المستخدم يجب أن يكون رقم")
            else:
                print("❌ معرف المستخدم والاسم مطلوبان")
        
        elif choice == '2':
            # تفعيل الأدمن
            print("\n--- تفعيل الأدمن ---")
            user_id = input("معرف المستخدم: ").strip()
            
            try:
                admin.add_admin(int(user_id))
            except ValueError:
                print("❌ معرف المستخدم يجب أن يكون رقم")
        
        elif choice == '3':
            # إزالة الأدمن
            print("\n--- إزالة الأدمن ---")
            user_id = input("معرف المستخدم: ").strip()
            
            try:
                admin.remove_admin(int(user_id))
            except ValueError:
                print("❌ معرف المستخدم يجب أن يكون رقم")
        
        elif choice == '4':
            # عرض الأدمن
            admin.list_admins()
        
        elif choice == '5':
            # ترقية مستخدم
            print("\n--- ترقية مستخدم ---")
            user_id = input("معرف المستخدم: ").strip()
            plan = input("اختر الباقة (bronze/silver/gold/platinum): ").strip().lower()
            
            try:
                admin.upgrade_user(int(user_id), plan)
            except ValueError:
                print("❌ معرف المستخدم يجب أن يكون رقم")
        
        elif choice == '6':
            # عرض بيانات مستخدم
            print("\n--- عرض بيانات مستخدم ---")
            user_id = input("معرف المستخدم: ").strip()
            
            try:
                admin.view_user(int(user_id))
            except ValueError:
                print("❌ معرف المستخدم يجب أن يكون رقم")
        
        elif choice == '7':
            # عرض جميع المستخدمين
            admin.list_all_users()
        
        elif choice == '8':
            # حذف مستخدم
            print("\n--- حذف مستخدم ---")
            user_id = input("معرف المستخدم: ").strip()
            confirm = input("هل أنت متأكد؟ (y/n): ").strip().lower()
            
            if confirm == 'y':
                try:
                    admin.delete_user(int(user_id))
                except ValueError:
                    print("❌ معرف المستخدم يجب أن يكون رقم")
            else:
                print("❌ تم الإلغاء")
        
        elif choice == '9':
            # تصدير تقرير
            admin.export_users_report()
        
        elif choice == '0':
            # خروج
            print("\n✅ وداعاً!")
            break
        
        else:
            print("❌ اختيار غير صحيح")
        
        input("\nاضغط Enter للمتابعة...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ تم الإيقاف من قبل المستخدم")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        sys.exit(1)

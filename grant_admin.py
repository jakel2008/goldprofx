"""
أداة سريعة لمنح صلاحيات الأدمن لمستخدم
Quick Admin Grant Tool
"""

import sqlite3
from pathlib import Path

DATABASE_FILE = Path(__file__).parent / 'users.db'

def list_users():
    """عرض قائمة المستخدمين"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # التأكد من وجود عمود is_admin
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'is_admin' not in columns:
            print("⚠️ إضافة عمود is_admin...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ تم إضافة عمود is_admin")
        
        cursor.execute('''
            SELECT id, username, email, full_name, is_admin
            FROM users
            ORDER BY id
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("\n❌ لا يوجد مستخدمون في قاعدة البيانات")
            print("💡 قم بالتسجيل أولاً من خلال: http://localhost:5000/register")
            return []
        
        print("\n" + "="*80)
        print("📋 قائمة المستخدمين:")
        print("="*80)
        for user in users:
            admin_status = "👑 مشرف" if user[4] else "👤 مستخدم عادي"
            print(f"ID: {user[0]:<5} | {user[1]:<20} | {user[2]:<30} | {admin_status}")
        print("="*80)
        
        return users
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return []

def grant_admin(user_id):
    """منح صلاحيات الأدمن لمستخدم"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # التحقق من وجود المستخدم
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ المستخدم بالمعرف {user_id} غير موجود")
            conn.close()
            return False
        
        # منح صلاحيات الأدمن
        cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        print(f"\n✅ تم منح صلاحيات المشرف للمستخدم: {user[0]}")
        print(f"🎉 يمكن الآن الوصول إلى لوحة الإدارة: http://localhost:5000/admin-panel")
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def remove_admin(user_id):
    """إزالة صلاحيات الأدمن من مستخدم"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ المستخدم بالمعرف {user_id} غير موجود")
            conn.close()
            return False
        
        cursor.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        print(f"\n✅ تم إزالة صلاحيات المشرف من: {user[0]}")
        return True
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def main():
    """البرنامج الرئيسي"""
    print("\n" + "="*80)
    print("🛡️  أداة إدارة صلاحيات المشرفين - Admin Management Tool")
    print("="*80)
    
    users = list_users()
    
    if not users:
        return
    
    print("\n📌 الخيارات:")
    print("1️⃣  منح صلاحيات المشرف (Grant Admin)")
    print("2️⃣  إزالة صلاحيات المشرف (Remove Admin)")
    print("3️⃣  تحديث القائمة (Refresh)")
    print("0️⃣  خروج (Exit)")
    
    while True:
        try:
            choice = input("\n👉 اختر العملية (1/2/3/0): ").strip()
            
            if choice == '0':
                print("👋 إلى اللقاء!")
                break
            elif choice == '1':
                user_id = input("🆔 أدخل معرف المستخدم (ID): ").strip()
                if user_id.isdigit():
                    grant_admin(int(user_id))
                else:
                    print("❌ المعرف يجب أن يكون رقماً")
            elif choice == '2':
                user_id = input("🆔 أدخل معرف المستخدم (ID): ").strip()
                if user_id.isdigit():
                    remove_admin(int(user_id))
                else:
                    print("❌ المعرف يجب أن يكون رقماً")
            elif choice == '3':
                users = list_users()
            else:
                print("❌ خيار غير صحيح")
                
        except KeyboardInterrupt:
            print("\n\n👋 تم إيقاف البرنامج")
            break
        except Exception as e:
            print(f"❌ خطأ: {e}")

if __name__ == '__main__':
    main()

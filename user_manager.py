"""
نظام إدارة المستخدمين
User Management System for Web App
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path

DATABASE_FILE = Path(__file__).parent / 'users.db'

class UserManager:
    def update_user_email(self, username, new_email):
        """تحديث البريد الإلكتروني للمستخدم حسب الاسم"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, username))
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'تم تحديث البريد بنجاح'}
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # جدول المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    plan TEXT DEFAULT 'free',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # إضافة عمود is_admin إن لم يكن موجودًا
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'is_admin' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            if 'role' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            
            # جدول جلسات المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    ip_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # جدول الأنشطة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            conn.commit()
            conn.close()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def hash_password(self, password):
        """تشفير كلمة المرور"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(self, stored_hash, password):
        """التحقق من كلمة المرور"""
        try:
            salt, pwd_hash = stored_hash.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return new_hash.hex() == pwd_hash
        except:
            return False
    
    def register_user(self, username, email, password, full_name):
        """تسجيل مستخدم جديد"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # التحقق من عدم وجود المستخدم
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                return {'success': False, 'message': 'اسم المستخدم أو البريد موجود بالفعل'}
            
            # إضافة المستخدم الجديد
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, is_admin)
                VALUES (?, ?, ?, ?, 'user', 0)
            ''', (username, email, password_hash, full_name))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # تسجيل النشاط
            self.log_activity(user_id, 'registration', 'New user registered')
            
            return {'success': True, 'message': 'تم التسجيل بنجاح', 'user_id': user_id}
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}
    
    def login_user(self, username, password, ip_address=''):
        """تسجيل دخول المستخدم"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # البحث عن المستخدم
            cursor.execute('''
                SELECT id, password_hash, is_active FROM users WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()
            
            if not result:
                return {'success': False, 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}
            
            user_id, password_hash, is_active = result
            
            if not is_active:
                return {'success': False, 'message': 'الحساب غير مفعل'}
            
            if not self.verify_password(password_hash, password):
                return {'success': False, 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}
            
            # إنشاء جلسة جديدة
            session_token = secrets.token_urlsafe(32)
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, ip_address, expires_at)
                VALUES (?, ?, ?, datetime('now', '+30 days'))
            ''', (user_id, session_token, ip_address))
            
            # تحديث آخر تسجيل دخول
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            # تسجيل النشاط
            self.log_activity(user_id, 'login', f'Login from {ip_address}')
            
            return {
                'success': True,
                'message': 'تسجيل دخول ناجح',
                'session_token': session_token,
                'user_id': user_id
            }
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}
    
    def verify_session(self, session_token):
        """التحقق من صحة الجلسة"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.email, u.full_name, u.plan, u.is_admin, u.role
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_token = ? AND us.expires_at > CURRENT_TIMESTAMP
            ''', (session_token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                role = result[6] if len(result) > 6 else 'user'
                is_admin = bool(result[5]) or role in ('admin', 'developer')
                return {
                    'success': True,
                    'user_id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'full_name': result[3],
                    'plan': result[4],
                    'is_admin': is_admin,
                    'role': role
                }
            return {'success': False}
        except:
            return {'success': False}

    def set_user_role(self, user_id, role):
        """تحديث دور المستخدم (developer/admin/user)"""
        if role not in ('developer', 'admin', 'user'):
            return {'success': False, 'message': 'دور غير صالح'}
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            is_admin = 1 if role in ('developer', 'admin') else 0
            cursor.execute('''
                UPDATE users SET role = ?, is_admin = ? WHERE id = ?
            ''', (role, is_admin, user_id))
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_user_info(self, user_id):
        """الحصول على معلومات المستخدم"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, full_name, plan, created_at, last_login, is_active, is_admin
                FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'full_name': result[3],
                    'plan': result[4],
                    'created_at': result[5],
                    'last_login': result[6],
                    'is_active': bool(result[7]),
                    'is_admin': bool(result[8])
                }
            return None
        except:
            return None
    
    def logout_user(self, session_token):
        """تسجيل خروج المستخدم"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM user_sessions WHERE session_token = ?
            ''', (session_token,))
            
            conn.commit()
            conn.close()
            return {'success': True}
        except:
            return {'success': False}
    
    def log_activity(self, user_id, action, details=''):
        """تسجيل نشاط المستخدم"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_activity (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, details))
            
            conn.commit()
            conn.close()
        except:
            pass
    
    def update_user_plan(self, user_id, plan):
        """تحديث خطة المستخدم"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET plan = ? WHERE id = ?
            ''', (plan, user_id))
            
            conn.commit()
            conn.close()
            
            self.log_activity(user_id, 'plan_update', f'Plan changed to {plan}')
            return {'success': True}
        except:
            return {'success': False}

    # إدارة صلاحيات الأدمن
    def set_admin_status(self, user_id, is_admin: bool):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_admin = ? WHERE id = ?', (1 if is_admin else 0, user_id))
            conn.commit()
            conn.close()
            self.log_activity(user_id, 'admin_update', f'Admin set to {is_admin}')
            return {'success': True}
        except Exception:
            return {'success': False}

    def set_active_status(self, user_id, is_active: bool):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (1 if is_active else 0, user_id))
            conn.commit()
            conn.close()
            self.log_activity(user_id, 'active_update', f'Active set to {is_active}')
            return {'success': True}
        except Exception:
            return {'success': False}

    def list_users(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, full_name, plan, is_active, is_admin, role, created_at, last_login
                FROM users ORDER BY id DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
            users = []
            for r in rows:
                role = r[7] if len(r) > 7 and r[7] else 'user'
                is_admin = bool(r[6]) or role in ('admin', 'developer')
                users.append({
                    'id': r[0],
                    'username': r[1],
                    'email': r[2],
                    'full_name': r[3],
                    'plan': r[4],
                    'is_active': bool(r[5]),
                    'is_admin': is_admin,
                    'role': role,
                    'created_at': r[8],
                    'last_login': r[9]
                })
            return users
        except Exception:
            return []

# إنشاء مثيل عام
user_manager = UserManager()

"""
نظام إدارة المستخدمين
User Management System for Web App
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime
from pathlib import Path

_default_data_dir = Path('/var/data') if Path('/var/data').exists() else Path(__file__).parent
_data_dir = Path(os.environ.get('GOLDPRO_DATA_DIR', str(_default_data_dir)))
try:
    _data_dir.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

DATABASE_FILE = Path(os.environ.get('USERS_DB_PATH', str(_data_dir / 'users.db')))

class UserManager:
    def _normalize_email(self, email):
        """تطبيع البريد الإلكتروني لتفادي مشاكل المقارنة والتكرار."""
        return str(email or '').strip().lower()

    def update_user_email(self, username, new_email):
        """تحديث البريد الإلكتروني للمستخدم حسب الاسم"""
        try:
            normalized_email = self._normalize_email(new_email)
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email = ? WHERE username = ?", (normalized_email, username))
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
            if 'phone' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            if 'country' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN country TEXT")
            if 'nickname' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
            if 'deleted_at' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP")
            if 'deleted_by' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN deleted_by TEXT")
            if 'delete_reason' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN delete_reason TEXT")
            if 'email_verified' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 1")
            if 'activation_token' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN activation_token TEXT")
            if 'activation_sent_at' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN activation_sent_at TIMESTAMP")
            if 'activated_at' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN activated_at TIMESTAMP")
            if 'marketing_email_opt_in' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN marketing_email_opt_in BOOLEAN DEFAULT 1")
            if 'whatsapp_opt_in' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN whatsapp_opt_in BOOLEAN DEFAULT 0")

            cursor.execute("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL")
            cursor.execute("UPDATE users SET marketing_email_opt_in = 1 WHERE marketing_email_opt_in IS NULL")
            cursor.execute("UPDATE users SET whatsapp_opt_in = 0 WHERE whatsapp_opt_in IS NULL")
            
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

    def _generate_activation_token(self):
        """توليد رمز تفعيل آمن وفريد."""
        return secrets.token_urlsafe(48)
    
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
    
    def register_user(self, username, email, password, full_name, phone=None, country=None, nickname=None,
                      marketing_email_opt_in=True, whatsapp_opt_in=False):
        """تسجيل مستخدم جديد مع إنشاء رمز تفعيل وإبقاء بيانات التواصل محفوظة."""
        try:
            normalized_email = self._normalize_email(email)
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            # التحقق من عدم وجود المستخدم
            cursor.execute(
                '''
                SELECT id FROM users
                WHERE (username = ? OR email = ?)
                  AND (deleted_at IS NULL OR deleted_at = '')
                ''',
                (username, normalized_email)
            )
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'message': 'اسم المستخدم أو البريد موجود بالفعل'}
            # إضافة المستخدم الجديد
            password_hash = self.hash_password(password)
            activation_token = self._generate_activation_token()
            cursor.execute('''
                INSERT INTO users (
                    username, email, password_hash, full_name, role, is_admin,
                    phone, country, nickname, is_active, email_verified,
                    activation_token, activation_sent_at, marketing_email_opt_in, whatsapp_opt_in
                )
                VALUES (?, ?, ?, ?, 'user', 0, ?, ?, ?, 0, 0, ?, CURRENT_TIMESTAMP, ?, ?)
            ''', (
                username,
                normalized_email,
                password_hash,
                full_name,
                phone,
                country,
                nickname,
                activation_token,
                1 if marketing_email_opt_in else 0,
                1 if whatsapp_opt_in else 0,
            ))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            # تسجيل النشاط
            self.log_activity(user_id, 'registration', 'New user registered')
            return {
                'success': True,
                'message': 'تم التسجيل بنجاح. تحقق من بريدك الإلكتروني لتفعيل الحساب.',
                'user_id': user_id,
                'activation_token': activation_token,
                'email': normalized_email
            }
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}

    def activate_user_by_id(self, user_id, actor='admin', reason='manual_activation'):
        """تفعيل حساب المستخدم مباشرة بدون الحاجة للبريد."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT id, email_verified, deleted_at
                FROM users
                WHERE id = ?
                ''',
                (user_id,)
            )
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'success': False, 'message': 'المستخدم غير موجود.'}

            found_user_id, email_verified, deleted_at = result
            if deleted_at:
                conn.close()
                return {'success': False, 'message': 'الحساب محذوف بواسطة الإدارة.'}

            if email_verified:
                conn.close()
                return {'success': True, 'message': 'الحساب مفعل مسبقاً.', 'user_id': found_user_id, 'already_active': True}

            cursor.execute(
                '''
                UPDATE users
                SET is_active = 1,
                    email_verified = 1,
                    activated_at = CURRENT_TIMESTAMP,
                    activation_token = NULL
                WHERE id = ?
                ''',
                (found_user_id,)
            )
            conn.commit()
            conn.close()
            actor_label = str(actor or 'system')
            reason_label = str(reason or 'manual_activation')
            self.log_activity(found_user_id, 'email_activation_fallback', f'actor={actor_label}; reason={reason_label}')
            return {'success': True, 'message': 'تم تفعيل الحساب من لوحة الإدارة.', 'user_id': found_user_id, 'already_active': False}
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}

    def activate_user(self, activation_token):
        """تفعيل المستخدم بواسطة رمز التفعيل المرسل عبر البريد."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT id, email_verified, deleted_at
                FROM users
                WHERE activation_token = ?
                ''',
                (activation_token,)
            )
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'success': False, 'message': 'رابط التفعيل غير صالح أو منتهي.'}

            user_id, email_verified, deleted_at = result
            if deleted_at:
                conn.close()
                return {'success': False, 'message': 'الحساب محذوف بواسطة الإدارة.'}

            if email_verified:
                conn.close()
                return {'success': True, 'message': 'الحساب مفعل مسبقاً.', 'user_id': user_id, 'already_active': True}

            cursor.execute(
                '''
                UPDATE users
                SET is_active = 1,
                    email_verified = 1,
                    activated_at = CURRENT_TIMESTAMP,
                    activation_token = NULL
                WHERE id = ?
                ''',
                (user_id,)
            )
            conn.commit()
            conn.close()
            self.log_activity(user_id, 'email_activation', 'Account activated via email link')
            return {'success': True, 'message': 'تم تفعيل الحساب بنجاح.', 'user_id': user_id, 'already_active': False}
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}

    def regenerate_activation_token(self, username_or_email):
        """إعادة إصدار رابط تفعيل جديد للحساب غير المفعل."""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT id, username, email, full_name, email_verified, deleted_at
                FROM users
                WHERE lower(username) = lower(?) OR lower(email) = lower(?)
                LIMIT 1
                ''',
                (username_or_email, username_or_email)
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                return {'success': False, 'message': 'لا يوجد حساب مطابق لهذا البريد أو اسم المستخدم.'}

            if row['deleted_at']:
                conn.close()
                return {'success': False, 'message': 'الحساب محذوف بواسطة الإدارة.'}

            if row['email_verified']:
                conn.close()
                return {'success': False, 'message': 'الحساب مفعل بالفعل.'}

            token = self._generate_activation_token()
            cursor.execute(
                '''
                UPDATE users
                SET activation_token = ?, activation_sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (token, row['id'])
            )
            conn.commit()
            conn.close()
            return {
                'success': True,
                'message': 'تم إنشاء رابط تفعيل جديد.',
                'user_id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'full_name': row['full_name'],
                'activation_token': token
            }
        except Exception as e:
            return {'success': False, 'message': f'خطأ: {str(e)}'}
    
    def login_user(self, username_or_email, password, ip_address=''):
        """تسجيل دخول المستخدم باسم المستخدم أو البريد الإلكتروني"""
        try:
            identifier = str(username_or_email or '').strip()
            normalized_email = self._normalize_email(identifier)
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            # البحث عن المستخدم بالاسم أو البريد
            cursor.execute('''
                SELECT id, password_hash, is_active, deleted_at, email_verified
                FROM users
                WHERE lower(username) = lower(?) OR lower(email) = lower(?)
            ''', (identifier, normalized_email))
            result = cursor.fetchone()
            if not result:
                return {'success': False, 'message': 'اسم المستخدم أو البريد الإلكتروني أو كلمة المرور غير صحيحة'}
            user_id, password_hash, is_active, deleted_at, email_verified = result
            if deleted_at:
                conn.close()
                return {'success': False, 'message': 'الحساب محذوف بواسطة الإدارة'}
            if not email_verified:
                conn.close()
                return {'success': False, 'message': 'الحساب غير مفعل بعد. افتح رابط التفعيل المرسل إلى بريدك الإلكتروني.'}
            if not is_active:
                conn.close()
                return {'success': False, 'message': 'الحساب غير مفعل'}
            if not self.verify_password(password_hash, password):
                conn.close()
                return {'success': False, 'message': 'اسم المستخدم أو البريد الإلكتروني أو كلمة المرور غير صحيحة'}
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
                                WHERE us.session_token = ?
                                    AND us.expires_at > CURRENT_TIMESTAMP
                                    AND u.is_active = 1
                                    AND (u.deleted_at IS NULL OR u.deleted_at = '')
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
                  SELECT id, username, email, full_name, plan, created_at, last_login, is_active, is_admin,
                      phone, country, nickname, email_verified, marketing_email_opt_in, whatsapp_opt_in,
                      activation_sent_at, activated_at
                FROM users
                WHERE id = ? AND (deleted_at IS NULL OR deleted_at = '')
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
                    'is_admin': bool(result[8]),
                    'phone': result[9],
                    'country': result[10],
                    'nickname': result[11],
                    'email_verified': bool(result[12]),
                    'marketing_email_opt_in': bool(result[13]),
                    'whatsapp_opt_in': bool(result[14]),
                    'activation_sent_at': result[15],
                    'activated_at': result[16]
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
            cursor.execute(
                '''
                UPDATE users
                SET is_admin = ?
                WHERE id = ? AND (deleted_at IS NULL OR deleted_at = '')
                ''',
                (1 if is_admin else 0, user_id)
            )
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
            cursor.execute(
                '''
                UPDATE users
                SET is_active = ?
                WHERE id = ? AND (deleted_at IS NULL OR deleted_at = '')
                ''',
                (1 if is_active else 0, user_id)
            )
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
                FROM users
                WHERE (deleted_at IS NULL OR deleted_at = '')
                ORDER BY id DESC
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

    def list_contactable_users(self, verified_only=True, marketing_only=True):
        """إرجاع قائمة العملاء مع قنوات التواصل المتاحة للإدارة."""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            where_parts = ["(deleted_at IS NULL OR deleted_at = '')"]
            if verified_only:
                where_parts.append('email_verified = 1')
            query = f'''
                SELECT id, username, email, full_name, phone, country, nickname,
                       email_verified, marketing_email_opt_in, whatsapp_opt_in,
                       created_at, activated_at, last_login, plan
                FROM users
                WHERE {' AND '.join(where_parts)}
                ORDER BY created_at DESC
            '''
            cursor.execute(query)
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                row_dict['email_verified'] = bool(row_dict.get('email_verified'))
                row_dict['marketing_email_opt_in'] = bool(row_dict.get('marketing_email_opt_in'))
                row_dict['whatsapp_opt_in'] = bool(row_dict.get('whatsapp_opt_in'))
                if marketing_only and not row_dict['marketing_email_opt_in'] and not row_dict['whatsapp_opt_in']:
                    continue
                rows.append(row_dict)
            conn.close()
            return rows
        except Exception:
            return []

    def list_pending_activation_users(self, older_than_hours=0):
        """إرجاع الحسابات غير المفعلة مع دعم فلترة المتأخرين في التفعيل."""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            where_parts = ["(deleted_at IS NULL OR deleted_at = '')", "COALESCE(email_verified, 0) = 0"]
            params = []
            if int(older_than_hours or 0) > 0:
                where_parts.append("created_at <= datetime('now', ?)")
                params.append(f"-{int(older_than_hours)} hours")

            cursor.execute(
                f'''
                SELECT id, username, email, full_name, phone, created_at,
                       activation_sent_at, marketing_email_opt_in, whatsapp_opt_in,
                       is_active
                FROM users
                WHERE {' AND '.join(where_parts)}
                ORDER BY created_at ASC
                ''',
                tuple(params)
            )
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                row_dict['marketing_email_opt_in'] = bool(row_dict.get('marketing_email_opt_in'))
                row_dict['whatsapp_opt_in'] = bool(row_dict.get('whatsapp_opt_in'))
                row_dict['is_active'] = bool(row_dict.get('is_active'))
                rows.append(row_dict)
            conn.close()
            return rows
        except Exception:
            return []

    def soft_delete_user(self, user_id, admin_username='system', reason=''):
        """حذف منطقي للمستخدم مع الاحتفاظ الكامل بالسجل لأغراض التدقيق والاستعادة."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                '''
                UPDATE users
                SET is_active = 0,
                    deleted_at = CURRENT_TIMESTAMP,
                    deleted_by = ?,
                    delete_reason = ?
                WHERE id = ? AND (deleted_at IS NULL OR deleted_at = '')
                ''',
                (str(admin_username or 'system'), str(reason or ''), user_id)
            )
            changed = int(cursor.rowcount or 0)
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            if changed > 0:
                self.log_activity(user_id, 'soft_delete', f'by={admin_username}; reason={reason}')
            return {'success': changed > 0, 'affected': changed}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def restore_user(self, user_id, admin_username='system'):
        """استعادة مستخدم محذوف من الإدارة."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                '''
                UPDATE users
                SET is_active = 1,
                    deleted_at = NULL,
                    deleted_by = NULL,
                    delete_reason = NULL
                WHERE id = ?
                ''',
                (user_id,)
            )
            changed = int(cursor.rowcount or 0)
            conn.commit()
            conn.close()
            if changed > 0:
                self.log_activity(user_id, 'restore_user', f'by={admin_username}')
            return {'success': changed > 0, 'affected': changed}
        except Exception as e:
            return {'success': False, 'message': str(e)}

# إنشاء مثيل عام
user_manager = UserManager()

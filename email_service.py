"""
نظام إرسال الإيميلات للإشعارات
Email Notification Service
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import os
from pathlib import Path

SUPPORT_EMAIL = "mahmoodalqaise750@gmail.com"


def _read_int_env(name, default):
    """قراءة متغير بيئة عددي مع fallback آمن عند وجود قيمة غير صالحة."""
    raw_value = os.environ.get(name, str(default))
    try:
        return int(str(raw_value).strip())
    except Exception:
        print(f"[WARN] Invalid integer for {name}: {raw_value!r}. Falling back to {default}.")
        return int(default)

class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com').strip()
        self.smtp_port = _read_int_env('SMTP_PORT', 587)
        self.smtp_user = os.environ.get('SMTP_USER', '').strip()
        self.smtp_password = os.environ.get('SMTP_PASS', '').strip()
        self.smtp_enabled = os.environ.get('SMTP_ENABLED', '1').strip().lower() in ('1', 'true', 'yes', 'on')
        self.default_sender = os.environ.get('SMTP_FROM_EMAIL', self.smtp_user or SUPPORT_EMAIL).strip()
        self.smtp_timeout_seconds = _read_int_env('SMTP_TIMEOUT_SECONDS', 20)
        self.last_delivery_status = {
            'ok': False,
            'category': 'not_attempted',
            'message': 'لم تتم أي محاولة إرسال بعد.',
            'updated_at': None
        }
        self.public_base_url = (
            os.environ.get('PUBLIC_BASE_URL')
            or os.environ.get('SITE_BASE_URL')
            or os.environ.get('RENDER_EXTERNAL_URL')
            or 'http://localhost:5000'
        ).rstrip('/')

    def can_send_email(self):
        """التحقق من جاهزية إعدادات SMTP."""
        return bool(self.smtp_enabled and self.smtp_server and self.smtp_user and self.smtp_password)

    def _update_last_delivery_status(self, ok, category, message):
        self.last_delivery_status = {
            'ok': bool(ok),
            'category': str(category or 'unknown'),
            'message': str(message or ''),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _classify_email_error(self, error_text):
        text = str(error_text or '').strip()
        lower = text.lower()
        if not self.smtp_enabled:
            return 'smtp_disabled'
        if not self.smtp_user or not self.smtp_password:
            return 'missing_credentials'
        if 'authentication' in lower or 'username and password not accepted' in lower or '535' in lower:
            return 'auth_failed'
        if 'timed out' in lower or 'timeout' in lower:
            return 'smtp_timeout'
        if 'name or service not known' in lower or 'nodename nor servname provided' in lower or 'getaddrinfo failed' in lower:
            return 'smtp_host_unreachable'
        if 'connection unexpectedly closed' in lower or 'connection reset' in lower or 'server disconnected' in lower:
            return 'smtp_connection_failed'
        if '5.7.1' in lower or 'sender address rejected' in lower or 'not allowed' in lower:
            return 'sender_rejected'
        if 'recipient address rejected' in lower or 'user unknown' in lower or 'mailbox unavailable' in lower:
            return 'recipient_rejected'
        return 'send_failed'

    def get_smtp_status(self):
        missing = []
        if not self.smtp_enabled:
            missing.append('SMTP_ENABLED=0')
        if not self.smtp_server:
            missing.append('SMTP_SERVER')
        if not self.smtp_user:
            missing.append('SMTP_USER')
        if not self.smtp_password:
            missing.append('SMTP_PASS')

        return {
            'enabled': bool(self.smtp_enabled),
            'ready': self.can_send_email(),
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'default_sender': self.default_sender,
            'public_base_url': self.public_base_url,
            'missing': missing,
            'last_delivery_status': dict(self.last_delivery_status),
        }

    def build_public_url(self, path):
        """إنشاء رابط عام صالح للإرسال داخل البريد الإلكتروني."""
        normalized = '/' + str(path or '').lstrip('/')
        return f"{self.public_base_url}{normalized}"
    
    def send_subscription_request(self, user_data, plan_data, payment_info=None):
        """إرسال طلب اشتراك جديد مع معلومات الدفع"""
        if payment_info is None:
            payment_info = {}
        
        location = payment_info.get('location', 'unknown')
        payment_method = payment_info.get('payment_method', 'unknown')
        transaction_id = payment_info.get('transaction_id', '')
        
        # تحديد نص طريقة الدفع
        payment_methods = {
            'cliq': 'CliQ (كليك)',
            'bank_transfer': 'حوالة بنكية / IBAN',
            'visa': 'بطاقة فيزا/ماستركارد',
            'crypto': 'عملات رقمية (Cryptocurrency)'
        }
        payment_method_text = payment_methods.get(payment_method, payment_method)
        
        location_text = 'داخل الأردن' if location == 'jordan' else 'خارج الأردن (دولي)'
        
        subject = f"طلب اشتراك جديد - {plan_data['name']} - {payment_method_text}"
        
        body = f"""
        طلب اشتراك جديد في Gold Analyzer VIP System
        ============================================
        
        تفاصيل المستخدم:
        - الاسم الكامل: {user_data.get('full_name', 'غير محدد')}
        - اسم المستخدم: {user_data.get('username')}
        - البريد الإلكتروني: {user_data.get('email')}
        - رقم المستخدم: {user_data.get('user_id')}
        
        تفاصيل الخطة:
        - اسم الخطة: {plan_data['name']}
        - السعر: ${plan_data['price']}
        - المدة: {plan_data['duration_days']} يوم
        - عدد الإشارات اليومية: {plan_data['signals_per_day']}
        
        معلومات الدفع:
        - الموقع الجغرافي: {location_text}
        - طريقة الدفع: {payment_method_text}
        - رقم العملية/المرجع: {transaction_id if transaction_id else 'لم يتم الإدخال'}
        
        تاريخ الطلب: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        ============================================
        
        الإجراء المطلوب:
        1. التحقق من استلام الدفع ({payment_method_text})
        2. تسجيل الدخول إلى لوحة الأدمن: http://localhost:5000/admin
        3. الانتقال إلى تبويب "طلبات الاشتراك"
        4. تفعيل الاشتراك بعد التأكد من الدفع
        
        ملاحظة: هذا الطلب في انتظار التفعيل من قبل الأدمن.
        """
        
        # حفظ الطلب في قاعدة البيانات
        self.save_pending_request(user_data, plan_data, payment_info)
        
        # محاولة إرسال الإيميل إذا كان SMTP مفعل
        if self.can_send_email():
            try:
                self._send_email(SUPPORT_EMAIL, subject, body)
                return True, "تم إرسال الطلب بنجاح"
            except Exception as e:
                print(f"خطأ في إرسال الإيميل: {e}")
                return True, "تم حفظ الطلب، سيتم مراجعته قريباً"
        
        return True, "تم حفظ طلبك، سيتم التواصل معك بعد التحقق من الدفع"
    
    def save_pending_request(self, user_data, plan_data, payment_info=None):
        """حفظ الطلب المعلق مع معلومات الدفع"""
        if payment_info is None:
            payment_info = {}
        
        try:
            import sqlite3
            from pathlib import Path
            
            default_data_dir = Path('/var/data') if Path('/var/data').exists() else Path(__file__).parent
            data_dir = Path(os.environ.get('GOLDPRO_DATA_DIR', str(default_data_dir)))
            db_path = Path(os.environ.get('USERS_DB_PATH', str(data_dir / 'users.db')))
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # إنشاء جدول الطلبات إذا لم يكن موجود
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    email TEXT,
                    full_name TEXT,
                    plan TEXT NOT NULL,
                    price REAL NOT NULL,
                    duration_days INTEGER,
                    location TEXT,
                    payment_method TEXT,
                    transaction_id TEXT,
                    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    payment_proof TEXT,
                    admin_notes TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # إضافة الطلب
            cursor.execute('''
                INSERT INTO subscription_requests 
                (user_id, username, email, full_name, plan, price, duration_days, 
                 location, payment_method, transaction_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (
                user_data.get('user_id'),
                user_data.get('username'),
                user_data.get('email'),
                user_data.get('full_name'),
                plan_data['plan'],
                plan_data['price'],
                plan_data['duration_days'],
                payment_info.get('location', ''),
                payment_info.get('payment_method', ''),
                payment_info.get('transaction_id', '')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"خطأ في حفظ الطلب: {e}")
            return False
    
    def _send_email(self, to_email, subject, body):
        """إرسال الإيميل عبر SMTP"""
        if not self.can_send_email():
            raise Exception("SMTP credentials not configured")
        
        msg = MIMEMultipart()
        msg['From'] = self.default_sender
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.smtp_timeout_seconds)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self.smtp_user, self.smtp_password)
        text = msg.as_string()
        server.sendmail(self.default_sender, to_email, text)
        server.quit()

    def send_account_activation(self, user_email, full_name, activation_link):
        """إرسال رابط تفعيل الحساب بعد التسجيل."""
        subject = 'تفعيل حسابك في GOLD PRO'
        display_name = full_name or 'عميل GOLD PRO'
        body = f"""
مرحباً {display_name},

شكراً لتسجيلك في GOLD PRO.

لتفعيل حسابك والبدء باستخدام الموقع، افتح الرابط التالي:
{activation_link}

إذا لم تقم بإنشاء هذا الحساب، تجاهل هذه الرسالة.

فريق GOLD PRO
"""
        if not self.can_send_email():
            message = 'SMTP غير مهيأ بعد. اضبط SMTP_SERVER وSMTP_PORT وSMTP_USER وSMTP_PASS.'
            self._update_last_delivery_status(False, 'missing_credentials', message)
            return False, message
        try:
            self._send_email(user_email, subject, body)
            self._update_last_delivery_status(True, 'sent', f'تم إرسال بريد التفعيل إلى {user_email}')
            return True, 'تم إرسال رابط التفعيل بنجاح.'
        except Exception as e:
            error_text = str(e)
            self._update_last_delivery_status(False, self._classify_email_error(error_text), error_text)
            return False, error_text

    def send_welcome_email(self, user_email, full_name):
        """إرسال رسالة ترحيب بعد تفعيل الحساب بنجاح."""
        display_name = full_name or 'عميل GOLD PRO'
        subject = 'مرحباً بك في GOLD PRO'
        login_link = self.build_public_url('/login?first=1')
        plans_link = self.build_public_url('/plans')
        body = f"""
مرحباً {display_name},

تم تفعيل حسابك بنجاح وأصبح بإمكانك الآن تسجيل الدخول إلى GOLD PRO.

رابط تسجيل الدخول:
{login_link}

يمكنك مراجعة الخطط والخدمات من هنا:
{plans_link}

نحتفظ ببريدك للتحديثات المهمة، وإذا أضفت رقم هاتفك ووافقت على التواصل فسيبقى متاحاً لفريق الدعم عند الحاجة.

فريق GOLD PRO
"""
        if not self.can_send_email():
            message = 'SMTP غير مهيأ بعد.'
            self._update_last_delivery_status(False, 'missing_credentials', message)
            return False, message
        try:
            self._send_email(user_email, subject, body)
            self._update_last_delivery_status(True, 'sent', f'تم إرسال رسالة الترحيب إلى {user_email}')
            return True, 'تم إرسال رسالة الترحيب.'
        except Exception as e:
            error_text = str(e)
            self._update_last_delivery_status(False, self._classify_email_error(error_text), error_text)
            return False, error_text
    
    def send_activation_confirmation(self, user_email, plan_name, end_date):
        """إرسال تأكيد تفعيل الاشتراك"""
        subject = f"تم تفعيل اشتراكك في Gold Analyzer - {plan_name}"
        
        body = f"""
        مرحباً،
        
        تم تفعيل اشتراكك بنجاح في Gold Analyzer VIP System!
        
        تفاصيل الاشتراك:
        - الخطة: {plan_name}
        - ينتهي في: {end_date}
        
        يمكنك الآن الوصول إلى جميع ميزات الخطة الخاصة بك.
        
        رابط تسجيل الدخول: http://localhost:5000/login
        
        شكراً لاختيارك Gold Analyzer!
        """
        
        if self.can_send_email():
            try:
                self._send_email(user_email, subject, body)
            except:
                pass

    def send_admin_broadcast(self, recipients, subject, body):
        """إرسال رسالة جماعية من الإدارة إلى العملاء."""
        if not self.can_send_email():
            return {
                'success': False,
                'message': 'SMTP غير مهيأ للإرسال الجماعي.',
                'sent': 0,
                'failed': 0,
                'errors': [],
                'recipient_count': 0,
                'sent_emails': [],
                'failed_emails': []
            }

        sent = 0
        failed = 0
        errors = []
        sent_emails = []
        failed_emails = []
        unique_emails = []
        seen = set()
        for recipient in recipients or []:
            email = str((recipient or {}).get('email') or '').strip().lower()
            if not email or email in seen:
                continue
            seen.add(email)
            unique_emails.append(email)

        for email in unique_emails:
            try:
                self._send_email(email, subject, body)
                sent += 1
                sent_emails.append(email)
            except Exception as e:
                failed += 1
                failed_emails.append({'email': email, 'error': str(e)})
                if len(errors) < 20:
                    errors.append(f'{email}: {e}')

        return {
            'success': failed == 0,
            'message': f'تم إرسال {sent} رسالة وفشل {failed}.' if unique_emails else 'لا يوجد مستلمون صالحون للإرسال.',
            'sent': sent,
            'failed': failed,
            'errors': errors,
            'recipient_count': len(unique_emails),
            'sent_emails': sent_emails,
            'failed_emails': failed_emails
        }

# إنشاء مثيل عام
email_service = EmailService()

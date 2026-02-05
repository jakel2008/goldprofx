"""
نظام إرسال الإيميلات للإشعارات
Email Notification Service
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

SUPPORT_EMAIL = "mahmoodalqaise750@gmail.com"

class EmailService:
    def __init__(self):
        # يمكن تفعيل SMTP لاحقاً
        self.smtp_enabled = False
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_user = ""  # يمكن إضافة بريد إلكتروني للإرسال
        self.smtp_password = ""  # كلمة مرور التطبيق
    
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
        if self.smtp_enabled:
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
            
            db_path = Path(__file__).parent / 'users.db'
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
        if not self.smtp_user or not self.smtp_password:
            raise Exception("SMTP credentials not configured")
        
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        text = msg.as_string()
        server.sendmail(self.smtp_user, to_email, text)
        server.quit()
    
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
        
        if self.smtp_enabled:
            try:
                self._send_email(user_email, subject, body)
            except:
                pass

# إنشاء مثيل عام
email_service = EmailService()

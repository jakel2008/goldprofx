#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نظام إدارة الاشتراكات VIP
"""

import sqlite3
from datetime import datetime, timedelta
import hashlib
import os
import sys

# إصلاح مشكلة الترميز على Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

class SubscriptionManager:

    def get_user_by_username(self, username):
        """جلب بيانات مستخدم بالاسم وكلمة المرور"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT user_id, username, plan, subscription_start, subscription_end, 
                   status, referral_code, total_paid, password_hash
            FROM users 
            WHERE username = ?
        ''', (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'user_id': row[0],
            'username': row[1],
            'plan': row[2],
            'subscription_start': row[3],
            'subscription_end': row[4],
            'status': row[5],
            'referral_code': row[6],
            'total_paid': row[7],
            'password_hash': row[8] if len(row) > 8 else None
        }
    """إدارة الاشتراكات والمستخدمين"""
    
    PLANS = {
        'free': {'price': 0, 'duration_days': 0, 'signals_per_day': 1},
        'bronze': {'price': 29, 'duration_days': 30, 'signals_per_day': 3},
        'silver': {'price': 69, 'duration_days': 90, 'signals_per_day': 5},
        'gold': {'price': 199, 'duration_days': 365, 'signals_per_day': 7},
        'platinum': {'price': 499, 'duration_days': 365, 'signals_per_day': 10}
    }
    
    def __init__(self, db_path='vip_subscriptions.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # جدول المستخدمين
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                plan TEXT DEFAULT 'free',
                subscription_start TIMESTAMP,
                subscription_end TIMESTAMP,
                status TEXT DEFAULT 'active',
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_paid REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                password_hash TEXT,
                email TEXT,
                activation_token TEXT,
                FOREIGN KEY(referred_by) REFERENCES users(user_id)
            )
        ''')
        # إضافة الأعمدة الجديدة إذا لم تكن موجودة (للتوافق مع قواعد بيانات قديمة)
        try:
            c.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
        except Exception: pass
        try:
            c.execute('ALTER TABLE users ADD COLUMN email TEXT')
        except Exception: pass
        try:
            c.execute('ALTER TABLE users ADD COLUMN activation_token TEXT')
        except Exception: pass
        try:
            c.execute('ALTER TABLE users ADD COLUMN chat_id TEXT')
        except Exception: pass
        try:
            c.execute('ALTER TABLE users ADD COLUMN telegram_id INTEGER')
        except Exception: pass
        
        # جدول المدفوعات
        c.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                plan TEXT,
                payment_method TEXT,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transaction_id TEXT UNIQUE,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول الإحالات
        c.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_user_id INTEGER,
                referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                reward_given INTEGER DEFAULT 0,
                FOREIGN KEY(referrer_id) REFERENCES users(user_id),
                FOREIGN KEY(referred_user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول التوصيات المُرسلة
        c.execute('''
            CREATE TABLE IF NOT EXISTS signals_sent (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                signal_data TEXT,
                quality TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("[OK] Database created successfully")
    
    def generate_referral_code(self, user_id):
        """توليد كود إحالة فريد"""
        hash_input = f"{user_id}{datetime.now().isoformat()}"
        code = hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()
        return f"REF{code}"
    
    def add_user(self, user_id, username, first_name="", referred_by_code=None):
        """إضافة مستخدم جديد مع Trial 3 أيام"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # التحقق من وجود المستخدم
        c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if c.fetchone():
            conn.close()
            return False, "المستخدم موجود مسبقاً"
        
        # إنشاء كود إحالة
        referral_code = self.generate_referral_code(user_id)
        
        # Trial لمدة 3 أيام
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=3)
        
        # التحقق من كود الإحالة
        referred_by_id = None
        if referred_by_code:
            c.execute('SELECT user_id FROM users WHERE referral_code = ?', 
                     (referred_by_code,))
            result = c.fetchone()
            if result:
                referred_by_id = result[0]
        
        c.execute('''
            INSERT INTO users 
            (user_id, username, first_name, plan, subscription_start, 
             subscription_end, status, referral_code, referred_by)
            VALUES (?, ?, ?, 'bronze', ?, ?, 'trial', ?, ?)
        ''', (user_id, username, first_name, trial_start, trial_end, 
              referral_code, referred_by_id))
        
        # تسجيل الإحالة
        if referred_by_id:
            c.execute('''
                INSERT INTO referrals (referrer_id, referred_user_id, status)
                VALUES (?, ?, 'pending')
            ''', (referred_by_id, user_id))
        
        conn.commit()
        conn.close()
        
        return True, f"تم التسجيل بنجاح! كود إحالتك: {referral_code}"
    
    def get_all_subscriptions(self):
        """الحصول على جميع المشتركين"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT user_id, username, first_name, plan, 
                   subscription_start, subscription_end, status, 
                   total_paid, created_at, referral_code
            FROM users
            ORDER BY created_at DESC
        ''')
        
        subscriptions = []
        for row in c.fetchall():
            subscriptions.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'plan': row[3],
                'subscription_start': row[4],
                'subscription_end': row[5],
                'status': row[6],
                'total_paid': row[7],
                'created_at': row[8],
                'referral_code': row[9]
            })
        
        conn.close()
        return subscriptions
    
    def update_subscription_plan(self, user_id, plan, duration_days=None):
        """تحديث خطة اشتراك المستخدم"""
        if plan not in self.PLANS:
            return False, "خطة غير صحيحة"
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # التحقق من وجود المستخدم
        c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not c.fetchone():
            conn.close()
            return False, "المستخدم غير موجود"
        
        # حساب مدة الاشتراك
        if duration_days is None:
            duration_days = self.PLANS[plan]['duration_days']
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days) if duration_days > 0 else None
        
        c.execute('''
            UPDATE users 
            SET plan = ?, subscription_start = ?, subscription_end = ?, status = 'active'
            WHERE user_id = ?
        ''', (plan, start_date, end_date, user_id))
        
        conn.commit()
        conn.close()
        return True, "تم تحديث الخطة بنجاح"
    
    def extend_subscription(self, user_id, days):
        """تمديد اشتراك المستخدم"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT subscription_end FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return False, "المستخدم غير موجود"
        
        current_end = result[0]
        if current_end:
            new_end = datetime.fromisoformat(current_end) + timedelta(days=days)
        else:
            new_end = datetime.now() + timedelta(days=days)
        
        c.execute('''
            UPDATE users 
            SET subscription_end = ?, status = 'active'
            WHERE user_id = ?
        ''', (new_end.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return True, f"تم تمديد الاشتراك لـ {days} يوم"
    
    def cancel_subscription(self, user_id):
        """إلغاء اشتراك المستخدم"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            UPDATE users 
            SET status = 'cancelled', subscription_end = ?
            WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return True, "تم إلغاء الاشتراك"
    
    def reactivate_subscription(self, user_id):
        """إعادة تفعيل اشتراك المستخدم"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT plan FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return False, "المستخدم غير موجود"
        
        plan = result[0]
        duration_days = self.PLANS.get(plan, {}).get('duration_days', 30)
        
        new_end = datetime.now() + timedelta(days=duration_days)
        
        c.execute('''
            UPDATE users 
            SET status = 'active', subscription_start = ?, subscription_end = ?
            WHERE user_id = ?
        ''', (datetime.now().isoformat(), new_end.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return True, "تم إعادة تفعيل الاشتراك"
    
    def check_subscription(self, user_id):
        """التحقق من حالة الاشتراك"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT plan, subscription_start, subscription_end, status, referral_code
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            return {
                'exists': False,
                'message': 'المستخدم غير موجود'
            }
        
        plan, start, end, status, ref_code = result
        
        # تحويل التواريخ
        if end:
            end_dt = datetime.fromisoformat(end)
            is_expired = datetime.now() > end_dt
            days_left = (end_dt - datetime.now()).days
        else:
            is_expired = False
            days_left = 0
        
        return {
            'exists': True,
            'plan': plan,
            'start_date': start,
            'end_date': end,
            'status': 'expired' if is_expired else status,
            'is_active': not is_expired and status in ['active', 'trial'],
            'days_left': max(0, days_left),
            'referral_code': ref_code,
            'plan_details': self.PLANS.get(plan, {})
        }
    
    def upgrade_user(self, user_id, plan, payment_method='manual', transaction_id=None):
        """ترقية المستخدم لباقة مدفوعة"""
        if plan not in self.PLANS:
            return False, "باقة غير صحيحة"
        
        plan_info = self.PLANS[plan]
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # الحصول على الاشتراك الحالي
        c.execute('SELECT subscription_end, status FROM users WHERE user_id = ?', 
                 (user_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return False, "المستخدم غير موجود"
        
        current_end, current_status = result
        
        # حساب تاريخ البدء والانتهاء
        start_date = datetime.now()
        
        # إذا كان الاشتراك الحالي لم ينتهِ، نبدأ من تاريخ الانتهاء
        if current_end:
            current_end_dt = datetime.fromisoformat(current_end)
            if current_end_dt > start_date:
                start_date = current_end_dt
        
        end_date = start_date + timedelta(days=plan_info['duration_days'])
        
        # تحديث المستخدم
        c.execute('''
            UPDATE users 
            SET plan = ?, 
                subscription_start = ?,
                subscription_end = ?,
                status = 'active',
                total_paid = total_paid + ?
            WHERE user_id = ?
        ''', (plan, start_date, end_date, plan_info['price'], user_id))
        
        # تسجيل الدفع
        c.execute('''
            INSERT INTO payments 
            (user_id, amount, plan, payment_method, transaction_id, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
        ''', (user_id, plan_info['price'], plan, payment_method, transaction_id))
        
        # مكافأة المُحيل إذا كان هذا أول اشتراك
        c.execute('''
            SELECT referred_by FROM users WHERE user_id = ?
        ''', (user_id,))
        referred_by = c.fetchone()
        
        if referred_by and referred_by[0]:
            # تحديث حالة الإحالة
            c.execute('''
                UPDATE referrals 
                SET status = 'completed', reward_given = 1
                WHERE referred_user_id = ? AND status = 'pending'
            ''', (user_id,))
            
            # منح المُحيل 5 أيام إضافية
            c.execute('''
                UPDATE users 
                SET subscription_end = DATETIME(subscription_end, '+5 days')
                WHERE user_id = ?
            ''', (referred_by[0],))
        
        conn.commit()
        conn.close()
        
        return True, f"تم الترقية للباقة {plan} بنجاح! صالحة حتى {end_date.strftime('%Y-%m-%d')}"
    
    def can_receive_signal(self, user_id, signal_quality='high'):
        """التحقق من إمكانية استقبال التوصية"""
        sub_info = self.check_subscription(user_id)
        
        if not sub_info['exists'] or not sub_info['is_active']:
            return False, "اشتراكك منتهي أو غير نشط"
        
        plan = sub_info['plan']
        
        # التحقق من عدد التوصيات اليومية
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        today = datetime.now().date()
        c.execute('''
            SELECT COUNT(*) FROM signals_sent 
            WHERE user_id = ? AND DATE(sent_at) = ?
        ''', (user_id, today))
        
        today_count = c.fetchone()[0]
        conn.close()
        
        max_signals = self.PLANS[plan]['signals_per_day']
        
        if today_count >= max_signals:
            return False, f"وصلت للحد الأقصى اليومي ({max_signals} توصيات)"
        
        # فلترة حسب جودة التوصية
        if signal_quality == 'high':
            # جميع الباقات تستقبل high quality
            return True, "يمكن الاستقبال"
        elif signal_quality == 'medium':
            # Bronze فما فوق
            if plan in ['bronze', 'silver', 'gold', 'platinum']:
                return True, "يمكن الاستقبال"
            return False, "هذه التوصية للأعضاء البرونز فما فوق"
        else:
            # low quality للجميع (لكن ليس مفيداً)
            return True, "يمكن الاستقبال"
    
    def log_signal_sent(self, user_id, signal_data, quality):
        """تسجيل التوصية المُرسلة"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO signals_sent (user_id, signal_data, quality)
            VALUES (?, ?, ?)
        ''', (user_id, str(signal_data), quality))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id):
        """إحصائيات المستخدم"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # إجمالي المدفوع
        c.execute('SELECT total_paid FROM users WHERE user_id = ?', (user_id,))
        total_paid = c.fetchone()[0] or 0
        
        # عدد التوصيات المُستلمة
        c.execute('SELECT COUNT(*) FROM signals_sent WHERE user_id = ?', (user_id,))
        total_signals = c.fetchone()[0]
        
        # عدد الإحالات
        c.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
        referrals_count = c.fetchone()[0]
        
        # الإحالات الناجحة
        c.execute('''
            SELECT COUNT(*) FROM referrals 
            WHERE referrer_id = ? AND status = 'completed'
        ''', (user_id,))
        successful_referrals = c.fetchone()[0]
        
        conn.close()
        
        return {
            'total_paid': total_paid,
            'total_signals_received': total_signals,
            'referrals_count': referrals_count,
            'successful_referrals': successful_referrals,
            'bonus_days_earned': successful_referrals * 30
        }
    
    def get_all_active_users(self):
        """جلب جميع المستخدمين النشطين"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT user_id, plan, status, chat_id, telegram_id
            FROM users 
            WHERE status IN ('active', 'trial') 
            AND (subscription_end IS NULL OR subscription_end > ?)
        ''', (datetime.now(),))
        
        users = c.fetchall()
        conn.close()
        
        return [
            {
                'user_id': u[0],
                'plan': u[1],
                'status': u[2],
                'chat_id': u[3],
                'telegram_id': u[4]
            }
            for u in users
        ]
    
    def get_user(self, user_id):
        """جلب بيانات مستخدم"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT user_id, username, plan, subscription_start, subscription_end, 
                   status, referral_code, total_paid
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'user_id': row[0],
            'username': row[1],
            'plan': row[2],
            'subscription_start': row[3],
            'subscription_end': row[4],
            'status': row[5],
            'referral_code': row[6],
            'total_paid': row[7]
        }


# مثال على الاستخدام
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("="*80)
    print("🧪 اختبار نظام الاشتراكات VIP")
    print("="*80)
    print()
    
    # إنشاء instance
    manager = SubscriptionManager()
    
    # إضافة مستخدم تجريبي
    test_user_id = 123456789
    success, message = manager.add_user(test_user_id, "test_user", "Test User")
    print(f"1️⃣ إضافة مستخدم: {message}")
    print()
    
    # التحقق من الاشتراك
    sub_info = manager.check_subscription(test_user_id)
    print(f"2️⃣ حالة الاشتراك:")
    print(f"   الباقة: {sub_info['plan']}")
    print(f"   الحالة: {sub_info['status']}")
    print(f"   أيام متبقية: {sub_info['days_left']}")
    print(f"   كود الإحالة: {sub_info['referral_code']}")
    print()
    
    # ترقية للباقة الذهبية
    success, message = manager.upgrade_user(test_user_id, 'gold', 'test_payment')
    print(f"3️⃣ الترقية: {message}")
    print()
    
    # التحقق من إمكانية استقبال توصية
    can_receive, msg = manager.can_receive_signal(test_user_id, 'high')
    print(f"4️⃣ استقبال توصية: {msg}")
    print()
    
    # إحصائيات
    stats = manager.get_user_stats(test_user_id)
    print(f"5️⃣ الإحصائيات:")
    print(f"   إجمالي المدفوع: ${stats['total_paid']}")
    print(f"   التوصيات المستلمة: {stats['total_signals_received']}")
    print(f"   الإحالات: {stats['referrals_count']}")
    print()
    
    print("="*80)
    print("✅ اكتمل الاختبار!")
    print("="*80)

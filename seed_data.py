# GOLD PRO - Seed Default Data
# إضافة البيانات الافتراضية (الخطط والمستخدمين التجريبيين)

import sqlite3
import hashlib

DB_PATH = 'goldpro_system.db'

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # إضافة الخطط
    plans = [
        ('free', 'الخطة المجانية - 1 إشارة يومياً', 0, 'إشارة واحدة يومية', 1),
        ('bronze', 'خطة البرونز - 5 إشارات يومياً', 29.99, 'إشارات متعددة يومياً', 1),
        ('silver', 'خطة الفضة - 15 إشارة يومياً', 79.99, 'إشارات متقدمة + دعم فني', 1),
        ('gold', 'خطة الذهب - 30 إشارة يومياً + مشاركات VIP', 199.99, 'إشارات حصرية + مجموعة VIP', 1),
        ('platinum', 'خطة البلاتينيوم - إشارات غير محدودة + استشارات', 299.99, 'كل شيء + استشارات شخصية', 1),
    ]
    
    for plan in plans:
        try:
            c.execute('INSERT INTO plans (name, description, price, features, is_active) VALUES (?, ?, ?, ?, ?)', plan)
        except sqlite3.IntegrityError:
            # الخطة موجودة بالفعل
            pass
    
    # إضافة مستخدم تجريبي (البريد: test@goldpro.com، كلمة المرور: Test123)
    test_email = 'test@goldpro.com'
    test_password = hashlib.sha256('Test123'.encode()).hexdigest()
    
    try:
        c.execute('''
            INSERT INTO users (email, password_hash, full_name, plan_id, is_active, activation_code, join_date)
            VALUES (?, ?, ?, 1, 1, NULL, datetime('now'))
        ''', (test_email, test_password, 'Test User'))
    except sqlite3.IntegrityError:
        # المستخدم موجود بالفعل
        print('Test user already exists.')
    
    conn.commit()
    conn.close()
    print('✅ تم إضافة البيانات الافتراضية بنجاح')
    print('📧 بريد تجريبي: test@goldpro.com')
    print('🔐 كلمة مرور: Test123')

if __name__ == '__main__':
    seed_data()

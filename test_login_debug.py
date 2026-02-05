import requests
import hashlib

# اختبار تسجيل الدخول بشكل مفصل
BASE_URL = 'http://127.0.0.1:5000'

# 1. التححقق من أن المستخدم موجود في قاعدة البيانات
import sqlite3
conn = sqlite3.connect('goldpro_system.db')
c = conn.cursor()
c.execute('SELECT email, password_hash FROM users WHERE email = ?', ('test@goldpro.com',))
user = c.fetchone()
if user:
    print(f"✅ المستخدم موجود: {user[0]}")
    # التحقق من كلمة المرور
    test_pass_hash = hashlib.sha256('Test123'.encode()).hexdigest()
    print(f"Password hash from DB: {user[1]}")
    print(f"Password hash from input: {test_pass_hash}")
    print(f"Passwords match: {user[1] == test_pass_hash}")
else:
    print("❌ المستخدم غير موجود")
conn.close()

# 2. محاولة الدخول
print("\n🔐 محاولة تسجيل الدخول...")
session = requests.Session()
login_response = session.post(f'{BASE_URL}/login', data={
    'email': 'test@goldpro.com',
    'password': 'Test123'
}, allow_redirects=False)

print(f"Login Status: {login_response.status_code}")
print(f"Login Headers: {dict(login_response.headers)}")
if 'Location' in login_response.headers:
    print(f"Redirect Location: {login_response.headers['Location']}")
else:
    print(f"No redirect - Response text (first 500): {login_response.text[:500]}")

# 3. التحقق من الكوكيز والجلسة
print(f"\nSession Cookies: {session.cookies.get_dict()}")

# 4. محاولة الوصول إلى dashboard
print("\n📊 محاولة الوصول إلى dashboard...")
dashboard_response = session.get(f'{BASE_URL}/dashboard')
print(f"Dashboard Status: {dashboard_response.status_code}")
if dashboard_response.status_code == 200:
    print("✅ تم الوصول إلى dashboard")
else:
    print(f"❌ فشل الوصول: {dashboard_response.status_code}")

import requests
import json

# اختبار تسجيل الدخول
BASE_URL = 'http://127.0.0.1:5000'

# 1. محاولة الدخول برقم البريد والكلمة المرور الصحيحة
print("🔐 اختبار تسجيل الدخول...")
session = requests.Session()
login_response = session.post(f'{BASE_URL}/login', data={
    'email': 'test@goldpro.com',
    'password': 'Test123'
}, allow_redirects=True)
print(f"Login Status: {login_response.status_code}")
print(f"Login URL: {login_response.url}")

# محاولة الوصول إلى dashboard
print("\n📊 اختبار الوصول إلى dashboard...")
dashboard_response = session.get(f'{BASE_URL}/dashboard')
print(f"Dashboard Status: {dashboard_response.status_code}")
if dashboard_response.status_code == 200:
    print("✅ تم الدخول بنجاح!")
    print(f"Dashboard Content (first 300 chars): {dashboard_response.text[:300]}")
else:
    print(f"❌ خطأ في الدخول: {dashboard_response.status_code}")
    print(f"Response: {dashboard_response.text[:300]}")

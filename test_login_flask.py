from web_app import app, get_user_by_email, check_password, get_plan_by_id
import hashlib
from flask import session

# اختبار الدخول باستخدام Flask test client
with app.test_client() as client:
    # اختبار POST للدخول
    print("🔐 اختبار الدخول عبر Flask client...")
    response = client.post('/login', data={
        'email': 'test@goldpro.com',
        'password': 'Test123'
    }, follow_redirects=True)
    
    print(f"Status: {response.status_code}")
    print(f"Response URL: {response.url if hasattr(response, 'url') else 'N/A'}")
    print(f"Response text (first 300): {response.data[:300].decode('utf-8', errors='ignore')}")
    
    # تحقق من جلسة اختبار
    print("\n📊 اختبار الوصول إلى dashboard...")
    dash_response = client.get('/dashboard', follow_redirects=True)
    print(f"Dashboard Status: {dash_response.status_code}")
    if dash_response.status_code == 200:
        print("✅ تم الوصول إلى dashboard")
    else:
        print(f"❌ فشل الوصول")

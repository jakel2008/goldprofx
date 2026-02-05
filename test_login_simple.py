#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

print("╔═══════════════════════════════════════════════╗")
print("║   اختبار تسجيل الدخول                      ║")
print("╚═══════════════════════════════════════════════╝\n")

url = 'http://localhost:5000/login'
data = {
    'email': 'test@goldpro.com',
    'password': 'Test123'
}

print(f"الرابط: {url}")
print(f"البريد: {data['email']}")
print(f"الكلمة: {data['password']}\n")

try:
    response = requests.post(url, data=data)
    print(f"✅ الطلب نجح")
    print(f"   رمز الحالة: {response.status_code}")
    print(f"   الرابط النهائي: {response.url}")
    print(f"   طول الصفحة: {len(response.text)} حرف")
    
    if "dashboard" in response.text.lower() or "لوحة" in response.text:
        print(f"   ✅ تم العثور على لوحة التحكم في الصفحة!")
    else:
        print(f"   📝 الصفحة: {response.text[:200]}...")
        
except Exception as e:
    print(f"❌ خطأ: {e}")

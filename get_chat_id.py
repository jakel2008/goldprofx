"""
الحصول على Chat ID الخاص بك
"""

import requests
import json

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"

print("=" * 60)
print("🔍 الحصول على Chat ID الخاص بك")
print("=" * 60)
print("\n📌 تعليمات:")
print("1. افتح البوت في تيليجرام")
print("2. أرسل أي رسالة للبوت (مثل: مرحبا)")
print("3. ثم عد هنا واضغط Enter")
print("\n" + "=" * 60)
input("\nهل أرسلت رسالة للبوت؟ اضغط Enter بعد الإرسال...")

print("\n🔄 جاري البحث عن Chat ID...")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

try:
    response = requests.get(url, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        updates = result.get('result', [])
        
        if not updates:
            print("\n❌ لم يتم العثور على رسائل")
            print("\n💡 تأكد من:")
            print("   1. أرسلت رسالة للبوت")
            print("   2. البوت الصحيح (تحقق من التوكن)")
            print("\n🔗 أو استخدم @userinfobot للحصول على Chat ID")
        else:
            print(f"\n✅ تم العثور على {len(updates)} رسالة")
            print("\n" + "=" * 60)
            print("📋 Chat IDs المتاحة:")
            print("=" * 60)
            
            seen_ids = set()
            for update in updates:
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    first_name = update['message']['chat'].get('first_name', 'N/A')
                    username = update['message']['chat'].get('username', 'N/A')
                    
                    if chat_id not in seen_ids:
                        seen_ids.add(chat_id)
                        print(f"\n📍 Chat ID: {chat_id}")
                        print(f"   الاسم: {first_name}")
                        print(f"   Username: @{username}")
                        print(f"\n   استخدم هذا الرقم في: MM_TELEGRAM_CHAT_ID={chat_id}")
            
            print("\n" + "=" * 60)
            print("\n✅ انسخ Chat ID وضعه في إعدادات البوت")
    else:
        print(f"\n❌ خطأ: {result.get('description')}")
        
except Exception as e:
    print(f"\n❌ خطأ في الاتصال: {e}")

print("\n" + "=" * 60)
input("\nاضغط Enter للإغلاق...")

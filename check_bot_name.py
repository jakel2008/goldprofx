"""
معرفة اسم البوت من التوكن
"""

import requests

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"

print("=" * 60)
print("🔍 التحقق من معلومات البوت")
print("=" * 60)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

try:
    response = requests.get(url, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        bot_info = result['result']
        
        print(f"\n✅ معلومات البوت:")
        print(f"   الاسم: {bot_info.get('first_name')}")
        print(f"   Username: @{bot_info.get('username')}")
        print(f"   ID: {bot_info.get('id')}")
        
        print(f"\n🔗 رابط البوت:")
        print(f"   https://t.me/{bot_info.get('username')}")
        
        print(f"\n💡 يجب أن تفتح هذا البوت في تيليجرام!")
        print(f"\n⚠️ إذا كنت تستخدم بوت آخر، لن تصلك الرسائل!")
        
    else:
        print(f"\n❌ خطأ: {result.get('description')}")
        
except Exception as e:
    print(f"\n❌ خطأ في الاتصال: {e}")

print("\n" + "=" * 60)
input("\nاضغط Enter للإغلاق...")

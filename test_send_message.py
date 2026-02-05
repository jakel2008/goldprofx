"""
اختبار سريع لإرسال رسالة تجريبية للبوت
"""

import requests
import os

# إعدادات البوت
BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
CHAT_ID = "7657829546"  # معرف الدردشة

def send_test_message():
    """إرسال رسالة تجريبية"""
    print("=" * 60)
    print("🧪 اختبار إرسال رسالة للبوت")
    print("=" * 60)
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    message = """
🧪 رسالة اختبار من نظام بث الإشارات

✅ إذا وصلتك هذه الرسالة، البوت يعمل بشكل صحيح!

🕐 الوقت: """ + requests.utils.quote(str(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    print(f"\n📤 جاري الإرسال إلى Chat ID: {CHAT_ID}")
    print(f"🔑 Token: {BOT_TOKEN[:20]}...")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        print(f"\n📊 النتيجة:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {result}")
        
        if result.get('ok'):
            print(f"\n✅ تم الإرسال بنجاح!")
            print(f"   Message ID: {result['result']['message_id']}")
            return True
        else:
            print(f"\n❌ فشل الإرسال!")
            print(f"   الخطأ: {result.get('description', 'Unknown error')}")
            
            if 'chat not found' in str(result.get('description', '')).lower():
                print("\n💡 الحل:")
                print("   1. افتح البوت في تيليجرام")
                print("   2. أرسل /start")
                print("   3. حاول مرة أخرى")
            
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ انتهت مهلة الاتصال")
        print("💡 تحقق من الاتصال بالإنترنت")
        return False
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        return False


def check_bot_info():
    """التحقق من معلومات البوت"""
    print("\n" + "=" * 60)
    print("🔍 التحقق من معلومات البوت")
    print("=" * 60)
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result['result']
            print(f"\n✅ البوت متصل!")
            print(f"   الاسم: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
            print(f"   ID: {bot_info.get('id')}")
            return True
        else:
            print(f"\n❌ فشل الاتصال بالبوت")
            print(f"   الخطأ: {result.get('description')}")
            return False
    except Exception as e:
        print(f"\n❌ خطأ في الاتصال: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    
    # 1. التحقق من معلومات البوت
    bot_ok = check_bot_info()
    
    if not bot_ok:
        print("\n⚠️ البوت غير متصل! تحقق من التوكن")
        input("\nاضغط Enter للإغلاق...")
        exit(1)
    
    # 2. إرسال رسالة تجريبية
    success = send_test_message()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 الاختبار نجح!")
        print("=" * 60)
        print("\n✅ البوت يعمل بشكل صحيح")
        print("✅ يمكنك الآن تشغيل النظام الكامل")
        print("\n💡 الخطوة التالية:")
        print("   نقر مزدوج على: START_ALL_SYSTEMS.bat")
    else:
        print("\n" + "=" * 60)
        print("❌ الاختبار فشل")
        print("=" * 60)
        print("\n⚠️ راجع الأخطاء أعلاه")
    
    print("\n" + "=" * 60)
    input("\nاضغط Enter للإغلاق...")

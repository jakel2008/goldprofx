import requests
import json

# إعدادات البوت
TELEGRAM_BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
TELEGRAM_CHAT_ID = "7657829546"

def send_test_message():
    """إرسال رسالة اختبار إلى بوت تلجرام"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # رسالة اختبار
    test_message = """🧪 *رسالة اختبار - نظام التوصيات التلقائي*

✅ البوت يعمل بنجاح!

📊 البيانات:
- التطبيق: Money Maker Analyzer
- الحالة: جاهز للعمل
- التاريخ: 2026-01-23

🔗 جاهز لاستقبال التوصيات التلقائية
"""
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": test_message,
        "parse_mode": "Markdown"
    }
    
    try:
        print("⏳ جاري الإرسال إلى بوت تلجرام...")
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"📡 رمز الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ تم إرسال الرسالة بنجاح!")
                print(f"📱 معرف الرسالة: {result['result']['message_id']}")
                return True
            else:
                print(f"❌ فشل الإرسال: {result.get('description', 'خطأ غير معروف')}")
                return False
        else:
            print(f"❌ خطأ في الاتصال: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ خطأ: لا يمكن الاتصال بخادم تلجرام")
        return False
    except requests.exceptions.Timeout:
        print("❌ خطأ: انتهاء المهلة الزمنية")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 اختبار بوت تلجرام")
    print("=" * 50)
    print(f"🔐 التوكن: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"💬 Chat ID: {TELEGRAM_CHAT_ID}")
    print("=" * 50)
    
    success = send_test_message()
    
    print("=" * 50)
    if success:
        print("✅ الاختبار نجح!")
    else:
        print("❌ الاختبار فشل - تحقق من التوكن ومعرف الدردشة")
    print("=" * 50)

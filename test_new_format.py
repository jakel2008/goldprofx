# -*- coding: utf-8 -*-
"""
اختبار التنسيق الجديد للإشارات - إرسال إشارة تجريبية بالتنسيق الجديد
"""
import os
import requests
from datetime import datetime

# استيراد دالة التنسيق
from signal_formatter import format_signal_message

# إعدادات البوت
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
ADMIN_CHAT_ID = "7657829546"  # jakel2008

def send_telegram(text, chat_id):
    """إرسال رسالة تليجرام"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        response = requests.post(
            url,
            json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

# إنشاء إشارة تجريبية
print("📡 إرسال إشارة تجريبية بالتنسيق الجديد...")

# إشارة شراء EURUSD
signal_buy = format_signal_message(
    symbol="EURUSD",
    signal_type="buy",
    entry=1.18624,
    stop_loss=1.18324,
    take_profits=[1.19124, 1.19424, 1.19924],
    quality_score=95
)

print("\n" + "=" * 50)
print("إشارة شراء:")
print("=" * 50)
print(signal_buy)

if send_telegram(signal_buy, ADMIN_CHAT_ID):
    print("\n✅ تم إرسال إشارة الشراء بنجاح!")
else:
    print("\n❌ فشل إرسال إشارة الشراء")

# الانتظار قليلاً
import time
time.sleep(2)

# إشارة بيع GBPUSD
signal_sell = format_signal_message(
    symbol="GBPUSD",
    signal_type="sell",
    entry=1.36565,
    stop_loss=1.36865,
    take_profits=[1.36265, 1.35965, 1.35465],
    quality_score=88
)

print("\n" + "=" * 50)
print("إشارة بيع:")
print("=" * 50)
print(signal_sell)

if send_telegram(signal_sell, ADMIN_CHAT_ID):
    print("\n✅ تم إرسال إشارة البيع بنجاح!")
else:
    print("\n❌ فشل إرسال إشارة البيع")

print("\n🎉 اختبار التنسيق الجديد مكتمل!")

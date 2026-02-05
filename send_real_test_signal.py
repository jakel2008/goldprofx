#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إرسال إشارة اختبار مع Chat ID الحقيقي المكتشف
"""
import json
import requests
import os
import sys
from datetime import datetime

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# استخدام Chat ID من discovered_chat_ids.json
with open('discovered_chat_ids.json', 'r', encoding='utf-8') as f:
    chat_data = json.load(f)
    real_chat_id = list(chat_data.keys())[0]
    real_user = chat_data[real_chat_id]

print("\n" + "="*70)
print("🔔 إرسال إشارة اختبار حقيقية")
print("="*70)
print(f"\nالمستخدم: {real_user['first_name']} (@{real_user['username']})")
print(f"Chat ID: {real_chat_id}")

# إشارة اختبار
signal = {
    'pair': 'EURUSD',
    'signal': 'BUY',
    'entry': 1.0850,
    'stop_loss': 1.0820,
    'take_profit': 1.0900,
    'quality_score': 92,
    'timestamp': datetime.now().isoformat(),
}

message = f"""
🎯 <b>إشارة تداول جديدة - اختبار</b>

📊 الزوج: <b>{signal['pair']}</b>
🔔 الإشارة: <b>{signal['signal']}</b>
💰 نقطة الدخول: <b>{signal['entry']}</b>
🛑 وقف الخسارة: <b>{signal['stop_loss']}</b>
🎁 جني الأرباح: <b>{signal['take_profit']}</b>
⭐ جودة الإشارة: <b>{signal['quality_score']}%</b>
⏰ التوقيت: <b>{signal['timestamp']}</b>

<i>✅ نظام GOLD PRO يعمل بنجاح!</i>
"""

print("\n" + "-"*70)
print("📤 جاري الإرسال...")

try:
    response = requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": real_chat_id,
            "text": message,
            "parse_mode": "HTML"
        },
        timeout=10
    )
    
    if response.status_code == 200 and response.json().get('ok'):
        print("✅ تم الإرسال بنجاح!")
        print("\n" + "="*70)
        print("🎉 النظام يعمل بشكل صحيح!")
        print("="*70)
    else:
        print(f"❌ فشل - {response.status_code}")
        print(f"الخطأ: {response.json()}")
        
except Exception as e:
    print(f"❌ خطأ: {e}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إرسال إشارة عبر البوت
"""
import json
import os
import sys
import requests
from datetime import datetime

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_test_signal():
    """إرسال إشارة اختبار"""
    
    print("🔔 اختبار إرسال إشارة عبر Telegram Bot")
    print("="*60)
    
    # Chat IDs للاختبار
    test_chat_ids = [
        "123456789",
        "987654321", 
        "555555555"
    ]
    
    # إشارة اختبار
    signal = {
        'pair': 'EURUSD',
        'signal': 'BUY',
        'entry': 1.0850,
        'stop_loss': 1.0820,
        'take_profit': 1.0900,
        'quality_score': 92,
        'timestamp': datetime.now().isoformat(),
        'reason': 'اختبار النظام'
    }
    
    message = f"""
🎯 <b>إشارة تداول جديدة</b>

📊 الزوج: <b>{signal['pair']}</b>
🔔 الإشارة: <b>{signal['signal']}</b>
💰 نقطة الدخول: <b>{signal['entry']}</b>
🛑 وقف الخسارة: <b>{signal['stop_loss']}</b>
🎁 جني الأرباح: <b>{signal['take_profit']}</b>
⭐ جودة الإشارة: <b>{signal['quality_score']}%</b>
💬 السبب: <b>{signal['reason']}</b>
⏰ التوقيت: <b>{signal['timestamp']}</b>

<i>✅ هذه رسالة اختبار للتحقق من الاتصال</i>
"""
    
    # إرسال للجميع
    for chat_id in test_chat_ids:
        try:
            print(f"\n📤 إرسال إلى Chat ID: {chat_id}...", end="", flush=True)
            
            response = requests.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code == 200 and response.json().get('ok'):
                print(" ✅ نجح!")
            else:
                print(f" ❌ فشل - {response.status_code}")
                print(f"   الخطأ: {response.json().get('description', 'غير معروف')}")
                
        except Exception as e:
            print(f" ❌ خطأ في الاتصال: {e}")
    
    # حفظ الإشارة في sent_signals.json
    print("\n" + "="*60)
    print("💾 حفظ الإشارة في السجل...")
    
    try:
        sent_signals = []
        if os.path.exists('sent_signals.json'):
            with open('sent_signals.json', 'r', encoding='utf-8') as f:
                sent_signals = json.load(f)
        
        sent_signals.append({
            'signal_id': f"TEST_{signal['pair']}_{datetime.now().timestamp()}",
            'sent_at': datetime.now().isoformat(),
            'test_mode': True
        })
        
        with open('sent_signals.json', 'w', encoding='utf-8') as f:
            json.dump(sent_signals, f, indent=2, ensure_ascii=False)
        
        print("✅ تم حفظ الإشارة بنجاح")
        
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")

if __name__ == "__main__":
    send_test_signal()

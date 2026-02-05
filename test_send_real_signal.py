#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إرسال إشارة حقيقية باستخدام Chat IDs المكتشفة
"""
import json
import os
import sys
import requests
from datetime import datetime
import sqlite3

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_real_test_signal():
    """إرسال إشارة اختبار حقيقية"""
    
    print("\n" + "="*70)
    print("🔔 اختبار إرسال إشارة حقيقية عبر Telegram")
    print("="*70)
    
    # جمع Chat IDs من قاعدة البيانات
    chat_ids = []
    try:
        conn = sqlite3.connect('vip_subscriptions.db')
        c = conn.cursor()
        
        c.execute("SELECT user_id, username, chat_id FROM users WHERE chat_id IS NOT NULL")
        rows = c.fetchall()
        
        for row in rows:
            if row[2]:  # إذا كان هناك chat_id
                chat_ids.append({
                    'id': row[0],
                    'username': row[1],
                    'chat_id': row[2]
                })
        
        conn.close()
    except Exception as e:
        print(f"❌ خطأ في قراءة قاعدة البيانات: {e}")
        return
    
    if not chat_ids:
        print("❌ لا توجد Chat IDs في قاعدة البيانات!")
        return
    
    print(f"\n✓ وجدنا {len(chat_ids)} مستخدم مع Chat IDs")
    
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
    
    success_count = 0
    failed_count = 0
    
    # إرسال للجميع
    print("\n" + "-"*70)
    for user in chat_ids:
        try:
            print(f"📤 إرسال إلى {user['username']} (Chat ID: {user['chat_id']})...", end="", flush=True)
            
            response = requests.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": user['chat_id'],
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code == 200 and response.json().get('ok'):
                print(" ✅ نجح!")
                success_count += 1
            else:
                print(f" ❌ فشل - {response.status_code}")
                print(f"   الخطأ: {response.json().get('description', 'غير معروف')}")
                failed_count += 1
                
        except Exception as e:
            print(f" ❌ خطأ: {e}")
            failed_count += 1
    
    # النتيجة
    print("\n" + "="*70)
    print("📊 النتائج:")
    print("="*70)
    print(f"✅ نجح: {success_count}")
    print(f"❌ فشل: {failed_count}")
    print(f"📈 نسبة النجاح: {(success_count/(success_count+failed_count)*100):.1f}%" if (success_count+failed_count) > 0 else "لا توجد نتائج")

if __name__ == "__main__":
    send_real_test_signal()

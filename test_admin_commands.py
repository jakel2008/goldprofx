#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار سريع لأوامر الأدمن
"""

import sys
import os
import requests
import time

# إصلاح الترميز
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
ADMIN_CHAT_ID = 7657829546

def send_command(command):
    """إرسال أمر للبوت"""
    print(f"📤 إرسال: {command}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": ADMIN_CHAT_ID,
                "text": command
            },
            timeout=10
        )
        
        if response.status_code == 200 and response.json().get('ok'):
            print(f"   ✅ تم الإرسال")
            return True
        else:
            print(f"   ❌ فشل: {response.json()}")
            return False
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return False

def main():
    """الوظيفة الرئيسية"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "🧪 اختبار أوامر الأدمن" + " "*33 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    print(f"🎯 البوت: @ABOOHASHEMFXBOT")
    print(f"👤 الأدمن: {ADMIN_CHAT_ID}")
    print()
    
    commands = [
        ('/admin', 'لوحة التحكم'),
        ('/admin_stats', 'الإحصائيات'),
        ('/admin_users', 'قائمة المستخدمين')
    ]
    
    print("سيتم إرسال الأوامر التالية:\n")
    for cmd, desc in commands:
        print(f"  {cmd} - {desc}")
    print()
    
    input("اضغط Enter للبدء...")
    print()
    
    for i, (cmd, desc) in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}] {desc}")
        print("="*60)
        
        send_command(cmd)
        
        if i < len(commands):
            print("\n⏳ انتظار 3 ثواني...")
            time.sleep(3)
    
    print("\n" + "="*80)
    print("✅ تم إرسال جميع الأوامر!")
    print("📱 تحقق من Telegram لرؤية النتائج")
    print("="*80)
    print()

if __name__ == "__main__":
    main()

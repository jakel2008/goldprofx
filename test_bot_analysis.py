#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار أوامر التحليل في البوت
"""

import sys
import os

# إصلاح الترميز
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

import requests

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
TEST_CHAT_ID = 7657829546  # Abo hashem

def send_command_test(command, symbol_name):
    """إرسال أمر اختبار"""
    print(f"📤 إرسال أمر: {command}")
    print(f"   الزوج: {symbol_name}")
    
    try:
        # إرسال الرسالة
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": TEST_CHAT_ID,
                "text": command
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print(f"✅ تم إرسال الأمر بنجاح!")
                print(f"   انتظر النتيجة في Telegram...")
                return True
            else:
                print(f"❌ فشل: {data.get('description', 'Unknown')}")
                return False
        else:
            print(f"❌ خطأ HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def main():
    """الوظيفة الرئيسية"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "🧪 اختبار أوامر التحليل" + " "*33 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    tests = [
        ('/analyze_eurusd', 'اليورو/دولار'),
        ('/analyze_gbpusd', 'الجنيه/دولار'),
        ('/analyze_xauusd', 'الذهب'),
        ('/analyze_btcusd', 'البيتكوين')
    ]
    
    print(f"🎯 سيتم إرسال {len(tests)} أمر اختبار إلى Telegram")
    print(f"📱 Chat ID: {TEST_CHAT_ID}")
    print()
    
    input("اضغط Enter للبدء...")
    print()
    
    for i, (command, name) in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}]")
        print("="*60)
        
        success = send_command_test(command, name)
        
        if i < len(tests):
            input("\nاضغط Enter للأمر التالي...")
    
    print("\n" + "="*80)
    print("✅ تم إرسال جميع الأوامر!")
    print("📱 تحقق من Telegram لرؤية النتائج")
    print("="*80)
    print()

if __name__ == "__main__":
    main()

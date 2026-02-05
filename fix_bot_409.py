#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إصلاح مشكلة 409 - حذف webhook
"""

import requests
import sys
import os

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def delete_webhook():
    """حذف webhook لحل مشكلة 409"""
    print("🔧 حذف webhook...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/deleteWebhook",
            json={"drop_pending_updates": True},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ تم حذف webhook بنجاح!")
                return True
            else:
                print(f"❌ فشل: {data.get('description')}")
                return False
        else:
            print(f"❌ خطأ HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def get_webhook_info():
    """عرض معلومات webhook"""
    print("\n📋 معلومات webhook الحالي:")
    
    try:
        response = requests.get(f"{BASE_URL}/getWebhookInfo", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                info = data['result']
                print(f"   URL: {info.get('url', 'None')}")
                print(f"   Pending Updates: {info.get('pending_update_count', 0)}")
                print(f"   Last Error: {info.get('last_error_message', 'None')}")
                return info
        else:
            print(f"❌ خطأ: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔧 إصلاح مشكلة 409 Conflict")
    print("="*60)
    
    get_webhook_info()
    print()
    delete_webhook()
    print()
    get_webhook_info()
    
    print("\n" + "="*60)
    print("✅ يمكنك الآن تشغيل البوت")
    print("="*60)
    print()

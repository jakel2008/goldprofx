#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تسجيل جميع أوامر البوت (عادية + أدمن)
"""

import sys
import os
import requests
import json

# إصلاح الترميز
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def register_commands():
    """تسجيل جميع الأوامر"""
    print("="*80)
    print("📝 تسجيل أوامر البوت")
    print("="*80)
    print()
    
    # الأوامر العادية
    user_commands = [
        {"command": "start", "description": "🎯 البدء والترحيب"},
        {"command": "subscribe", "description": "📝 إنشاء حساب مجاني"},
        {"command": "status", "description": "📊 حالة الاشتراك"},
        {"command": "plans", "description": "💎 الباقات المتاحة"},
        {"command": "upgrade", "description": "⬆️ ترقية الباقة"},
        {"command": "help", "description": "❓ قائمة الأوامر"},
        {"command": "analyze", "description": "📈 قائمة التحليل"},
        {"command": "analyze_eurusd", "description": "تحليل EURUSD"},
        {"command": "analyze_gbpusd", "description": "تحليل GBPUSD"},
        {"command": "analyze_usdjpy", "description": "تحليل USDJPY"},
        {"command": "analyze_xauusd", "description": "تحليل الذهب"},
        {"command": "analyze_btcusd", "description": "تحليل البيتكوين"},
        {"command": "referral", "description": "🎁 كود الإحالة"}
    ]
    
    # أوامر الأدمن
    admin_commands = [
        {"command": "admin", "description": "👨‍💼 لوحة تحكم الأدمن"},
        {"command": "admin_stats", "description": "📊 إحصائيات النظام"},
        {"command": "admin_users", "description": "👥 قائمة المستخدمين"},
        {"command": "admin_user", "description": "👤 تفاصيل مستخدم"},
        {"command": "admin_upgrade", "description": "⬆️ ترقية مستخدم"},
        {"command": "admin_extend", "description": "➕ تمديد اشتراك"},
        {"command": "admin_cancel", "description": "❌ إلغاء اشتراك"},
        {"command": "admin_reactivate", "description": "♻️ إعادة تفعيل"},
        {"command": "admin_broadcast", "description": "📤 بث رسالة"},
        {"command": "admin_test", "description": "🧪 اختبار رسالة"}
    ]
    
    # تسجيل الأوامر العادية
    print("1️⃣ تسجيل الأوامر العادية...")
    try:
        response = requests.post(
            f"{BASE_URL}/setMyCommands",
            json={"commands": user_commands},
            timeout=10
        )
        
        if response.status_code == 200 and response.json().get('ok'):
            print(f"   ✅ تم تسجيل {len(user_commands)} أمر عادي")
        else:
            print(f"   ❌ فشل: {response.json()}")
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # تسجيل أوامر الأدمن
    print("\n2️⃣ تسجيل أوامر الأدمن...")
    
    # الأدمن
    admin_users = [7657829546, 111111111]  # IDs من admin_users.json
    
    for admin_id in admin_users:
        try:
            # تسجيل الأوامر العادية + أوامر الأدمن
            all_commands = user_commands + admin_commands
            
            response = requests.post(
                f"{BASE_URL}/setMyCommands",
                json={
                    "commands": all_commands,
                    "scope": {
                        "type": "chat",
                        "chat_id": admin_id
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200 and response.json().get('ok'):
                print(f"   ✅ Admin {admin_id}: {len(all_commands)} أمر")
            else:
                print(f"   ⚠️ Admin {admin_id}: {response.json().get('description', 'خطأ')}")
        except Exception as e:
            print(f"   ❌ Admin {admin_id}: {e}")
    
    print("\n" + "="*80)
    print("✅ اكتمل تسجيل الأوامر!")
    print("="*80)
    
    # عرض قائمة الأوامر
    print("\n📋 الأوامر المسجلة:\n")
    print("<b>للمستخدمين العاديين:</b>")
    for cmd in user_commands:
        print(f"   /{cmd['command']} - {cmd['description']}")
    
    print("\n<b>للأدمن فقط:</b>")
    for cmd in admin_commands:
        print(f"   /{cmd['command']} - {cmd['description']}")
    
    print()

if __name__ == "__main__":
    register_commands()

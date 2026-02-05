#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
فحص وتشخيص مشكلة أوامر البوت
"""

import requests
import json
import os
import sys

# إصلاح الترميز
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def check_bot_info():
    """التحقق من معلومات البوت"""
    print("="*80)
    print("🤖 فحص معلومات البوت")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                result = bot_info['result']
                print(f"✅ البوت نشط ويعمل")
                print(f"   الاسم: {result['first_name']}")
                print(f"   Username: @{result.get('username', 'N/A')}")
                print(f"   ID: {result['id']}")
                print(f"   يدعم المجموعات: {result.get('can_join_groups', False)}")
                return True
            else:
                print(f"❌ خطأ: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ فشل الاتصال: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

def get_recent_updates():
    """جلب آخر التحديثات من Telegram"""
    print("\n" + "="*80)
    print("📬 فحص الرسائل الواردة")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                updates = data['result']
                print(f"✅ تم جلب {len(updates)} تحديث")
                
                if updates:
                    print("\n📝 آخر 5 رسائل:")
                    for update in updates[-5:]:
                        update_id = update.get('update_id')
                        message = update.get('message', {})
                        text = message.get('text', 'N/A')
                        from_user = message.get('from', {})
                        chat_id = message.get('chat', {}).get('id')
                        date = message.get('date')
                        
                        print(f"\n   Update ID: {update_id}")
                        print(f"   من: {from_user.get('first_name', 'Unknown')} (@{from_user.get('username', 'N/A')})")
                        print(f"   Chat ID: {chat_id}")
                        print(f"   النص: {text}")
                        print(f"   التاريخ: {date}")
                else:
                    print("\n⚠️ لا توجد تحديثات جديدة")
                    
                return updates
            else:
                print(f"❌ خطأ: {data.get('description', 'Unknown error')}")
                return None
        else:
            print(f"❌ فشل الاتصال: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None

def check_bot_commands():
    """التحقق من الأوامر المسجلة في البوت"""
    print("\n" + "="*80)
    print("⚙️ فحص الأوامر المسجلة")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/getMyCommands", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                commands = data['result']
                if commands:
                    print(f"✅ الأوامر المسجلة ({len(commands)}):")
                    for cmd in commands:
                        print(f"   /{cmd['command']} - {cmd['description']}")
                else:
                    print("⚠️ لا توجد أوامر مسجلة في BotFather")
                    print("   يجب تسجيل الأوامر يدوياً")
                return commands
            else:
                print(f"❌ خطأ: {data.get('description', 'Unknown error')}")
                return None
        else:
            print(f"❌ فشل الاتصال: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None

def register_bot_commands():
    """تسجيل الأوامر في البوت"""
    print("\n" + "="*80)
    print("📝 تسجيل الأوامر")
    print("="*80)
    
    commands = [
        {"command": "start", "description": "🎯 البدء والترحيب"},
        {"command": "subscribe", "description": "📝 إنشاء حساب مجاني"},
        {"command": "status", "description": "📊 حالة الاشتراك"},
        {"command": "help", "description": "❓ قائمة الأوامر"},
        {"command": "plans", "description": "💎 الباقات المتاحة"},
        {"command": "myid", "description": "🆔 معرفة الآيدي الخاص بك"},
        {"command": "analyze", "description": "📈 قائمة التحليل"},
        {"command": "analyze_eurusd", "description": "تحليل EURUSD"},
        {"command": "analyze_gbpusd", "description": "تحليل GBPUSD"},
        {"command": "analyze_usdjpy", "description": "تحليل USDJPY"},
        {"command": "analyze_xauusd", "description": "تحليل الذهب"},
        {"command": "analyze_btcusd", "description": "تحليل البيتكوين"},
        {"command": "referral", "description": "🎁 كود الإحالة"}
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/setMyCommands",
            json={"commands": commands},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ تم تسجيل الأوامر بنجاح!")
                print(f"   عدد الأوامر: {len(commands)}")
                for cmd in commands:
                    print(f"   /{cmd['command']}")
                return True
            else:
                print(f"❌ فشل التسجيل: {data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ فشل الاتصال: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def test_send_message():
    """اختبار إرسال رسالة"""
    print("\n" + "="*80)
    print("📤 اختبار إرسال رسالة")
    print("="*80)
    
    # Chat ID للمستخدم الحقيقي
    chat_id = 7657829546
    
    message = """
🤖 اختبار أوامر البوت

الأوامر المتاحة:
/start - البدء
/subscribe - إنشاء حساب
/status - حالة الاشتراك
/help - المساعدة
/plans - الباقات
/analyze - التحليل
/referral - كود الإحالة

جرب أي أمر الآن! 👆
"""
    
    try:
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print(f"✅ تم إرسال رسالة الاختبار بنجاح!")
                print(f"   Message ID: {data['result']['message_id']}")
                return True
            else:
                print(f"❌ فشل الإرسال: {data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ فشل الاتصال: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def check_last_update_file():
    """فحص ملف last_update.json"""
    print("\n" + "="*80)
    print("📂 فحص ملف التحديثات")
    print("="*80)
    
    if os.path.exists('last_update.json'):
        try:
            with open('last_update.json', 'r') as f:
                data = json.load(f)
            print(f"✅ آخر Update ID: {data.get('last_update_id', 'N/A')}")
            return data
        except Exception as e:
            print(f"❌ خطأ في القراءة: {e}")
            return None
    else:
        print("⚠️ الملف غير موجود (سيتم إنشاؤه عند أول تشغيل)")
        return None

def main():
    """الوظيفة الرئيسية"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "🔍 تشخيص أوامر البوت" + " "*35 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # 1. فحص معلومات البوت
    bot_ok = check_bot_info()
    
    if not bot_ok:
        print("\n❌ البوت غير متصل! تحقق من Token")
        return
    
    # 2. فحص الأوامر المسجلة
    registered_commands = check_bot_commands()
    
    # 3. تسجيل الأوامر إذا لم تكن مسجلة
    if not registered_commands:
        print("\n⚠️ لا توجد أوامر مسجلة، سيتم التسجيل الآن...")
        register_bot_commands()
    
    # 4. فحص آخر تحديث
    check_last_update_file()
    
    # 5. جلب الرسائل الواردة
    updates = get_recent_updates()
    
    # 6. اختبار إرسال رسالة
    test_send_message()
    
    print("\n" + "="*80)
    print("✅ اكتمل الفحص!")
    print("="*80)
    
    # التوصيات
    print("\n📋 التوصيات:")
    print("   1. تأكد من تشغيل vip_bot_simple.py")
    print("   2. جرب الأوامر في Telegram الآن")
    print("   3. إذا لم تعمل، أعد تشغيل البوت بـ START_BOT.bat")
    print()

if __name__ == "__main__":
    main()

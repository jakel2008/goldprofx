#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الحصول على Chat ID الحقيقي من Telegram
"""
import requests
import os
import sys
import json
from datetime import datetime

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_updates():
    """الحصول على آخر الرسائل والأوامر"""
    print("\n" + "="*70)
    print("📱 جمع Chat IDs من Telegram")
    print("="*70)
    print("""
⚠️  تعليمات:
1. افتح تطبيق Telegram على هاتفك
2. ابحث عن البوت: @GOLD PRO Bot (أو استخدم الـ Token)
3. أرسل أي رسالة (مثل: /start أو Hello)
4. سيظهر Chat ID هنا
    """)
    print("-"*70)
    
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                updates = data.get('result', [])
                print(f"\n✓ تم الحصول على {len(updates)} رسالة")
                
                chat_ids = {}
                
                for update in updates:
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        username = msg['chat'].get('username', 'بدون اسم')
                        first_name = msg['chat'].get('first_name', 'مستخدم')
                        text = msg.get('text', '[لا نص]')
                        date = msg.get('date', 0)
                        
                        if chat_id not in chat_ids:
                            chat_ids[chat_id] = {
                                'username': username,
                                'first_name': first_name,
                                'latest_message': text,
                                'timestamp': datetime.fromtimestamp(date).isoformat()
                            }
                
                if chat_ids:
                    print("\n📋 Chat IDs المكتشفة:")
                    print("-"*70)
                    
                    for chat_id, info in chat_ids.items():
                        print(f"""
   Chat ID: {chat_id}
   المستخدم: {info['first_name']} (@{info['username']})
   آخر رسالة: {info['latest_message'][:50]}
   التوقيت: {info['timestamp']}""")
                    
                    # حفظ الـ Chat IDs
                    with open('discovered_chat_ids.json', 'w', encoding='utf-8') as f:
                        json.dump(chat_ids, f, indent=2, ensure_ascii=False)
                    
                    print("\n✅ تم حفظ Chat IDs في: discovered_chat_ids.json")
                    
                    # تحديث قاعدة البيانات
                    print("\n" + "="*70)
                    print("🔄 تحديث قاعدة البيانات...")
                    
                    import sqlite3
                    conn = sqlite3.connect('vip_subscriptions.db')
                    c = conn.cursor()
                    
                    for idx, (chat_id, info) in enumerate(chat_ids.items(), 1):
                        # محاولة العثور على المستخدم بـ username أو إنشاء جديد
                        c.execute("""
                            UPDATE users 
                            SET chat_id = ?, telegram_id = ?
                            WHERE user_id = ?
                        """, (str(chat_id), chat_id, idx))
                    
                    conn.commit()
                    conn.close()
                    print("✅ تم تحديث قاعدة البيانات")
                    
                else:
                    print("""
❌ لم يتم العثور على أي رسائل

⚠️  تأكد من:
1. توكن البوت صحيح
2. تم تشغيل البوت
3. أرسلت رسالة للبوت
4. الانتظار بضع ثوان ثم المحاولة مجدداً
                    """)
            else:
                print(f"❌ خطأ: {data}")
                
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")

if __name__ == "__main__":
    get_updates()

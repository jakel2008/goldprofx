"""
اختبار سريع لإرسال إشارة إلى البوت
"""
import requests
import json
import sqlite3
from datetime import datetime

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"

def get_all_active_users():
    """الحصول على جميع المستخدمين النشطين"""
    conn = sqlite3.connect('vip_subscriptions.db')
    c = conn.cursor()
    c.execute("SELECT user_id, plan FROM users WHERE status='active'")
    users = c.fetchall()
    conn.close()
    return users

def send_test_signal():
    """إرسال إشارة اختبارية"""
    users = get_all_active_users()
    print(f"📊 عدد المستخدمين النشطين: {len(users)}")
    
    # قراءة آخر إشارة من المجلد
    import os
    signals_dir = "signals"
    if os.path.exists(signals_dir):
        signal_files = [f for f in os.listdir(signals_dir) if f.endswith('.json')]
        if signal_files:
            latest_signal = sorted(signal_files)[-1]
            with open(f"{signals_dir}/{latest_signal}", 'r', encoding='utf-8') as f:
                signal_data = json.load(f)
            
            print(f"📡 إرسال الإشارة: {signal_data.get('symbol', 'Unknown')}")
            
            # تنسيق الرسالة
            symbol = signal_data.get('symbol', 'Unknown')
            trade_type = signal_data.get('trade_type', 'Unknown')
            entry = signal_data.get('entry_price', 0)
            sl = signal_data.get('stop_loss', 0)
            tp = signal_data.get('take_profit', [])
            
            message = f"""
🔔 *إشارة جديدة*

💱 الزوج: *{symbol}*
📊 النوع: {trade_type}
💰 سعر الدخول: `{entry}`
🛑 وقف الخسارة: `{sl}`
🎯 الأهداف:
"""
            if isinstance(tp, list):
                for i, target in enumerate(tp, 1):
                    message += f"   • الهدف {i}: `{target}`\n"
            
            message += f"\n⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # إرسال لجميع المستخدمين
            success_count = 0
            for user_id, plan in users:
                try:
                    response = requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={
                            'chat_id': user_id,
                            'text': message,
                            'parse_mode': 'Markdown'
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        success_count += 1
                        print(f"✅ تم الإرسال إلى: {user_id} ({plan})")
                    else:
                        print(f"❌ فشل الإرسال إلى: {user_id} - {response.json()}")
                except Exception as e:
                    print(f"❌ خطأ في الإرسال إلى {user_id}: {e}")
            
            print(f"\n✅ تم إرسال الإشارة إلى {success_count}/{len(users)} مستخدم")
        else:
            print("⚠️ لا توجد إشارات في المجلد")
    else:
        print("⚠️ مجلد الإشارات غير موجود")

if __name__ == "__main__":
    send_test_signal()

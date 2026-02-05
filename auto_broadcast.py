"""
نظام البث التلقائي للإشارات
يقوم بفحص الإشارات الجديدة وإرسالها للمستخدمين النشطين
"""
import requests
import json
import sqlite3
import time
import os
from datetime import datetime
from pathlib import Path

BOT_TOKEN = "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A"
SIGNALS_DIR = Path("signals")
SENT_LOG_FILE = Path("sent_signals_log.json")

# عتبات الجودة حسب الباقة
QUALITY_THRESHOLDS = {
    'free': 80,
    'bronze': 70,
    'silver': 60,
    'gold': 50,
    'platinum': 40
}

def log_message(msg):
    """طباعة رسالة مع الوقت"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_active_users():
    """الحصول على المستخدمين النشطين"""
    try:
        conn = sqlite3.connect('vip_subscriptions.db')
        c = conn.cursor()
        c.execute("SELECT user_id, plan FROM users WHERE status='active'")
        users = c.fetchall()
        conn.close()
        return users
    except Exception as e:
        log_message(f"❌ خطأ في قراءة المستخدمين: {e}")
        return []

def load_sent_signals():
    """تحميل سجل الإشارات المرسلة"""
    if SENT_LOG_FILE.exists():
        try:
            with open(SENT_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def mark_signal_sent(signal_file):
    """تسجيل الإشارة كمرسلة"""
    sent = load_sent_signals()
    sent.append({
        'file': signal_file,
        'sent_at': datetime.now().isoformat()
    })
    # الاحتفاظ بآخر 100 إشارة
    if len(sent) > 100:
        sent = sent[-100:]
    
    with open(SENT_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent, f, indent=2, ensure_ascii=False)

def format_signal_message(signal_data):
    """تنسيق رسالة الإشارة"""
    symbol = signal_data.get('symbol', 'Unknown')
    trade_type = signal_data.get('trade_type', 'Unknown')
    entry = signal_data.get('entry_price', 0)
    sl = signal_data.get('stop_loss', 0)
    tp = signal_data.get('take_profit', [])
    confidence = signal_data.get('confidence', 'MEDIUM')
    
    # رموز الاتجاه
    direction = "📈" if "Buy" in trade_type or "buy" in trade_type.lower() else "📉"
    
    message = f"""
{direction} *إشارة جديدة من GOLD PRO VIP*

💱 الزوج: *{symbol}*
📊 النوع: {trade_type}
💰 سعر الدخول: `{entry:.5f}`
🛑 وقف الخسارة: `{sl:.5f}`

🎯 *الأهداف:*
"""
    
    if isinstance(tp, list):
        for i, target in enumerate(tp, 1):
            message += f"   {i}. `{target:.5f}`\n"
    else:
        message += f"   1. `{tp:.5f}`\n"
    
    # إضافة مستوى الثقة
    confidence_emoji = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}.get(confidence, "⚪")
    message += f"\n{confidence_emoji} مستوى الثقة: *{confidence}*"
    
    message += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    message += "\n\n💡 *تذكير:* التزم بإدارة المخاطر ولا تخاطر بأكثر من 2٪ من رأس المال"
    
    return message

def send_signal_to_user(user_id, message):
    """إرسال الإشارة لمستخدم واحد"""
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
        return response.status_code == 200
    except Exception as e:
        log_message(f"❌ خطأ في إرسال الإشارة لـ {user_id}: {e}")
        return False

def broadcast_new_signals():
    """فحص وبث الإشارات الجديدة"""
    if not SIGNALS_DIR.exists():
        log_message("⚠️ مجلد الإشارات غير موجود")
        return
    
    # قراءة الإشارات المرسلة سابقاً
    sent_signals = load_sent_signals()
    sent_files = [s['file'] for s in sent_signals]
    
    # فحص الإشارات الجديدة
    signal_files = sorted([f for f in SIGNALS_DIR.glob("*.json")])
    
    for signal_file in signal_files:
        if signal_file.name in sent_files:
            continue  # تم إرسالها مسبقاً
        
        try:
            # قراءة الإشارة
            with open(signal_file, 'r', encoding='utf-8') as f:
                signal_data = json.load(f)
            
            log_message(f"📡 إشارة جديدة: {signal_data.get('symbol', 'Unknown')}")
            
            # تنسيق الرسالة
            message = format_signal_message(signal_data)
            
            # الحصول على المستخدمين النشطين
            users = get_active_users()
            if not users:
                log_message("⚠️ لا يوجد مستخدمون نشطون")
                continue
            
            # إرسال للمستخدمين
            success_count = 0
            for user_id, plan in users:
                if send_signal_to_user(user_id, message):
                    success_count += 1
                    log_message(f"✅ تم الإرسال إلى {user_id} ({plan})")
                time.sleep(0.1)  # تجنب الحظر من Telegram
            
            log_message(f"✅ تم إرسال الإشارة إلى {success_count}/{len(users)} مستخدم")
            
            # تسجيل الإشارة كمرسلة
            mark_signal_sent(signal_file.name)
            
        except Exception as e:
            log_message(f"❌ خطأ في معالجة {signal_file.name}: {e}")

def run_broadcaster(interval=60):
    """تشغيل نظام البث بشكل مستمر"""
    log_message("=" * 60)
    log_message("🚀 نظام البث التلقائي للإشارات")
    log_message("=" * 60)
    log_message(f"⏱️ فحص كل {interval} ثانية")
    log_message("=" * 60)
    
    try:
        while True:
            broadcast_new_signals()
            time.sleep(interval)
    except KeyboardInterrupt:
        log_message("\n⏹️ تم إيقاف نظام البث")

if __name__ == "__main__":
    # فحص واحد للإشارات الحالية
    broadcast_new_signals()
    
    # بدء التشغيل المستمر
    log_message("\n🔄 بدء وضع المراقبة المستمرة...")
    run_broadcaster(interval=300)  # كل 5 دقائق

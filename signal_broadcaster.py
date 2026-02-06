"""
نظام بث الإشارات التلقائي للبوت VIP
يقرأ الإشارات المحفوظة ويرسلها للبوت تلقائياً
"""

import sys
import os

# إصلاح مشكلة الترميز على Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

import json
import time
import sqlite3
import requests
import hashlib
from datetime import datetime
from pathlib import Path

# إعدادات البوت
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
DEFAULT_CHAT_ID = os.environ.get("MM_TELEGRAM_CHAT_ID", "7657829546")

# مسارات الملفات
SIGNALS_DIR = Path(__file__).parent / "signals"
SENT_SIGNALS_FILE = Path(__file__).parent / "sent_signals.json"


def load_sent_signals():
    """تحميل قائمة الإشارات المرسلة"""
    if SENT_SIGNALS_FILE.exists():
        try:
            with open(SENT_SIGNALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_sent_signal(signal_id, signature=None):
    """حفظ معرف الإشارة المرسلة"""
    sent = load_sent_signals()
    sig = signature or signal_id
    existing = {item.get('signature') or item.get('signal_id') for item in sent if isinstance(item, dict)}
    if sig in existing:
        return
    sent.append({
        'signal_id': signal_id,
        'signature': sig,
        'sent_at': datetime.now().isoformat()
    })
    # الاحتفاظ بآخر 1000 إشارة فقط
    if len(sent) > 1000:
        sent = sent[-1000:]
    
    with open(SENT_SIGNALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent, f, indent=2, ensure_ascii=False)


def get_active_users_by_plan():
    """الحصول على المستخدمين النشطين مرتبين حسب الخطة - من قاعدة البيانات فقط"""
    try:
        conn = sqlite3.connect('vip_subscriptions.db')
        c = conn.cursor()
        # استخدام المستخدمين الفعليين من قاعدة البيانات
        c.execute("SELECT user_id, plan, chat_id FROM users WHERE status='active' AND chat_id IS NOT NULL")
        users = c.fetchall()
        conn.close()
        
        # تنظيم المستخدمين حسب الخطة
        users_by_plan = {
            'free': [],
            'bronze': [],
            'silver': [],
            'gold': [],
            'platinum': []
        }
        
        active_users_count = 0
        
        for user_id, plan, chat_id in users:
            if plan not in users_by_plan:
                continue
            
            # تحويل Chat ID إلى رقم صحيح
            try:
                target_chat_id = int(str(chat_id).strip())
                if target_chat_id > 0:
                    users_by_plan[plan].append(target_chat_id)
                    active_users_count += 1
            except (ValueError, TypeError):
                continue
        
        # إزالة التكرارات لكل خطة
        for plan in users_by_plan:
            users_by_plan[plan] = list(dict.fromkeys(users_by_plan[plan]))
        
        # طباعة ملخص المستخدمين
        total_users = sum(len(v) for v in users_by_plan.values())
        if total_users > 0:
            print(f"👥 المستخدمون النشطون المكتشفون: {total_users}")
            for plan, users in users_by_plan.items():
                if users:
                    print(f"   {plan.upper()}: {len(users)} مستخدم")

        return users_by_plan
    except Exception as e:
        print(f"❌ خطأ في قراءة المستخدمين: {e}")
        return {'free': [], 'bronze': [], 'silver': [], 'gold': [], 'platinum': []}


def calculate_signal_quality(signal_data):
    """حساب جودة الإشارة (0-100)"""
    try:
        if signal_data.get('quality_score') is not None:
            return int(signal_data.get('quality_score'))
        confidence = signal_data.get('confidence', 'MEDIUM')
        quality_map = {
            'HIGH': 85,
            'MEDIUM': 65,
            'LOW': 45
        }
        return quality_map.get(confidence, 65)
    except:
        return 65


def send_with_retry(user_id, message, max_attempts=3):
    """إرسال رسالة مع إعادة المحاولة"""
    for attempt in range(1, max_attempts + 1):
        try:
            timeout = 10 * attempt
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    'chat_id': user_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                },
                timeout=timeout
            )
            if response.status_code == 200:
                return True
        except Exception:
            if attempt == max_attempts:
                return False
        time.sleep(0.2)
    return False


def send_signal_to_users(signal_data, quality_score):
    """إرسال الإشارة للمستخدمين حسب جودتها وخططهم"""
    # فلترة أفضل الصفقات فقط
    entry = signal_data.get('entry_price', signal_data.get('entry', 0))
    sl = signal_data.get('stop_loss', signal_data.get('sl', 0))
    tp1 = signal_data.get('take_profit_1', signal_data.get('tp1'))
    try:
        entry = float(entry)
        sl = float(sl)
        tp1 = float(tp1) if tp1 is not None else 0
        risk = abs(entry - sl)
        reward = abs(tp1 - entry)
        rr = (reward / risk) if risk > 0 and reward > 0 else 0
    except Exception:
        rr = 0

    # تم تعطيل فلترة الجودة/العائد لإرسال جميع الإشارات

    users_by_plan = get_active_users_by_plan()
    
    # إرسال لكل الخطط دون تقييد
    eligible_plans = ['platinum', 'gold', 'silver', 'bronze', 'free']
    
    # بيانات الإشارة
    symbol = signal_data.get('symbol') or signal_data.get('pair', 'Unknown')
    trade_type = signal_data.get('trade_type') or signal_data.get('signal_type') or signal_data.get('signal', 'Signal')
    entry = signal_data.get('entry_price', signal_data.get('entry', 0))
    sl = signal_data.get('stop_loss', signal_data.get('sl', 0))
    tp_list = [
        signal_data.get('take_profit_1', signal_data.get('tp1')),
        signal_data.get('take_profit_2', signal_data.get('tp2')),
        signal_data.get('take_profit_3', signal_data.get('tp3'))
    ]
    tp = [t for t in tp_list if t]  # إزالة القيم الفارغة
    
    # استخدام التنسيق الجديد
    from signal_formatter import format_signal_message
    
    message = format_signal_message(
        symbol=symbol,
        signal_type=trade_type,
        entry=entry,
        stop_loss=sl,
        take_profits=tp,
        quality_score=quality_score
    )
    
    # إرسال للمستخدمين المؤهلين
    sent_count = 0
    for plan in eligible_plans:
        for user_id in users_by_plan.get(plan, []):
            success = send_with_retry(user_id, message)
            if success:
                sent_count += 1
                print(f"   ✅ {user_id} ({plan})")
            else:
                print(f"   ❌ خطأ في الإرسال لـ {user_id}")
            time.sleep(0.05)  # تأخير بسيط بين الإرسالات
    
    return sent_count


def _normalize_price(value):
    try:
        return f"{float(value):.5f}"
    except Exception:
        return "0.00000"


def get_signal_id(signal_data):
    """إنشاء معرف ثابت لتجنب تكرار نفس الصفقة"""
    trade_id = signal_data.get('trade_id')
    if trade_id:
        return f"trade_{trade_id}"

    symbol = (signal_data.get('symbol') or signal_data.get('pair') or 'UNK').upper()
    direction = (signal_data.get('trade_type') or signal_data.get('signal_type') or signal_data.get('signal') or '').strip().upper()
    entry = _normalize_price(signal_data.get('entry_price', signal_data.get('entry', 0)))
    sl = _normalize_price(signal_data.get('stop_loss', signal_data.get('sl', 0)))
    tp1 = _normalize_price(signal_data.get('take_profit_1', signal_data.get('tp1', 0)))
    tp2 = _normalize_price(signal_data.get('take_profit_2', signal_data.get('tp2', 0)))
    tp3 = _normalize_price(signal_data.get('take_profit_3', signal_data.get('tp3', 0)))

    key = f"{symbol}|{direction}|{entry}|{sl}|{tp1}|{tp2}|{tp3}"
    digest = hashlib.sha1(key.encode('utf-8')).hexdigest()[:16]
    return f"sig_{digest}"


def read_and_broadcast_signals():
    """قراءة وبث الإشارات الجديدة"""
    if not SIGNALS_DIR.exists():
        print(f"⚠️ مجلد الإشارات غير موجود: {SIGNALS_DIR}")
        return 0
    
    sent_signals = load_sent_signals()
    sent_ids = set()
    for s in sent_signals:
        if isinstance(s, dict):
            sent_ids.add(s.get('signature') or s.get('signal_id'))
    
    # قراءة جميع ملفات الإشارات
    signal_files = list(SIGNALS_DIR.glob("*.json"))
    
    if not signal_files:
        print("⏳ لا توجد ملفات إشارات")
        return 0
    
    new_signals_count = 0
    
    for signal_file in signal_files:
        try:
            with open(signal_file, 'r', encoding='utf-8') as f:
                signals = json.load(f)
            
            # التعامل مع الإشارات المخزنة كقائمة أو قاموس
            if isinstance(signals, dict):
                signals = [signals]
            
            for signal in signals:
                signal_id = get_signal_id(signal)
                
                # تحقق إذا لم ترسل من قبل
                if signal_id not in sent_ids:
                    # حساب جودة الإشارة
                    quality_score = calculate_signal_quality(signal)
                    
                    # إرسال الإشارة
                    display_symbol = signal.get('symbol') or signal.get('pair')
                    print(f"\n📢 بث إشارة جديدة: {display_symbol}")
                    print(f"   الجودة: {quality_score}/100")
                    
                    sent_count = send_signal_to_users(signal, quality_score)
                    
                    if sent_count > 0:
                        print(f"✅ تم الإرسال ل {sent_count} مشترك")
                        save_sent_signal(signal_id, signature=signal_id)
                        sent_ids.add(signal_id)
                        new_signals_count += 1
                    else:
                        print("⚠️ لا يوجد مستخدمين مؤهلين")
                    
                    time.sleep(2)  # تأخير بين الإشارات
        
        except Exception as e:
            print(f"❌ خطأ في قراءة {signal_file.name}: {e}")
            continue
    
    return new_signals_count


def start_auto_broadcaster(check_interval=60):
    """بدء بث الإشارات تلقائياً"""
    print("=" * 60)
    print("🤖 نظام بث الإشارات التلقائي")
    print("=" * 60)
    print(f"📁 مجلد الإشارات: {SIGNALS_DIR}")
    print(f"⏰ التحقق كل: {check_interval} ثانية")
    print(f"🚀 بدء المراقبة: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\n⏳ جاري المراقبة... (اضغط Ctrl+C للإيقاف)\n")
    
    try:
        while True:
            try:
                new_count = read_and_broadcast_signals()
                
                if new_count > 0:
                    print(f"\n✅ تم بث {new_count} إشارة جديدة")
                
                # انتظار قبل الفحص التالي
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ خطأ في دورة البث: {e}")
                time.sleep(10)
                
    except KeyboardInterrupt:
        print("\n\n❌ تم إيقاف نظام البث")


if __name__ == "__main__":
    # بدء البث التلقائي (فحص كل دقيقة)
    start_auto_broadcaster(check_interval=60)

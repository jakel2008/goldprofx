"""
بوت تيليجرام موحد لإرسال التوصيات وإدارة اشتراكات VIP
يجمع بين وظائف إرسال التوصيات وإدارة المستخدمين في بوت واحد
"""

import requests
import json
import time
import os
from datetime import datetime
from vip_subscription_system import SubscriptionManager
from quality_scorer import get_quality_threshold_for_plan
import threading

# إعدادات البوت
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# قاعدة البيانات
subscription_manager = SubscriptionManager()

# ملف لتتبع آخر update_id
LAST_UPDATE_FILE = "last_update.json"


def load_last_update():
    """تحميل آخر update_id من الملف"""
    try:
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_update_id', 0)
    except:
        pass
    return 0


def save_last_update(update_id):
    """حفظ آخر update_id"""
    try:
        with open(LAST_UPDATE_FILE, 'w') as f:
            json.dump({'last_update_id': update_id}, f)
    except Exception as e:
        print(f"خطأ في حفظ update_id: {e}")


def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    """إرسال رسالة للمستخدم"""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get('ok', False)
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")
        return False


def send_broadcast_signal(signal_data, quality_score):
    """إرسال توصية لجميع المشتركين النشطين حسب مستوى الجودة"""
    subscribers = subscription_manager.get_all_active_users()
    sent_count = 0
    
    for user_row in subscribers:
        user_id = user_row[0]
        username = user_row[1] if len(user_row) > 1 else "unknown"
        
        # الحصول على معلومات الاشتراك
        sub_info = subscription_manager.check_subscription(user_id)
        
        if not sub_info.get('is_active'):
            continue
        
        plan = sub_info.get('plan', 'free')
        
        # فحص إذا كان المستخدم مؤهل لهذه التوصية
        threshold = get_quality_threshold_for_plan(plan)
        
        # تحويل threshold النصي لرقمي
        threshold_map = {'high': 75, 'medium': 50, 'low': 0}
        min_quality = threshold_map.get(threshold, 75)
        
        if quality_score >= min_quality:
            # التحقق من الحد اليومي
            plan_details = sub_info.get('plan_details', {})
            daily_limit = plan_details.get('signals_per_day', 1)
            
            # حساب عدد التوصيات اليوم
            import sqlite3
            conn = sqlite3.connect('vip_subscriptions.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM signals_sent 
                WHERE user_id = ? AND DATE(sent_at) = DATE('now')
            ''', (user_id,))
            today_count = cursor.fetchone()[0]
            conn.close()
            
            if today_count < daily_limit:
                # تنسيق الرسالة
                message = format_signal_message(signal_data, quality_score, plan)
                
                if send_message(user_id, message):
                    subscription_manager.log_signal_sent(
                        user_id, 
                        str(signal_data), 
                        f"{quality_score}"
                    )
                    sent_count += 1
                    print(f"✅ تم إرسال التوصية للمستخدم {user_id} ({plan})")
                    time.sleep(0.5)  # تجنب Rate Limiting
            else:
                # إرسال تنبيه للمستخدم أنه وصل للحد اليومي
                remaining = daily_limit - today_count
                limit_msg = f"⚠️ لقد وصلت للحد الأقصى اليومي من التوصيات ({today_count}/{daily_limit})\n\n"
                limit_msg += "💎 قم بترقية اشتراكك للحصول على المزيد:\n/plans"
                send_message(user_id, limit_msg)
    
    return sent_count


def format_signal_message(signal, quality_score, user_plan):
    """تنسيق رسالة التوصية"""
    symbol = signal.get('symbol', 'N/A')
    rec = signal.get('rec', 'N/A')
    entry = signal.get('entry', 0)
    sl = signal.get('sl', 0)
    tp1 = signal.get('tp1', 0)
    tp2 = signal.get('tp2', 0)
    tp3 = signal.get('tp3', 0)
    tf = signal.get('tf', '1H')
    rr = signal.get('rr', 0)
    
    # أيقونة الجودة
    if quality_score >= 75:
        quality_icon = "🔥 HIGH"
    elif quality_score >= 50:
        quality_icon = "⚡ MEDIUM"
    else:
        quality_icon = "💡 LOW"
    
    # أيقونة نوع التوصية
    if "شراء" in rec:
        direction_icon = "🟢 BUY"
    elif "بيع" in rec:
        direction_icon = "🔴 SELL"
    else:
        direction_icon = "⚪ NEUTRAL"
    
    message = f"""
╔═══════════════════════╗
    {quality_icon} - {direction_icon}
╚═══════════════════════╝

💰 <b>{symbol}</b> | ⏰ {tf}

📊 <b>التوصية:</b> {rec}

🎯 <b>نقطة الدخول:</b> {entry:.5f}
🛑 <b>إيقاف الخسارة:</b> {sl:.5f}

✅ <b>أخذ الربح 1:</b> {tp1:.5f}
✅ <b>أخذ الربح 2:</b> {tp2:.5f}
✅ <b>أخذ الربح 3:</b> {tp3:.5f}

📈 <b>نسبة المخاطرة/العائد:</b> {rr:.2f}:1

⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━
💎 <b>اشتراكك:</b> {user_plan}
━━━━━━━━━━━━━━━━━━━

⚠️ <b>تحذير:</b> التداول ينطوي على مخاطر
"""
    
    return message


def get_start_message():
    """رسالة البداية"""
    return """
🤖 <b>مرحباً بك في بوت التوصيات VIP</b> 🤖

نقدم لك توصيات تداول احترافية للفوركس والعملات الرقمية مع نظام متقدم للجودة!

━━━━━━━━━━━━━━━━━━━

📊 <b>ماذا نقدم؟</b>
✅ توصيات يومية مدروسة
✅ 3 مستويات لأخذ الربح
✅ نسبة مخاطرة/عائد ممتازة
✅ نظام تقييم جودة متقدم

━━━━━━━━━━━━━━━━━━━

🎯 <b>الأوامر المتاحة:</b>

/start - البداية
/plans - خطط الاشتراك
/subscribe - الاشتراك
/status - حالة اشتراكك
/referral - احصل على رابط الإحالة
/help - المساعدة

━━━━━━━━━━━━━━━━━━━

💡 ابدأ الآن واحصل على <b>3 أيام تجريبية مجاناً!</b>

👇 اضغط /plans لمشاهدة خطط الاشتراك
"""


def get_plans_message():
    """رسالة خطط الاشتراك"""
    return """
💎 <b>خطط اشتراك VIP</b> 💎

اختر الخطة المناسبة لك:

━━━━━━━━━━━━━━━━━━━

🥉 <b>BRONZE - $29/شهر</b>
✅ 10 توصيات يومياً
✅ توصيات جودة عالية (75+)
✅ دعم فني أساسي
✅ 3 أيام تجربة مجانية

━━━━━━━━━━━━━━━━━━━

🥈 <b>SILVER - $79/شهر</b>
✅ 30 توصية يومياً
✅ توصيات جودة متوسطة+ (50+)
✅ دعم فني ذهبي
✅ تحليلات إضافية

━━━━━━━━━━━━━━━━━━━

🥇 <b>GOLD - $149/شهر</b>
✅ 75 توصية يومياً
✅ جميع مستويات الجودة
✅ دعم VIP 24/7
✅ تقارير أسبوعية

━━━━━━━━━━━━━━━━━━━

💎 <b>PLATINUM - $499/شهر</b>
✅ توصيات غير محدودة
✅ جميع المميزات
✅ استشارات شخصية
✅ تحليل محفظة

━━━━━━━━━━━━━━━━━━━

🎁 <b>برنامج الإحالة:</b>
احصل على +30 يوم مجاناً لكل صديق تدعوه!

👉 اكتب /subscribe للاشتراك
"""


def get_status_message(user_id):
    """رسالة حالة الاشتراك"""
    try:
        sub_info = subscription_manager.check_subscription(user_id)
        
        if not sub_info.get('exists'):
            return "❌ لم يتم العثور على اشتراكك\n\nاكتب /subscribe للاشتراك"
        
        plan = sub_info.get('plan', 'free')
        status = sub_info.get('status', 'unknown')
        start_date = sub_info.get('start_date', 'N/A')
        end_date = sub_info.get('end_date', 'N/A')
        days_left = sub_info.get('days_left', 0)
        plan_details = sub_info.get('plan_details', {})
        daily_limit = plan_details.get('signals_per_day', 0)
        
        # حساب التوصيات اليوم
        import sqlite3
        conn = sqlite3.connect('vip_subscriptions.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM signals_sent 
            WHERE user_id = ? AND DATE(sent_at) = DATE('now')
        ''', (user_id,))
        signals_today = cursor.fetchone()[0]
        conn.close()
        
        status_icon = "✅" if status == "active" else "⏸️"
        
        message = f"""
{status_icon} <b>حالة اشتراكك</b>

━━━━━━━━━━━━━━━━━━━

💎 <b>الخطة:</b> {plan.upper()}
📊 <b>الحالة:</b> {status}
⏰ <b>تاريخ البداية:</b> {start_date}
📅 <b>تاريخ الانتهاء:</b> {end_date}
⏳ <b>الأيام المتبقية:</b> {days_left} يوم

━━━━━━━━━━━━━━━━━━━

📈 <b>الاستخدام اليوم:</b>
{signals_today} / {daily_limit} توصية

━━━━━━━━━━━━━━━━━━━

💡 <b>اكتب /plans لترقية اشتراكك</b>
🔗 <b>اكتب /referral لدعوة أصدقائك</b>
"""
        
        return message
        
    except Exception as e:
        return f"❌ خطأ في جلب البيانات: {e}"


def get_referral_message(user_id):
    """رسالة رابط الإحالة"""
    sub_info = subscription_manager.check_subscription(user_id)
    referral_code = sub_info.get('referral_code', 'N/A')
    
    # حساب عدد الإحالات
    import sqlite3
    conn = sqlite3.connect('vip_subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM referrals WHERE referrer_id = ?
    ''', (user_id,))
    referral_count = cursor.fetchone()[0]
    conn.close()
    
    return f"""
🎁 <b>برنامج الإحالة</b> 🎁

━━━━━━━━━━━━━━━━━━━

رابطك الخاص:
<code>https://t.me/YourBotUsername?start={referral_code}</code>

━━━━━━━━━━━━━━━━━━━

👥 <b>عدد الإحالات:</b> {referral_count}

💰 <b>المكافأة:</b>
احصل على +30 يوم مجاني لكل صديق يشترك!

━━━━━━━━━━━━━━━━━━━

📤 شارك الرابط مع أصدقائك الآن!
"""


def handle_subscribe_command(user_id, username, referrer_id=None):
    """التعامل مع أمر الاشتراك"""
    # التحقق من وجود المستخدم
    sub_info = subscription_manager.check_subscription(user_id)
    
    if sub_info.get('exists'):
        return "✅ أنت مشترك بالفعل!\n\nاكتب /status لمعرفة تفاصيل اشتراكك"
    
    # تسجيل مستخدم جديد
    success = subscription_manager.add_user(
        user_id=user_id,
        username=username or f"user_{user_id}",
        first_name="",
        referred_by_code=referrer_id
    )
    
    if success:
        message = f"""
🎉 <b>تم تفعيل حسابك!</b> 🎉

━━━━━━━━━━━━━━━━━━━

✅ الخطة: FREE
✅ 1 توصية يومياً مجاناً
✅ توصيات جودة متوسطة+

━━━━━━━━━━━━━━━━━━━

⏰ ابدأ باستقبال التوصيات الآن!

💎 للحصول على المزيد من التوصيات:
اكتب /plans
"""
        return message
    else:
        return "❌ حدث خطأ في التسجيل، حاول مرة أخرى"


def handle_callback(callback_query):
    """التعامل مع الأزرار التفاعلية"""
    data = callback_query.get('data', '')
    user_id = callback_query['from']['id']
    message_id = callback_query['message']['message_id']
    chat_id = callback_query['message']['chat']['id']
    
    if data.startswith('upgrade_'):
        plan = data.replace('upgrade_', '')
        # هنا يمكنك إضافة منطق الترقية والدفع
        response = f"""
💳 <b>ترقية الاشتراك - {plan.upper()}</b>

━━━━━━━━━━━━━━━━━━━

للترقية، يرجى إتمام الدفع عبر:

💳 PayPal: your_paypal@email.com
💰 Stripe: [رابط الدفع]
🏦 تحويل بنكي: [تفاصيل الحساب]

بعد الدفع، أرسل إثبات الدفع مع user ID الخاص بك:
<code>{user_id}</code>

سيتم تفعيل اشتراكك خلال 24 ساعة.
"""
        send_message(chat_id, response)


def process_update(update):
    """معالجة تحديثات التليجرام"""
    try:
        # رسالة نصية
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            username = message['from'].get('username', '')
            text = message.get('text', '')
            
            # التحقق من referral في /start
            referrer_id = None
            if text.startswith('/start '):
                referral_code = text.split(' ')[1]
                referrer_id = subscription_manager.get_user_by_referral(referral_code)
            
            # الأوامر
            if text == '/start' or text.startswith('/start'):
                response = get_start_message()
                send_message(chat_id, response)
                
            elif text == '/plans':
                response = get_plans_message()
                
                # أزرار تفاعلية للخطط
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🥉 BRONZE - $29", "callback_data": "upgrade_bronze"}],
                        [{"text": "🥈 SILVER - $79", "callback_data": "upgrade_silver"}],
                        [{"text": "🥇 GOLD - $149", "callback_data": "upgrade_gold"}],
                        [{"text": "💎 PLATINUM - $499", "callback_data": "upgrade_platinum"}]
                    ]
                }
                send_message(chat_id, response, reply_markup=keyboard)
                
            elif text == '/subscribe':
                response = handle_subscribe_command(user_id, username, referrer_id)
                send_message(chat_id, response)
                
            elif text == '/status':
                response = get_status_message(user_id)
                send_message(chat_id, response)
                
            elif text == '/referral':
                response = get_referral_message(user_id)
                send_message(chat_id, response)
                
            elif text == '/help':
                response = """
📚 <b>المساعدة</b>

<b>الأوامر المتاحة:</b>

/start - البداية والتعليمات
/plans - عرض خطط الاشتراك
/subscribe - الاشتراك (3 أيام مجاناً)
/status - معرفة حالة اشتراكك
/referral - الحصول على رابط الإحالة
/help - عرض هذه الرسالة

━━━━━━━━━━━━━━━━━━━

💡 <b>كيف يعمل البوت؟</b>

1️⃣ اشترك بـ /subscribe (تجربة مجانية)
2️⃣ ستصلك التوصيات تلقائياً
3️⃣ كل توصية تحتوي على:
   - نقطة دخول
   - وقف خسارة
   - 3 نقاط لأخذ الربح
   
━━━━━━━━━━━━━━━━━━━

❓ <b>للدعم الفني:</b>
تواصل معنا: @YourSupportHandle
"""
                send_message(chat_id, response)
        
        # Callback Query (الأزرار)
        elif 'callback_query' in update:
            handle_callback(update['callback_query'])
            
    except Exception as e:
        print(f"خطأ في معالجة التحديث: {e}")


def run_bot():
    """تشغيل البوت بشكل مستمر"""
    print("🤖 بدء تشغيل بوت التوصيات VIP...")
    print(f"🔗 Bot Token: {BOT_TOKEN[:20]}...")
    
    last_update_id = load_last_update()
    
    while True:
        try:
            url = f"{BASE_URL}/getUpdates"
            params = {
                'offset': last_update_id + 1,
                'timeout': 30
            }
            
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ok'):
                    updates = data.get('result', [])
                    
                    for update in updates:
                        last_update_id = update['update_id']
                        process_update(update)
                        save_last_update(last_update_id)
                    
                    if updates:
                        print(f"✅ معالجة {len(updates)} تحديث")
            else:
                print(f"❌ خطأ في الاتصال: {response.status_code}")
                time.sleep(5)
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout - إعادة المحاولة...")
            continue
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
            time.sleep(5)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════╗
║   بوت التوصيات VIP الموحد           ║
║   Unified VIP Signals Bot            ║
╚═══════════════════════════════════════╝
    """)
    
    run_bot()

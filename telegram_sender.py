"""
Telegram Sender Module
وحدة إرسال الرسائل عبر التليجرام - دعم البوتات المتعددة
"""
import os
import requests
import json
from pathlib import Path
from datetime import datetime
from vip_subscription_system import SubscriptionManager

# Settings
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
BOTS_CONFIG_FILE = Path(__file__).parent / "bots_config.json"

subscription_manager = SubscriptionManager()


def load_bots_config():
    """تحميل إعدادات البوتات"""
    try:
        if BOTS_CONFIG_FILE.exists():
            with open(BOTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"bots": []}
    except Exception as e:
        print(f"Error loading bots config: {e}")
        return {"bots": []}


def save_bots_config(config):
    """حفظ إعدادات البوتات"""
    try:
        with open(BOTS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving bots config: {e}")
        return False


def get_active_bots():
    """الحصول على البوتات النشطة"""
    config = load_bots_config()
    return [bot for bot in config.get('bots', []) if bot.get('status') == 'active']


def send_telegram_message(chat_id, text, parse_mode="HTML", bot_token=None):
    """
    إرسال رسالة إلى مستخدم معين
    Send message to specific user
    """
    if not bot_token:
        bot_token = BOT_TOKEN
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        return {
            'success': result.get('ok', False),
            'response': result
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_to_multiple_bots(chat_id, text, parse_mode="HTML", bot_ids=None):
    """
    إرسال رسالة عبر عدة بوتات
    Send message via multiple bots
    """
    active_bots = get_active_bots()
    
    # تصفية البوتات إذا تم تحديد IDs معينة
    if bot_ids:
        active_bots = [bot for bot in active_bots if bot.get('id') in bot_ids]
    
    results = []
    for bot in active_bots:
        result = send_telegram_message(chat_id, text, parse_mode, bot.get('token'))
        results.append({
            'bot_id': bot.get('id'),
            'bot_name': bot.get('name'),
            'success': result.get('success'),
            'error': result.get('error')
        })
    
    return results


def send_signal_to_subscribers(signal_data, quality_score=100):
    """
    إرسال إشارة إلى جميع المشتركين المؤهلين
    Send signal to all eligible subscribers
    """
    try:
        subscribers = subscription_manager.get_all_active_users()
        results = {
            'total_subscribers': len(subscribers),
            'sent_count': 0,
            'failed_count': 0,
            'details': []
        }
        
        # تنسيق رسالة الإشارة
        message = format_signal_message(signal_data)
        
        for user_data in subscribers:
            try:
                # Handle both dict and tuple formats
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                    plan = user_data.get('plan', 'free')
                else:
                    user_id = user_data[0]
                    plan = user_data[1] if len(user_data) > 1 else 'free'
                
                if not user_id:
                    continue
                
                # إرسال الرسالة
                result = send_telegram_message(user_id, message)
                
                if result['success']:
                    results['sent_count'] += 1
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'sent'
                    })
                else:
                    results['failed_count'] += 1
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'failed',
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['details'].append({
                    'user_id': user_id if 'user_id' in locals() else 'unknown',
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_recommendation_to_subscribers(recommendation_data):
    """
    إرسال توصية إلى جميع المشتركين
    Send recommendation to all subscribers
    """
    try:
        subscribers = subscription_manager.get_all_active_users()
        results = {
            'total_subscribers': len(subscribers),
            'sent_count': 0,
            'failed_count': 0,
            'details': []
        }
        
        # تنسيق رسالة التوصية
        message = format_recommendation_message(recommendation_data)
        
        for user_data in subscribers:
            try:
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                else:
                    user_id = user_data[0]
                
                if not user_id:
                    continue
                
                result = send_telegram_message(user_id, message)
                
                if result['success']:
                    results['sent_count'] += 1
                else:
                    results['failed_count'] += 1
                    
            except Exception as e:
                results['failed_count'] += 1
        
        return results
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_report_to_subscribers(report_text):
    """
    إرسال تقرير إلى جميع المشتركين
    Send report to all subscribers
    """
    try:
        subscribers = subscription_manager.get_all_active_users()
        results = {
            'total_subscribers': len(subscribers),
            'sent_count': 0,
            'failed_count': 0
        }
        
        for user_data in subscribers:
            try:
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                else:
                    user_id = user_data[0]
                
                if not user_id:
                    continue
                
                result = send_telegram_message(user_id, report_text)
                
                if result['success']:
                    results['sent_count'] += 1
                else:
                    results['failed_count'] += 1
                    
            except Exception as e:
                results['failed_count'] += 1
        
        return results
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def format_signal_message(signal):
    """تنسيق رسالة الإشارة - محسّن"""
    signal_type = signal.get('signal', signal.get('rec', 'N/A')).upper()
    signal_emoji = "🟢" if signal_type == 'BUY' else "🔴"
    signal_ar = "شراء BUY" if signal_type == 'BUY' else "بيع SELL"
    
    # حساب المسافات
    entry = float(signal.get('entry', 0))
    sl = float(signal.get('sl', 0))
    tp1 = float(signal.get('tp1', 0))
    tp2 = float(signal.get('tp2', signal.get('tp1', 0)))
    tp3 = float(signal.get('tp3', signal.get('tp1', 0)))
    
    sl_distance = abs(entry - sl)
    tp1_distance = abs(tp1 - entry)
    tp2_distance = abs(tp2 - entry) if tp2 else 0
    tp3_distance = abs(tp3 - entry) if tp3 else 0
    
    msg = f"""
╔═══════════════════════════
║ {signal_emoji} <b>إشارة تداول - TRADING SIGNAL</b>
╚═══════════════════════════

📊 <b>الزوج / Pair:</b> {signal.get('symbol', 'N/A')}
📈 <b>الاتجاه / Direction:</b> {signal_ar}
⏰ <b>الإطار / Timeframe:</b> {signal.get('timeframe', signal.get('tf', 'N/A'))}
⭐ <b>الجودة / Quality:</b> {signal.get('quality_score', 'N/A')}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>نقطة الدخول / Entry:</b>
   ▪️ {entry}

🛑 <b>وقف الخسارة / Stop Loss:</b>
   ▪️ {sl}
   📏 المسافة: {sl_distance:.4f} نقطة

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>أهداف الربح / Take Profit:</b>

   1️⃣ <b>الهدف الأول / TP1:</b>
      ▪️ {tp1}
      📏 +{tp1_distance:.4f} نقطة
      💡 أغلق 30% من الصفقة
"""
    
    if tp2 and tp2 != tp1:
        msg += f"""
   2️⃣ <b>الهدف الثاني / TP2:</b>
      ▪️ {tp2}
      📏 +{tp2_distance:.4f} نقطة
      💡 أغلق 40% من الصفقة
"""
    
    if tp3 and tp3 != tp1 and tp3 != tp2:
        msg += f"""
   3️⃣ <b>الهدف الثالث / TP3:</b>
      ▪️ {tp3}
      📏 +{tp3_distance:.4f} نقطة
      💡 أغلق باقي الصفقة 30%
"""
    
    msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ <b>تحذير:</b> لا تخاطر بأكثر من 2% من رأس المال
💼 <b>إدارة المخاطر:</b> استخدم حجم عقد مناسب

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {signal.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
"""
    return msg.strip()


def format_recommendation_message(rec):
    """تنسيق رسالة التوصية - محسّن"""
    signal_emoji = "🟢" if rec.get('signal', '').lower() == 'buy' else "🔴"
    signal_type = "شراء BUY" if rec.get('signal', '').lower() == 'buy' else "بيع SELL"
    
    # حساب المسافات
    entry = float(rec.get('entry', 0))
    sl = float(rec.get('sl', 0))
    tp1 = float(rec.get('tp1', 0))
    tp2 = float(rec.get('tp2', 0))
    tp3 = float(rec.get('tp3', 0))
    
    sl_distance = abs(entry - sl)
    tp1_distance = abs(tp1 - entry)
    tp2_distance = abs(tp2 - entry)
    tp3_distance = abs(tp3 - entry)
    
    msg = f"""
╔═══════════════════════════
║ {signal_emoji} <b>توصية جديدة - NEW SIGNAL</b>
╚═══════════════════════════

📊 <b>الزوج / Pair:</b> {rec.get('pair', 'N/A')}
📈 <b>الإشارة / Signal:</b> {signal_type}
⏰ <b>الإطار الزمني / Timeframe:</b> {rec.get('timeframe', 'N/A')}
⭐ <b>جودة الإشارة / Quality:</b> {rec.get('quality_score', 'N/A')}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>نقطة الدخول / Entry Point:</b>
   ▪️ {entry}

🛑 <b>وقف الخسارة / Stop Loss:</b>
   ▪️ {sl}
   📏 المسافة: {sl_distance:.4f} نقطة

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>أهداف الربح / Take Profit Levels:</b>

   1️⃣ <b>الهدف الأول / TP1:</b>
      ▪️ {tp1}
      📏 المسافة: {tp1_distance:.4f} نقطة
      💡 أغلق 30% من الصفقة

   2️⃣ <b>الهدف الثاني / TP2:</b>
      ▪️ {tp2}
      📏 المسافة: {tp2_distance:.4f} نقطة
      💡 أغلق 40% من الصفقة

   3️⃣ <b>الهدف الثالث / TP3:</b>
      ▪️ {tp3}
      📏 المسافة: {tp3_distance:.4f} نقطة
      💡 أغلق باقي الصفقة 30%

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>ملاحظات / Notes:</b>
{rec.get('reason', '• تحليل فني متقدم\n• اتبع إدارة المخاطر')}

⚠️ <b>تحذير:</b> لا تخاطر بأكثر من 2% من رأس المال

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {rec.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
"""
    return msg.strip()

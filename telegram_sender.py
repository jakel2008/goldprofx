"""
Telegram Sender Module
وحدة إرسال الرسائل عبر التليجرام - دعم البوتات المتعددة
"""
import os
import importlib
import requests
import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
try:
    _subscription_mod = importlib.import_module("vip_subscription_system")
    SubscriptionManager = getattr(_subscription_mod, "SubscriptionManager")
except Exception:  # Fallback for missing dependency
    class SubscriptionManager:  # type: ignore
        def get_all_active_users(self):
            return []

        def can_receive_signal(self, user_id, signal_quality_bucket):
            return False, "subscription system unavailable"

        def log_signal_sent(self, user_id, signal_data, signal_quality_bucket):
            return False

# Settings
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

_default_data_dir = Path('/var/data') if Path('/var/data').exists() else Path(__file__).parent
DATA_DIR = Path(os.environ.get('GOLDPRO_DATA_DIR', str(_default_data_dir)))
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

BOTS_CONFIG_FILE = Path(os.environ.get('BOTS_CONFIG_FILE', str(DATA_DIR / 'bots_config.json')))
BROADCAST_TARGETS_FILE = Path(os.environ.get('BROADCAST_TARGETS_FILE', str(DATA_DIR / 'broadcast_targets.json')))
SITE_SETTINGS_FILE = Path(os.environ.get('SITE_SETTINGS_FILE', str(DATA_DIR / 'site_settings.json')))


def _migrate_legacy_json_file(target_path):
    """One-time migration from repo-root json file to persistent data dir."""
    try:
        target = Path(str(target_path))
        legacy = Path(__file__).parent / target.name
        if target.exists() or (not legacy.exists()):
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(legacy), str(target))
    except Exception:
        pass

subscription_manager = SubscriptionManager()

_migrate_legacy_json_file(BOTS_CONFIG_FILE)
_migrate_legacy_json_file(BROADCAST_TARGETS_FILE)
_migrate_legacy_json_file(SITE_SETTINGS_FILE)


def _ensure_delivery_audit_table():
    try:
        db_path = getattr(subscription_manager, 'db_path', 'vip_subscriptions.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS delivery_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan TEXT,
                content_type TEXT,
                quality_score INTEGER,
                quality_bucket TEXT,
                status TEXT,
                reason TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception:
        pass


def _log_delivery_audit(user_id, plan, content_type, quality_score, quality_bucket, status, reason=''):
    try:
        db_path = getattr(subscription_manager, 'db_path', 'vip_subscriptions.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO delivery_audit
            (user_id, plan, content_type, quality_score, quality_bucket, status, reason, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(user_id) if user_id is not None else None,
            str(plan or ''),
            str(content_type or ''),
            int(quality_score) if quality_score is not None else None,
            str(quality_bucket or ''),
            str(status or ''),
            str(reason or ''),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


_ensure_delivery_audit_table()


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


def _get_active_bot_tokens():
    """إرجاع توكنات البوتات النشطة الصالحة للإرسال."""
    tokens = []
    for bot in get_active_bots():
        token = str(bot.get('token', '')).strip()
        if token:
            tokens.append(token)

    if not tokens and str(BOT_TOKEN or '').strip():
        tokens = [BOT_TOKEN]

    return tokens


def load_broadcast_targets():
    """تحميل أهداف البث الخارجية (قنوات تيليجرام / واتساب Webhook)."""
    try:
        if BROADCAST_TARGETS_FILE.exists():
            with open(BROADCAST_TARGETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f) or {}
            if isinstance(data, dict):
                targets = data.get('targets')
                if isinstance(targets, list):
                    return {'targets': targets}
        return {'targets': []}
    except Exception:
        return {'targets': []}


def _load_recommendation_footer_settings():
    """قراءة الرسالة والرابط المنفصلين أسفل التوصيات من إعدادات الموقع."""
    try:
        if not SITE_SETTINGS_FILE.exists():
            return {'enabled': True, 'message': '', 'link': ''}
        with open(SITE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
        if not isinstance(data, dict):
            return {'enabled': True, 'message': '', 'link': ''}
        footer_enabled = data.get('recommendation_footer_enabled', True)
        if isinstance(footer_enabled, str):
            footer_enabled = footer_enabled.strip().lower() in ('1', 'true', 'yes', 'on')
        footer_message = str(data.get('recommendation_footer_message') or '').strip()
        footer_link = str(data.get('recommendation_footer_link') or '').strip()
        return {'enabled': bool(footer_enabled), 'message': footer_message, 'link': footer_link}
    except Exception:
        return {'enabled': True, 'message': '', 'link': ''}


def save_broadcast_targets(config):
    """حفظ أهداف البث الخارجية."""
    try:
        if not isinstance(config, dict):
            return False
        targets = config.get('targets', [])
        if not isinstance(targets, list):
            return False
        with open(BROADCAST_TARGETS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'targets': targets}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _send_to_telegram_target(text, parse_mode, target):
    """إرسال رسالة إلى قناة/جروب تيليجرام عبر البوتات النشطة."""
    chat_id = str(target.get('chat_id') or target.get('telegram_chat_id') or '').strip()
    if not chat_id:
        return {'success': False, 'sent_count': 0, 'failed_count': 1, 'error': 'missing telegram chat_id'}

    bot_mode = str(target.get('bot_mode') or 'all_active').strip().lower()
    tokens = _get_active_bot_tokens()
    if bot_mode == 'single' and tokens:
        tokens = tokens[:1]

    sent_count = 0
    failed_count = 0
    details = []

    for token in tokens:
        result = send_telegram_message(chat_id, text, parse_mode=parse_mode, bot_token=token)
        if result.get('success'):
            sent_count += 1
            details.append({'status': 'sent'})
        else:
            failed_count += 1
            details.append({'status': 'failed', 'error': result.get('error')})

    return {
        'success': sent_count > 0,
        'sent_count': sent_count,
        'failed_count': failed_count,
        'details': details
    }


def _send_to_whatsapp_target(text, target):
    """إرسال رسالة واتساب عبر Webhook/API خارجي مخصص."""
    webhook_url = str(target.get('webhook_url') or target.get('url') or '').strip()
    if not webhook_url:
        return {'success': False, 'sent_count': 0, 'failed_count': 1, 'error': 'missing whatsapp webhook_url'}

    headers = {'Content-Type': 'application/json'}
    auth_token = str(target.get('auth_token') or '').strip()
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'

    payload = {
        'message': text,
        'group_id': target.get('group_id') or target.get('to') or '',
        'name': target.get('name') or 'whatsapp-target'
    }

    try:
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=12)
        ok = response.status_code >= 200 and response.status_code < 300
        return {
            'success': ok,
            'sent_count': 1 if ok else 0,
            'failed_count': 0 if ok else 1,
            'status_code': response.status_code,
            'error': None if ok else response.text[:500]
        }
    except Exception as e:
        return {'success': False, 'sent_count': 0, 'failed_count': 1, 'error': str(e)}


def send_broadcast_to_configured_targets(text, parse_mode='HTML'):
    """إرسال رسالة إلى أهداف البث المفعلة (Telegram targets + WhatsApp targets)."""
    config = load_broadcast_targets()
    targets = config.get('targets', []) if isinstance(config, dict) else []

    enabled_targets = [t for t in targets if isinstance(t, dict) and t.get('enabled', True)]
    results = {
        'total_targets': len(enabled_targets),
        'sent_count': 0,
        'failed_count': 0,
        'details': []
    }

    # Fallback مهم للإنتاج: إذا لا توجد أهداف بث مفعلة،
    # نرسل إلى chat id الافتراضي من البيئة حتى لا يتوقف النشر بالكامل.
    if not enabled_targets:
        fallback_chat_id = str(os.environ.get('MM_TELEGRAM_CHAT_ID', '') or '').strip()
        if fallback_chat_id:
            fallback_result = send_telegram_message(fallback_chat_id, text, parse_mode=parse_mode)
            sent = 1 if fallback_result.get('success') else 0
            failed = 0 if fallback_result.get('success') else 1
            results['sent_count'] += sent
            results['failed_count'] += failed
            results['details'].append({
                'name': 'MM_TELEGRAM_CHAT_ID',
                'platform': 'telegram_fallback',
                'success': bool(fallback_result.get('success', False)),
                'sent_count': sent,
                'failed_count': failed,
                'error': fallback_result.get('error')
            })
        return results

    for target in enabled_targets:
        platform = str(target.get('platform') or target.get('type') or 'telegram').strip().lower()
        name = str(target.get('name') or platform)

        if platform in ('telegram', 'telegram_channel', 'telegram_group'):
            res = _send_to_telegram_target(text, parse_mode, target)
        elif platform in ('whatsapp', 'whatsapp_group'):
            res = _send_to_whatsapp_target(text, target)
        else:
            res = {'success': False, 'sent_count': 0, 'failed_count': 1, 'error': f'unsupported platform: {platform}'}

        results['sent_count'] += int(res.get('sent_count', 0) or 0)
        results['failed_count'] += int(res.get('failed_count', 0) or 0)
        results['details'].append({
            'name': name,
            'platform': platform,
            'success': bool(res.get('success', False)),
            'sent_count': int(res.get('sent_count', 0) or 0),
            'failed_count': int(res.get('failed_count', 0) or 0),
            'error': res.get('error')
        })

    return results


def send_telegram_message(chat_id, text, parse_mode="HTML", bot_token=None):
    """
    إرسال رسالة إلى مستخدم معين
    Send message to specific user
    """
    if not bot_token:
        bot_token = BOT_TOKEN

    chat_id = str(chat_id or '').strip()
    if not chat_id:
        config = load_broadcast_targets()
        targets = config.get('targets', []) if isinstance(config, dict) else []
        for item in targets:
            if not isinstance(item, dict):
                continue
            if not item.get('enabled', True):
                continue
            platform = str(item.get('platform') or item.get('type') or '').strip().lower()
            if platform not in ('telegram', 'telegram_channel', 'telegram_group'):
                continue
            candidate = str(item.get('chat_id') or item.get('telegram_chat_id') or '').strip()
            if candidate:
                chat_id = candidate
                break

    if not chat_id:
        return {
            'success': False,
            'error': 'missing telegram chat_id'
        }
    
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
        bot_tokens = _get_active_bot_tokens()
        
        plan_quality_threshold = {
            'free': 90,
            'bronze': 80,
            'silver': 70,
            'gold': 60,
            'platinum': 50
        }

        signal_quality_bucket = 'high'
        if quality_score < 70:
            signal_quality_bucket = 'low'
        elif quality_score < 85:
            signal_quality_bucket = 'medium'

        for user_data in subscribers:
            try:
                # Handle both dict and tuple formats
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                    plan = user_data.get('plan', 'free')
                    chat_id = user_data.get('chat_id') or user_data.get('telegram_id') or user_id
                else:
                    user_id = user_data[0]
                    plan = user_data[1] if len(user_data) > 1 else 'free'
                    chat_id = user_id
                
                if not user_id:
                    continue

                # فلترة حسب الخطة والجودة
                min_quality = plan_quality_threshold.get(plan, 90)
                if quality_score < min_quality:
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'skipped_quality',
                        'reason': f'min_quality={min_quality}, signal_quality={quality_score}'
                    })
                    _log_delivery_audit(user_id, plan, 'signal', quality_score, signal_quality_bucket, 'skipped_quality', f'min_quality={min_quality}, signal_quality={quality_score}')
                    continue

                # احترام الحد اليومي من نظام الاشتراكات
                can_receive, reason = subscription_manager.can_receive_signal(user_id, signal_quality_bucket)
                if not can_receive:
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'skipped_plan_limit',
                        'reason': reason
                    })
                    _log_delivery_audit(user_id, plan, 'signal', quality_score, signal_quality_bucket, 'skipped_plan_limit', reason)
                    continue
                
                # إرسال الرسالة عبر البوتات الفعالة (توزيع بالتناوب)
                selected_token = bot_tokens[results['sent_count'] % len(bot_tokens)] if bot_tokens else None
                result = send_telegram_message(chat_id, message, bot_token=selected_token)
                
                if result['success']:
                    subscription_manager.log_signal_sent(user_id, signal_data, signal_quality_bucket)
                    results['sent_count'] += 1
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'sent'
                    })
                    _log_delivery_audit(user_id, plan, 'signal', quality_score, signal_quality_bucket, 'sent', '')
                else:
                    results['failed_count'] += 1
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'failed',
                        'error': result.get('error', 'Unknown error')
                    })
                    _log_delivery_audit(user_id, plan, 'signal', quality_score, signal_quality_bucket, 'failed', result.get('error', 'Unknown error'))
                    
            except Exception as e:
                results['failed_count'] += 1
                results['details'].append({
                    'user_id': user_id if 'user_id' in locals() else 'unknown',
                    'status': 'error',
                    'error': str(e)
                })
                _log_delivery_audit(user_id if 'user_id' in locals() else None, plan if 'plan' in locals() else '', 'signal', quality_score, signal_quality_bucket, 'error', str(e))
        
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
        bot_tokens = _get_active_bot_tokens()

        sent_counter = 0

        plan_quality_threshold = {
            'free': 90,
            'bronze': 80,
            'silver': 70,
            'gold': 60,
            'platinum': 50
        }

        quality_score = 85
        try:
            quality_score = int(
                recommendation_data.get('quality_score')
                or recommendation_data.get('quality')
                or recommendation_data.get('confidence')
                or 85
            )
        except Exception:
            quality_score = 85

        signal_quality_bucket = 'high'
        if quality_score < 70:
            signal_quality_bucket = 'low'
        elif quality_score < 85:
            signal_quality_bucket = 'medium'
        
        for user_data in subscribers:
            try:
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                    plan = user_data.get('plan', 'free')
                    chat_id = user_data.get('chat_id') or user_data.get('telegram_id') or user_id
                else:
                    user_id = user_data[0]
                    plan = user_data[1] if len(user_data) > 1 else 'free'
                    chat_id = user_id
                
                if not user_id:
                    continue

                min_quality = plan_quality_threshold.get(plan, 90)
                if quality_score < min_quality:
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'skipped_quality',
                        'reason': f'min_quality={min_quality}, rec_quality={quality_score}'
                    })
                    _log_delivery_audit(user_id, plan, 'recommendation', quality_score, signal_quality_bucket, 'skipped_quality', f'min_quality={min_quality}, rec_quality={quality_score}')
                    continue

                can_receive, reason = subscription_manager.can_receive_signal(user_id, signal_quality_bucket)
                if not can_receive:
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'skipped_plan_limit',
                        'reason': reason
                    })
                    _log_delivery_audit(user_id, plan, 'recommendation', quality_score, signal_quality_bucket, 'skipped_plan_limit', reason)
                    continue
                
                selected_token = bot_tokens[sent_counter % len(bot_tokens)] if bot_tokens else None
                result = send_telegram_message(chat_id, message, bot_token=selected_token)
                
                if result['success']:
                    sent_counter += 1
                    results['sent_count'] += 1
                    subscription_manager.log_signal_sent(user_id, recommendation_data, signal_quality_bucket)
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'sent'
                    })
                    _log_delivery_audit(user_id, plan, 'recommendation', quality_score, signal_quality_bucket, 'sent', '')
                else:
                    results['failed_count'] += 1
                    results['details'].append({
                        'user_id': user_id,
                        'plan': plan,
                        'status': 'failed',
                        'error': result.get('error', 'Unknown error')
                    })
                    _log_delivery_audit(user_id, plan, 'recommendation', quality_score, signal_quality_bucket, 'failed', result.get('error', 'Unknown error'))
                    
            except Exception as e:
                results['failed_count'] += 1
                results['details'].append({
                    'user_id': user_id if 'user_id' in locals() else 'unknown',
                    'status': 'error',
                    'error': str(e)
                })
                _log_delivery_audit(user_id if 'user_id' in locals() else None, plan if 'plan' in locals() else '', 'recommendation', quality_score, signal_quality_bucket, 'error', str(e))
        
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
        bot_tokens = _get_active_bot_tokens()
        sent_counter = 0
        
        for user_data in subscribers:
            try:
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                else:
                    user_id = user_data[0]
                
                if not user_id:
                    continue
                
                selected_token = bot_tokens[sent_counter % len(bot_tokens)] if bot_tokens else None
                result = send_telegram_message(user_id, report_text, bot_token=selected_token)
                
                if result['success']:
                    sent_counter += 1
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
    rr_tp1 = 0.0
    if sl_distance > 0:
        rr_tp1 = round(tp1_distance / sl_distance, 2)

    confidence_text = signal.get('confidence', 'N/A')
    follow_up_status = signal.get('follow_up_status', 'active')
    adaptive_mode = signal.get('adaptive_mode', '')
    adaptive_min_quality = signal.get('adaptive_min_quality_score', '')
    adaptive_min_rr = signal.get('adaptive_min_rr', '')
    
    msg = f"""
╔═══════════════════════════
║ {signal_emoji} <b>إشارة تداول - TRADING SIGNAL</b>
╚═══════════════════════════

📊 <b>الزوج / Pair:</b> {signal.get('symbol', 'N/A')}
📈 <b>الاتجاه / Direction:</b> {signal_ar}
⏰ <b>الإطار / Timeframe:</b> {signal.get('timeframe', signal.get('tf', 'N/A'))}
⭐ <b>الجودة / Quality:</b> {signal.get('quality_score', 'N/A')}/100
📐 <b>العائد/المخاطرة TP1:</b> 1:{rr_tp1}
🔰 <b>الثقة / Confidence:</b> {confidence_text}
🧭 <b>المتابعة / Follow-up:</b> {follow_up_status}
🧠 <b>وضع الفلترة / Adaptive:</b> {adaptive_mode or 'baseline'}

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
🔒 <b>خطة المتابعة:</b> بعد TP1 يتم نقل وقف الخسارة للتعادل، وبعد TP2 يتم تأمين ربح عند TP1
📊 <b>حدود القبول:</b> جودة≥{adaptive_min_quality or 'N/A'} | RR≥{adaptive_min_rr or 'N/A'}

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
    footer_settings = _load_recommendation_footer_settings()
    footer_enabled = bool(footer_settings.get('enabled', True))
    footer_message = footer_settings.get('message', '')
    footer_link = footer_settings.get('link', '')
    
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

{f"📝 <b>رسالة إضافية:</b>\n{footer_message}\n" if footer_enabled and footer_message else ""}
{f"🔗 <b>رابط إضافي:</b>\n{footer_link}\n" if footer_enabled and footer_link else ""}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 {rec.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
"""
    return msg.strip()

# ============ صفحة استرجاع كلمة المرور ============


import secrets
import smtplib
from email.mime.text import MIMEText
import hashlib
import importlib.util
import sys
from pathlib import Path
import os  # <-- Add this line
import threading
import time
import shutil
import xml.etree.ElementTree as ET
import csv
from io import StringIO

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response, abort, send_from_directory
import sqlite3
from werkzeug.utils import secure_filename
import requests
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader
# ============== Bot Management Routes ==============

# Define CHAT_ID for bot test send (replace with your actual chat id)
CHAT_ID = os.environ.get('MM_TELEGRAM_CHAT_ID', '')
from functools import wraps, lru_cache
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

# --- Fix ImportError for vip_subscription_system ---
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# --- Fix ImportError for vip_subscription_system ---
try:
    import vip_subscription_system # type: ignore
except ImportError as e:
    print(f"[ERROR] Could not import vip_subscription_system: {e}")
    # Optionally, you can raise or handle as needed
    raise

try:

    try:

        # --- Fix ImportError for user_manager ---
        try:

            # --- Fix ImportError for user_manager ---
            try:

                # --- Fix ImportError for user_manager ---
                try:
                    from user_manager import user_manager # type: ignore
                except ImportError:
                    import importlib.util
                    import sys
                    from pathlib import Path
                    user_manager_path = Path(__file__).parent / 'user_manager.py'
                    spec = importlib.util.spec_from_file_location('user_manager', str(user_manager_path))
                    user_manager_module = importlib.util.module_from_spec(spec)
                    sys.modules['user_manager'] = user_manager_module
                    spec.loader.exec_module(user_manager_module)
                    user_manager = user_manager_module.user_manager
            except ImportError:
                import importlib.util
                import sys
                from pathlib import Path
                user_manager_path = Path(__file__).parent / 'user_manager.py'
                spec = importlib.util.spec_from_file_location('user_manager', str(user_manager_path))
                user_manager_module = importlib.util.module_from_spec(spec)
                sys.modules['user_manager'] = user_manager_module
                spec.loader.exec_module(user_manager_module)
                user_manager = user_manager_module.user_manager
        except ImportError:
            import importlib.util
            import sys
            from pathlib import Path
            user_manager_path = Path(__file__).parent / 'user_manager.py'
            spec = importlib.util.spec_from_file_location('user_manager', str(user_manager_path))
            user_manager_module = importlib.util.module_from_spec(spec)
            sys.modules['user_manager'] = user_manager_module
            spec.loader.exec_module(user_manager_module)
            user_manager = user_manager_module.user_manager
    except ImportError:
        # Try relative import if direct import fails
        import importlib.util
        import sys
        from pathlib import Path
        user_manager_path = Path(__file__).parent / 'user_manager.py'
        spec = importlib.util.spec_from_file_location('user_manager', str(user_manager_path))
        user_manager_module = importlib.util.module_from_spec(spec)
        sys.modules['user_manager'] = user_manager_module
        spec.loader.exec_module(user_manager_module)
        user_manager = user_manager_module.user_manager
except ImportError:
    # Try relative import if direct import fails
    import importlib.util
    import sys
    from pathlib import Path
    user_manager_path = Path(__file__).parent / 'user_manager.py'
    spec = importlib.util.spec_from_file_location('user_manager', str(user_manager_path))
    user_manager_module = importlib.util.module_from_spec(spec)
    sys.modules['user_manager'] = user_manager_module
    spec.loader.exec_module(user_manager_module)
    user_manager = user_manager_module.user_manager
from email_service import email_service  # type: ignore
import telegram_sender  # type: ignore
try:
    from generate_daily_delivery_csv import fetch_rows as fetch_delivery_rows, write_csv as write_delivery_csv  # type: ignore
except Exception:
    fetch_delivery_rows = None  # type: ignore
    write_delivery_csv = None  # type: ignore
try:
    from telegram_command_bot import TelegramCommandBot  # type: ignore
except Exception:
    TelegramCommandBot = None  # type: ignore

# استيراد قائمة الروابط المركزية
import sys
sys.path.append(str(Path(__file__).parent / 'templates'))
# دعم إخراج UTF-8 للكونسول على ويندوز
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
try:
    import site_links # pyright: ignore[reportMissingImports]
except Exception:
    site_links.links = []

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-to-random-string'

MY_FOREX_BASE_PATH = os.environ.get('MY_FOREX_BASE_PATH', '/forex-app').rstrip('/') or '/forex-app'
# البحث أولاً داخل المشروع (للإنتاج)، ثم المجلد المجاور (للتطوير المحلي)
_my_forex_local = Path(__file__).resolve().parent / 'my-forex-app'
_my_forex_sibling = Path(__file__).resolve().parent.parent / 'my-forex-app'
MY_FOREX_APP_DIR = Path(os.environ.get('MY_FOREX_APP_DIR', str(_my_forex_local if _my_forex_local.exists() else _my_forex_sibling)))
MY_FOREX_TEMPLATES_DIR = MY_FOREX_APP_DIR / 'templates'

if MY_FOREX_TEMPLATES_DIR.exists():
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        PrefixLoader({'my_forex': FileSystemLoader(str(MY_FOREX_TEMPLATES_DIR))}),
    ])

ADMIN_USERNAME = 'jakel2008'
ADMIN_PASSWORD = 'JAKEL2008'
EMAIL_ACTIVATION_REQUIRED = os.environ.get('EMAIL_ACTIVATION_REQUIRED', '0').strip().lower() in ('1', 'true', 'yes', 'on')
ONLINE_ACTIVITY_WINDOW_MINUTES = max(1, int(os.environ.get('ONLINE_ACTIVITY_WINDOW_MINUTES', '5')))
LAST_SEEN_TOUCH_THROTTLE_SECONDS = max(15, int(os.environ.get('LAST_SEEN_TOUCH_THROTTLE_SECONDS', '60')))

TELEGRAM_COMMAND_BOT_ENABLED = os.environ.get('TELEGRAM_COMMAND_BOT_ENABLED', '1').strip().lower() in ('1', 'true', 'yes', 'on')
TELEGRAM_COMMAND_BOT = TelegramCommandBot(Path(__file__).parent) if TelegramCommandBot else None
BACKGROUND_SERVICES_ENABLED = os.environ.get('BACKGROUND_SERVICES_ENABLED', '1').strip().lower() in ('1', 'true', 'yes', 'on')
BACKGROUND_SERVICES_BOOTSTRAPPED = False
BACKGROUND_SERVICES_BOOTSTRAP_IN_PROGRESS = False
BACKGROUND_SERVICES_BOOTSTRAP_THREAD = None
BACKGROUND_SERVICES_BOOTSTRAP_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def load_my_forex_module():
    """تحميل تطبيق My Forex داخل النظام الرئيسي دون تشغيل خادم منفصل."""
    app_path = MY_FOREX_APP_DIR / 'app.py'
    if not app_path.exists():
        raise FileNotFoundError(f'My Forex app.py not found at {app_path}')

    if str(MY_FOREX_APP_DIR) not in sys.path:
        sys.path.insert(0, str(MY_FOREX_APP_DIR))

    module_name = 'integrated_my_forex_app'
    existing_module = sys.modules.get(module_name)
    if existing_module is not None:
        return existing_module

    spec = importlib.util.spec_from_file_location(module_name, str(app_path))
    if spec is None or spec.loader is None:
        raise ImportError(f'Unable to load My Forex application from {app_path}')

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def build_my_forex_context(selected_symbol='EURUSD', selected_interval='1h', include_all_option=False):
    module = load_my_forex_module()
    return {
        'symbol_options': [
            {'value': symbol, 'label': info['label']}
            for symbol, info in module.SUPPORTED_SYMBOLS.items()
        ],
        'grouped_symbol_options': module.build_grouped_symbol_options(include_all_option=include_all_option),
        'interval_options': list(module.SUPPORTED_INTERVALS.keys()),
        'selected_symbol': selected_symbol,
        'selected_interval': selected_interval,
        'symbol_count': len(module.SUPPORTED_SYMBOLS),
        'interval_count': len(module.SUPPORTED_INTERVALS),
        'main_site_url': '/',
        'return_to_param': quote('/', safe=''),
        'forex_base_path': MY_FOREX_BASE_PATH,
    }


def start_telegram_command_bot():
    """تشغيل بوت الأوامر في Thread مستقل بدون التأثير على الويب."""
    if not TELEGRAM_COMMAND_BOT_ENABLED:
        return False, 'telegram command bot disabled'
    if TELEGRAM_COMMAND_BOT is None:
        return False, 'telegram command bot module unavailable'
    try:
        return TELEGRAM_COMMAND_BOT.start()
    except Exception as e:
        return False, str(e)


def _bootstrap_background_services_once():
    """تشغيل خدمات الخلفية خارج مسار الطلب حتى لا تحجب الاستجابة الأولى."""
    global BACKGROUND_SERVICES_BOOTSTRAPPED, BACKGROUND_SERVICES_BOOTSTRAP_IN_PROGRESS

    try:
        try:
            start_continuous_analyzer(interval_seconds=CONTINUOUS_ANALYZER_INTERVAL_DEFAULT)
        except Exception:
            pass

        try:
            start_cleanup_scheduler(interval_seconds=CLEANUP_INTERVAL_DEFAULT)
        except Exception:
            pass

        try:
            start_delivery_report_scheduler(
                daily_time=DELIVERY_REPORT_DAILY_TIME,
                check_interval_seconds=DELIVERY_REPORT_CHECK_INTERVAL_SECONDS
            )
        except Exception:
            pass

        try:
            if TELEGRAM_COMMAND_BOT_ENABLED and TELEGRAM_COMMAND_BOT is not None:
                start_telegram_command_bot()
        except Exception:
            pass
    finally:
        with BACKGROUND_SERVICES_BOOTSTRAP_LOCK:
            BACKGROUND_SERVICES_BOOTSTRAPPED = True
            BACKGROUND_SERVICES_BOOTSTRAP_IN_PROGRESS = False


def _schedule_background_services_bootstrap():
    """جدولة تشغيل خدمات الخلفية بشكل غير حاجب للاستجابة."""
    global BACKGROUND_SERVICES_BOOTSTRAP_IN_PROGRESS, BACKGROUND_SERVICES_BOOTSTRAP_THREAD

    if not BACKGROUND_SERVICES_ENABLED or BACKGROUND_SERVICES_BOOTSTRAPPED:
        return False

    with BACKGROUND_SERVICES_BOOTSTRAP_LOCK:
        if BACKGROUND_SERVICES_BOOTSTRAPPED or BACKGROUND_SERVICES_BOOTSTRAP_IN_PROGRESS:
            return False

        BACKGROUND_SERVICES_BOOTSTRAP_IN_PROGRESS = True
        BACKGROUND_SERVICES_BOOTSTRAP_THREAD = threading.Thread(
            target=_bootstrap_background_services_once,
            daemon=True,
            name='background-services-bootstrap'
        )
        BACKGROUND_SERVICES_BOOTSTRAP_THREAD.start()
        return True


@app.route('/healthz')
def healthz():
    return jsonify({'ok': True}), 200


def _is_local_admin_session():
    return session.get('local_admin_username') == ADMIN_USERNAME

# ============ صفحة استرجاع كلمة المرور ============
def ensure_password_reset_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT,
            used INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.commit()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============ صفحة إعادة تعيين كلمة المرور ============
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT user_id, expires_at, used FROM password_resets WHERE token = ?', (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        return render_template('reset_password.html', error='الرابط غير صالح أو منتهي.')
    user_id, expires_at, used = row
    if used:
        conn.close()
        return render_template('reset_password.html', error='تم استخدام الرابط بالفعل.')
    if datetime.fromisoformat(expires_at) < datetime.now():
        conn.close()
        return render_template('reset_password.html', error='انتهت صلاحية الرابط.')
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if not password or len(password) < 6:
            return render_template('reset_password.html', error='كلمة المرور يجب أن تكون 6 أحرف على الأقل.')
        if password != confirm:
            return render_template('reset_password.html', error='كلمتا المرور غير متطابقتين.')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        c.execute('UPDATE password_resets SET used = 1 WHERE token = ?', (token,))
        conn.commit()
        conn.close()
        return render_template('reset_password.html', success='تم تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.')
    conn.close()
    return render_template('reset_password.html')

# ============ صفحة استرجاع كلمة المرور ============
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            return render_template('forgot_password.html', error='يرجى إدخال البريد الإلكتروني.')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT id, full_name FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        if not user:
            conn.close()
            return render_template('forgot_password.html', error='البريد غير مسجل.')
        ensure_password_reset_table()
        user_id, full_name = user
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(minutes=30)).isoformat()
        created_at = datetime.now().isoformat()
        c.execute('INSERT INTO password_resets (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)',
                  (user_id, token, expires_at, created_at))
        conn.commit()
        conn.close()
        reset_link = url_for('reset_password', token=token, _external=True)
        msg_body = f"""
مرحباً {full_name},

لإعادة تعيين كلمة المرور، يرجى الضغط على الرابط التالي:
{reset_link}

الرابط صالح لمدة 30 دقيقة فقط.
"""
        smtp_server = os.environ.get('SMTP_SERVER')
        try:
            smtp_port = int(str(os.environ.get('SMTP_PORT', 587)).strip())
        except Exception:
            smtp_port = 587
            print(f"[WARN] Invalid SMTP_PORT value: {os.environ.get('SMTP_PORT')!r}. Falling back to 587.")
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        smtp_ready = all([smtp_server, smtp_user, smtp_pass]) and smtp_server != 'smtp.example.com'
        try:
            msg = MIMEText(msg_body, 'plain', 'utf-8')
            msg['Subject'] = 'استعادة كلمة المرور - GOLD PRO'
            msg['From'] = smtp_user or 'noreply@goldpro.com'
            msg['To'] = email
            if smtp_ready:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(msg['From'], [msg['To']], msg.as_string())
            else:
                print('SMTP settings not ready, skipping email send.')
        except Exception as e:
            print(f'Error sending reset email: {e}')
        return render_template('forgot_password.html', success='تم إرسال رابط الاستعادة إلى بريدك إذا كان مسجلاً.')
    return render_template('forgot_password.html')
subscription_manager = vip_subscription_system.SubscriptionManager()


def _build_public_url(path):
    """إنشاء رابط عام صالح للرسائل البريدية."""
    try:
        return email_service.build_public_url(path)
    except Exception:
        base = os.environ.get('PUBLIC_BASE_URL') or os.environ.get('SITE_BASE_URL') or os.environ.get('RENDER_EXTERNAL_URL') or request.host_url.rstrip('/')
        return f"{str(base).rstrip('/')}/{str(path).lstrip('/')}"


def _ensure_customer_communication_tables():
    """إنشاء جداول تتبع الحملات البريدية وسجلات المستلمين."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            campaign_type TEXT DEFAULT 'update',
            audience TEXT NOT NULL,
            actor_username TEXT,
            recipient_count INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("PRAGMA table_info(email_campaigns)")
    columns = {row[1] for row in cursor.fetchall()}
    if 'campaign_type' not in columns:
        cursor.execute("ALTER TABLE email_campaigns ADD COLUMN campaign_type TEXT DEFAULT 'update'")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_campaign_recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            delivery_status TEXT NOT NULL,
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(campaign_id) REFERENCES email_campaigns(id)
        )
    ''')
    conn.commit()
    conn.close()


def _log_email_campaign(subject, body, campaign_type, audience, actor_username, result):
    """حفظ حملة بريدية جماعية ونتيجة كل مستلم في users.db."""
    _ensure_customer_communication_tables()
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO email_campaigns (
            subject, body, campaign_type, audience, actor_username,
            recipient_count, sent_count, failed_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            subject,
            body,
            campaign_type,
            audience,
            actor_username,
            int(result.get('recipient_count', 0) or 0),
            int(result.get('sent', 0) or 0),
            int(result.get('failed', 0) or 0),
        )
    )
    campaign_id = cursor.lastrowid

    for email in result.get('sent_emails', []) or []:
        cursor.execute(
            '''
            INSERT INTO email_campaign_recipients (campaign_id, email, delivery_status)
            VALUES (?, ?, 'sent')
            ''',
            (campaign_id, email)
        )

    for failed_row in result.get('failed_emails', []) or []:
        cursor.execute(
            '''
            INSERT INTO email_campaign_recipients (campaign_id, email, delivery_status, error_message)
            VALUES (?, ?, 'failed', ?)
            ''',
            (
                campaign_id,
                str((failed_row or {}).get('email') or '').strip(),
                str((failed_row or {}).get('error') or '').strip() or None,
            )
        )

    conn.commit()
    conn.close()
    return campaign_id


def _get_recent_email_campaigns(limit=20):
    """إرجاع آخر الحملات البريدية مع ملخص سريع."""
    _ensure_customer_communication_tables()
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, subject, audience, actor_username, recipient_count,
             sent_count, failed_count, created_at, campaign_type
        FROM email_campaigns
        ORDER BY id DESC
        LIMIT ?
        ''',
        (int(limit or 20),)
    )
    campaigns = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return campaigns


def _ensure_subscription_user_link(user_id, username, full_name='', email='', phone='', country='', nickname='', prefer_trial=False):
    """ضمان وجود المستخدم في قاعدة vip_subscriptions وربطه بمعرّف users.db."""
    try:
        user_id = int(user_id)
    except Exception:
        return False, 'invalid_user_id'

    username = str(username or '').strip()
    first_name = str(full_name or '').strip()
    email = str(email or '').strip()
    phone = str(phone or '').strip()
    country = str(country or '').strip()
    nickname = str(nickname or '').strip()

    if not username:
        return False, 'missing_username'

    try:
        conn = sqlite3.connect('vip_subscriptions.db')
        c = conn.cursor()
        c.execute('PRAGMA table_info(users)')
        cols = {row[1] for row in c.fetchall()}
        if 'deleted_at' in cols:
            c.execute('SELECT deleted_at FROM users WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            if row and row[0]:
                conn.close()
                return False, 'user_deleted_by_admin'
        conn.close()
    except Exception:
        pass

    existing = subscription_manager.get_user(user_id)
    if existing:
        try:
            conn = sqlite3.connect('vip_subscriptions.db')
            c = conn.cursor()
            c.execute("PRAGMA table_info(users)")
            cols = {row[1] for row in c.fetchall()}

            updates = []
            params = []
            if 'username' in cols:
                updates.append('username = ?')
                params.append(username)
            if 'first_name' in cols:
                updates.append('first_name = ?')
                params.append(first_name)
            if email and 'email' in cols:
                updates.append('email = ?')
                params.append(email)
            if phone and 'phone' in cols:
                updates.append('phone = ?')
                params.append(phone)
            if country and 'country' in cols:
                updates.append('country = ?')
                params.append(country)
            if nickname and 'nickname' in cols:
                updates.append('nickname = ?')
                params.append(nickname)

            if updates:
                params.append(user_id)
                c.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", tuple(params))
                conn.commit()
            conn.close()
        except Exception:
            pass
        return True, 'already_linked'

    if prefer_trial:
        ok, msg = subscription_manager.add_user(
            user_id,
            username,
            first_name,
            email=email or None,
            phone=phone or None,
            country=country or None,
            nickname=nickname or None
        )
        return bool(ok), msg

    try:
        conn = sqlite3.connect('vip_subscriptions.db')
        c = conn.cursor()

        c.execute('PRAGMA table_info(users)')
        cols = {row[1] for row in c.fetchall()}

        referral_code = None
        for _ in range(6):
            candidate = subscription_manager.generate_referral_code(user_id)
            c.execute('SELECT 1 FROM users WHERE referral_code = ?', (candidate,))
            if not c.fetchone():
                referral_code = candidate
                break
        if not referral_code:
            referral_code = f"REF{user_id}{int(time.time()) % 100000}"

        insert_columns = [
            'user_id', 'username', 'first_name', 'plan', 'subscription_start',
            'subscription_end', 'status', 'referral_code', 'total_paid', 'created_at'
        ]
        insert_values = [
            user_id, username, first_name, 'free', datetime.now().isoformat(),
            None, 'active', referral_code, 0, 'CURRENT_TIMESTAMP'
        ]

        if 'email' in cols:
            insert_columns.append('email')
            insert_values.append(email or None)
        if 'phone' in cols:
            insert_columns.append('phone')
            insert_values.append(phone or None)
        if 'country' in cols:
            insert_columns.append('country')
            insert_values.append(country or None)
        if 'nickname' in cols:
            insert_columns.append('nickname')
            insert_values.append(nickname or None)

        values_sql = []
        params = []
        for value in insert_values:
            if value == 'CURRENT_TIMESTAMP':
                values_sql.append('CURRENT_TIMESTAMP')
            else:
                values_sql.append('?')
                params.append(value)

        c.execute(
            f"INSERT INTO users ({', '.join(insert_columns)}) VALUES ({', '.join(values_sql)})",
            tuple(params)
        )

        conn.commit()
        conn.close()
        return True, 'linked_free'
    except Exception as e:
        return False, str(e)


def _sync_registered_users_to_subscriptions(prefer_trial_for_missing=False):
    """مزامنة جميع المستخدمين من users.db إلى vip_subscriptions.db."""
    summary = {
        'total_users': 0,
        'linked': 0,
        'failed': 0,
        'skipped_deleted': 0,
        'errors': []
    }
    try:
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('PRAGMA table_info(users)')
        users_cols = {row[1] for row in c.fetchall()}
        where = '1=1'
        if 'deleted_at' in users_cols:
            where += " AND (deleted_at IS NULL OR deleted_at = '')"
        select_parts = ['id', 'username', 'full_name', 'email']
        for extra_col in ('phone', 'country', 'nickname'):
            if extra_col in users_cols:
                select_parts.append(extra_col)
            else:
                select_parts.append(f'NULL AS {extra_col}')
        c.execute(f"SELECT {', '.join(select_parts)} FROM users WHERE {where} ORDER BY id ASC")
        rows = c.fetchall()
        conn.close()
    except Exception as e:
        summary['errors'].append(f'load_users_failed: {e}')
        return summary

    summary['total_users'] = len(rows)
    for row in rows:
        ok, msg = _ensure_subscription_user_link(
            row['id'],
            row['username'],
            row['full_name'],
            row['email'],
            row['phone'],
            row['country'],
            row['nickname'],
            prefer_trial=prefer_trial_for_missing
        )
        if ok:
            summary['linked'] += 1
        else:
            if str(msg or '').strip().lower() in ('deleted_by_admin', 'user_deleted_by_admin'):
                summary['skipped_deleted'] += 1
                continue
            summary['failed'] += 1
            if len(summary['errors']) < 20:
                summary['errors'].append(f"user_id={row['id']}: {msg}")
    return summary


def _normalize_symbol_key(symbol):
    """تطبيع رمز الأصل/الزوج لصيغة موحدة للمقارنة والتخزين."""
    normalized = str(symbol or '').upper().replace('/', '').replace('-', '').replace('_', '').replace(' ', '')
    aliases = {
        'WTI': 'USOIL',
        'CRUDE': 'USOIL',
        'BRENT': 'UKOIL',
        'NGAS': 'NATGAS',
        'DJI': 'US30',
        'IXIC': 'NAS100',
        'NASDAQ100': 'NAS100',
        'NAS': 'NAS100',
        'SPX': 'SPX500',
        'SP500': 'SPX500',
        'GSPC': 'SPX500',
        'GOLD': 'XAUUSD',
        'SILVER': 'XAGUSD',
        'BTCUSDT': 'BTCUSD',
        'ETHUSDT': 'ETHUSD',
        'BNBUSDT': 'BNBUSD',
        'SOLUSDT': 'SOLUSD',
        'XRPUSDT': 'XRPUSD',
        'ADAUSDT': 'ADAUSD',
        'DOGEUSDT': 'DOGEUSD',
        'LTCUSDT': 'LTCUSD'
    }
    return aliases.get(normalized, normalized)

DATA_DIR = Path(
    os.environ.get(
        'GOLDPRO_DATA_DIR',
        '/var/data' if Path('/var/data').exists() else str(Path(__file__).parent)
    )
)
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# ====== Environment variable defaults for persistent data paths and settings ======
os.environ.setdefault('SIGNALS_DIR', '/var/data/signals')
os.environ.setdefault('SENT_SIGNALS_FILE', '/var/data/sent_signals.json')
os.environ.setdefault('RECOMMENDATIONS_DIR', '/var/data/recommendations')
os.environ.setdefault('ANALYSIS_DIR', '/var/data/analysis')
os.environ.setdefault('USER_PREFERENCES_FILE', '/var/data/user_pairs_preferences.json')
os.environ.setdefault('BACKUPS_DIR', '/var/data/backups')
os.environ.setdefault('BACKUPS_KEEP', '21')
os.environ.setdefault('BACKUP_ON_ADMIN_WRITE', '1')
os.environ.setdefault('AUTO_MERGE_LEGACY_ON_STARTUP', '1')
os.environ.setdefault('AUTO_BROADCAST_REGISTRY_FILE', '/var/data/auto_broadcast_registry.json')
os.environ.setdefault('AUTO_BROADCAST_RECENT_WINDOW_MINUTES', '2880')
os.environ.setdefault('AUTO_BROADCAST_RESEND_INTERVAL_MINUTES', '30')
os.environ.setdefault('AUTO_BROADCAST_ALLOW_RESEND', '0')
os.environ.setdefault('SIGNALS_LOOKBACK_DAYS', '7')

# Telegram Command Bot environment defaults
os.environ.setdefault('TELEGRAM_COMMAND_STATE_FILE', '/var/data/telegram_command_bot_state.json')
os.environ.setdefault('TELEGRAM_COMMAND_POLL_INTERVAL', '2')
os.environ.setdefault('TELEGRAM_COMMAND_TIMEOUT', '30')
os.environ.setdefault('TELEGRAM_ADMIN_IDS', '')
os.environ.setdefault('TELEGRAM_ADMIN_USERNAMES', '')

USERS_DB_PATH = Path(os.environ.get('USERS_DB_PATH', str(DATA_DIR / 'users.db')))
VIP_SUBSCRIPTIONS_DB_PATH = Path(os.environ.get('VIP_SUBSCRIPTIONS_DB_PATH', str(DATA_DIR / 'vip_subscriptions.db')))
VIP_SIGNALS_DB_PATH = Path(os.environ.get('VIP_SIGNALS_DB_PATH', str(DATA_DIR / 'vip_signals.db')))
SIGNALS_DIR = Path(os.environ.get('SIGNALS_DIR', str(DATA_DIR / 'signals')))
SENT_SIGNALS_FILE = Path(os.environ.get('SENT_SIGNALS_FILE', str(DATA_DIR / 'sent_signals.json')))

_ORIGINAL_SQLITE_CONNECT = sqlite3.connect


def _patched_sqlite_connect(database, *args, **kwargs):
    """توجيه كل الاتصالات القديمة vip_signals.db إلى المسار الموحّد."""
    original_database = database
    try:
        if isinstance(database, str):
            normalized = database.replace('\\', '/').strip().lower()
            if normalized in ('vip_signals.db', './vip_signals.db'):
                database = str(VIP_SIGNALS_DB_PATH)
            elif normalized in ('users.db', './users.db'):
                database = str(USERS_DB_PATH)
            elif normalized in ('vip_subscriptions.db', './vip_subscriptions.db'):
                database = str(VIP_SUBSCRIPTIONS_DB_PATH)
    except Exception:
        pass
    conn = _ORIGINAL_SQLITE_CONNECT(database, *args, **kwargs)
    try:
        db_path = str(database or '').replace('\\', '/').strip().lower()
        vip_path = str(VIP_SIGNALS_DB_PATH).replace('\\', '/').strip().lower()
        original_hint = str(original_database or '').replace('\\', '/').strip().lower()
        if db_path == vip_path or original_hint in ('vip_signals.db', './vip_signals.db'):
            cursor = conn.cursor()
            cursor.execute('PRAGMA busy_timeout = 30000')
            cursor.execute('PRAGMA journal_mode = WAL')
            cursor.execute('PRAGMA synchronous = NORMAL')
    except Exception:
        pass
    return conn


sqlite3.connect = _patched_sqlite_connect
AUTO_BROADCAST_REGISTRY_FILE = Path(os.environ.get('AUTO_BROADCAST_REGISTRY_FILE', str(DATA_DIR / 'auto_broadcast_registry.json')))
AUTO_BROADCAST_RECENT_WINDOW_MINUTES = max(1, int(os.environ.get('AUTO_BROADCAST_RECENT_WINDOW_MINUTES', '2880')))
AUTO_BROADCAST_RESEND_INTERVAL_MINUTES = max(1, int(os.environ.get('AUTO_BROADCAST_RESEND_INTERVAL_MINUTES', '30')))
AUTO_BROADCAST_ALLOW_RESEND = os.environ.get('AUTO_BROADCAST_ALLOW_RESEND', '0').strip().lower() in ('1', 'true', 'yes', 'on')
SIGNALS_LOOKBACK_DAYS = max(1, int(os.environ.get('SIGNALS_LOOKBACK_DAYS', '7')))
ACTIVE_SIGNAL_STATUS_LOOKBACK_DAYS = max(SIGNALS_LOOKBACK_DAYS, int(os.environ.get('ACTIVE_SIGNAL_STATUS_LOOKBACK_DAYS', '45')))
RECOMMENDATIONS_DIR = Path(os.environ.get('RECOMMENDATIONS_DIR', str(DATA_DIR / 'recommendations')))
ANALYSIS_DIR = Path(os.environ.get('ANALYSIS_DIR', str(DATA_DIR / 'analysis')))
USER_PREFERENCES_FILE = Path(os.environ.get('USER_PREFERENCES_FILE', str(DATA_DIR / 'user_pairs_preferences.json')))
BACKUPS_DIR = Path(os.environ.get('BACKUPS_DIR', str(DATA_DIR / 'backups')))
BACKUPS_KEEP = max(3, int(os.environ.get('BACKUPS_KEEP', '21')))
BACKUP_ON_ADMIN_WRITE = os.environ.get('BACKUP_ON_ADMIN_WRITE', '1').strip().lower() in ('1', 'true', 'yes', 'on')
AUTO_MERGE_LEGACY_ON_STARTUP = os.environ.get('AUTO_MERGE_LEGACY_ON_STARTUP', '1').strip().lower() in ('1', 'true', 'yes', 'on')
CLOSED_TRADES_ARCHIVE_FILE = Path(__file__).parent / "closed_trades.json"
PUBLIC_ADS_FILE = Path(__file__).parent / 'public_ads.json'
ECONOMIC_NEWS_CACHE_FILE = Path(__file__).parent / 'economic_news_cache.json'
ECONOMIC_NEWS_SOURCES_FILE = Path(__file__).parent / 'economic_news_sources.json'

ECONOMIC_NEWS_SOURCES = [
    {
        'name': 'FXStreet',
        'url': 'https://www.fxstreet.com/rss/news',
        'enabled': True
    },
    {
        'name': 'DailyFX',
        'url': 'https://www.dailyfx.com/feeds/market-news',
        'enabled': True
    },
    {
        'name': 'Investing',
        'url': 'https://www.investing.com/rss/news_25.rss',
        'enabled': True
    },
    {
        'name': 'ArgaamAR',
        'url': 'https://www.argaam.com/ar/rss',
        'enabled': True
    },
    {
        'name': 'MubasherAR',
        'url': 'https://www.mubasher.info/rss/news',
        'enabled': True
    },
    {
        'name': 'SkyNewsArabiaEco',
        'url': 'https://www.skynewsarabia.com/web/rss/7-1',
        'enabled': True
    }
]

ECONOMIC_KEYWORDS = [
    'cpi', 'inflation', 'fomc', 'fed', 'ecb', 'boe', 'boj', 'rate', 'rates',
    'interest', 'nfp', 'payroll', 'gdp', 'pmi', 'jobless', 'unemployment',
    'retail sales', 'consumer confidence', 'crude', 'oil', 'gold', 'dollar',
    'forex', 'economy', 'economic', 'bank of', 'قرار الفائدة', 'التضخم', 'البطالة',
    'الناتج المحلي', 'الفيدرالي', 'اقتصاد', 'النفط', 'الذهب', 'الدولار'
]

DEFAULT_PUBLIC_ADS = [
    {
        'badge': 'إعلان مميز',
        'title': 'خصم 30% على باقة Silver',
        'text': 'لفترة محدودة، احصل على مزايا التحليل المتقدم مع سعر خاص.',
        'cta_text': 'عرض الخطط',
        'cta_url': '/plans'
    },
    {
        'badge': 'جديد',
        'title': 'إشارات يومية محدثة',
        'text': 'تابع توصيات السوق بشكل يومي مع تحديثات مستمرة وجودة عالية.',
        'cta_text': 'تسجيل لأول مرة',
        'cta_url': '/register?first=1'
    },
    {
        'badge': 'دعم',
        'title': 'دعم مباشر للمشتركين',
        'text': 'فريق الدعم متاح للرد على الاستفسارات ومتابعة طلبات الاشتراك.',
        'cta_text': 'تسجيل الدخول',
        'cta_url': '/login?first=1'
    }
]

# خريطة رموز Yahoo Finance
YF_SYMBOLS = {
    'XAUUSD': 'GC=F', 'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X', 'AUDUSD': 'AUDUSD=X', 'USDCAD': 'USDCAD=X',
    'NZDUSD': 'NZDUSD=X', 'USDCHF': 'USDCHF=X', 'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD', 'XAGUSD': 'SI=F',
    'USOIL': 'CL=F', 'WTI': 'CL=F',
    'UKOIL': 'BZ=F', 'BRENT': 'BZ=F',
    'NATGAS': 'NG=F', 'NGAS': 'NG=F',
    'EURJPY': 'EURJPY=X', 'GBPJPY': 'GBPJPY=X', 'EURGBP': 'EURGBP=X',
    'CADJPY': 'CADJPY=X', 'CHFJPY': 'CHFJPY=X',
    'US30': '^DJI', 'NAS100': '^IXIC', 'SPX500': '^GSPC'
}

BINANCE_PRICE_URL = 'https://api.binance.com/api/v3/ticker/price'
BINANCE_SYMBOLS = {
    'BTCUSD': 'BTCUSDT',
    'ETHUSD': 'ETHUSDT',
    'BTCUSDT': 'BTCUSDT',
    'ETHUSDT': 'ETHUSDT'
}
TWELVEDATA_PRICE_URL = 'https://api.twelvedata.com/price'
TWELVEDATA_API_KEY = os.environ.get('TWELVEDATA_API_KEY', '079cdb64bbc8415abcf8f7be7e389349')
LIVE_PRICE_CACHE_TTL_SECONDS = int(os.environ.get('LIVE_PRICE_CACHE_TTL_SECONDS', '20'))
LIVE_PRICE_FAIL_CACHE_TTL_SECONDS = int(os.environ.get('LIVE_PRICE_FAIL_CACHE_TTL_SECONDS', '8'))
YF_COOLDOWN_SECONDS = int(os.environ.get('YF_COOLDOWN_SECONDS', '45'))
YF_MAX_RETRIES = int(os.environ.get('YF_MAX_RETRIES', '2'))
YF_RETRY_BACKOFF_SECONDS = float(os.environ.get('YF_RETRY_BACKOFF_SECONDS', '0.8'))
LIVE_PRICE_CACHE = {}
YF_FAILURE_UNTIL = {}
LIVE_PRICE_CACHE_LOCK = threading.Lock()
UPDATE_PRICES_LAST_PAYLOAD = {
    'signals': [],
    'updated_at': None,
    'updated_at_ts': 0.0
}
UPDATE_PRICES_CACHE_TTL_SECONDS = max(1, int(os.environ.get('UPDATE_PRICES_CACHE_TTL_SECONDS', '5')))

CONTINUOUS_ANALYZER_SYMBOLS = [
    # Forex
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
    'EURJPY', 'GBPJPY', 'EURGBP', 'CADJPY', 'CHFJPY',
    # Commodities
    'XAUUSD', 'XAGUSD', 'USOIL', 'UKOIL', 'NATGAS',
    # Indices
    'US30', 'NAS100', 'SPX500',
    # Crypto
    'BTCUSD', 'ETHUSD'
]

_symbols_from_env = os.environ.get('CONTINUOUS_ANALYZER_SYMBOLS', '').strip()
if _symbols_from_env:
    parsed_symbols = [s.strip().upper().replace('/', '') for s in _symbols_from_env.split(',') if s.strip()]
    if parsed_symbols:
        CONTINUOUS_ANALYZER_SYMBOLS = parsed_symbols


def _parse_analyzer_intervals(raw_value, fallback):
    values = []
    for item in str(raw_value or '').split(','):
        normalized = str(item or '').strip().lower().replace(' ', '')
        if normalized in ('15m', '15min'):
            interval = '15min'
        elif normalized in ('30m', '30min'):
            interval = '30min'
        elif normalized in ('1h', '60m', '60min'):
            interval = '1h'
        elif normalized in ('4h', '240m', '240min'):
            interval = '4h'
        elif normalized in ('1d', '1day', 'daily'):
            interval = '1day'
        else:
            interval = None
        if interval and interval not in values:
            values.append(interval)
    return values or list(fallback)


HIGH_FREQUENCY_ANALYZER_SYMBOLS = {
    _normalize_symbol_key(symbol)
    for symbol in str(
        os.environ.get(
            'HIGH_FREQUENCY_ANALYZER_SYMBOLS',
            'XAUUSD,XAGUSD,USOIL,UKOIL,NATGAS,US30,NAS100,SPX500,BTCUSD,ETHUSD,EURUSD,GBPUSD,USDJPY,GBPJPY,EURJPY'
        )
    ).split(',')
    if _normalize_symbol_key(symbol)
}
HIGH_FREQUENCY_ANALYZER_INTERVALS = _parse_analyzer_intervals(
    os.environ.get('HIGH_FREQUENCY_ANALYZER_INTERVALS', '30min,1h'),
    ['30min', '1h']
)
DEFAULT_ANALYZER_INTERVALS = _parse_analyzer_intervals(
    os.environ.get('DEFAULT_ANALYZER_INTERVALS', '1h'),
    ['1h']
)
ANALYZER_MAX_INTERVALS_PER_SYMBOL = max(1, min(3, int(os.environ.get('ANALYZER_MAX_INTERVALS_PER_SYMBOL', '2'))))
ANALYZER_ENABLE_INTERVAL_FALLBACK = os.environ.get('ANALYZER_ENABLE_INTERVAL_FALLBACK', '0').strip().lower() in ('1', 'true', 'yes', 'on')
ANALYZER_FALLBACK_INTERVALS = _parse_analyzer_intervals(
    os.environ.get('ANALYZER_FALLBACK_INTERVALS', '1h'),
    ['1h']
)

CONTINUOUS_ANALYZER_INTERVAL_DEFAULT = int(os.environ.get('CONTINUOUS_ANALYZER_INTERVAL_SECONDS', '120'))
MIN_SIGNAL_QUALITY_SCORE = int(os.environ.get('MIN_SIGNAL_QUALITY_SCORE', '55'))
MIN_SIGNAL_RR = float(os.environ.get('MIN_SIGNAL_RR', '1.0'))
MAX_SIGNAL_VOLATILITY = float(os.environ.get('MAX_SIGNAL_VOLATILITY', '4.2'))
RELAX_SIGNAL_FILTERS_WHEN_EMPTY = os.environ.get('RELAX_SIGNAL_FILTERS_WHEN_EMPTY', '1').strip().lower() in ('1', 'true', 'yes', 'on')
RELAX_SIGNAL_FILTERS_IF_ACTIVE_COUNT_LE = max(0, int(os.environ.get('RELAX_SIGNAL_FILTERS_IF_ACTIVE_COUNT_LE', '3')))
MIN_SIGNAL_QUALITY_WHEN_EMPTY = int(os.environ.get('MIN_SIGNAL_QUALITY_WHEN_EMPTY', '35'))
MIN_SIGNAL_RR_WHEN_EMPTY = float(os.environ.get('MIN_SIGNAL_RR_WHEN_EMPTY', '0.5'))
MAX_SIGNAL_VOLATILITY_WHEN_EMPTY = float(os.environ.get('MAX_SIGNAL_VOLATILITY_WHEN_EMPTY', '8.0'))
CLEANUP_INTERVAL_DEFAULT = int(os.environ.get('SIGNALS_CLEANUP_INTERVAL_SECONDS', '180'))
CRITICAL_SIGNAL_SYMBOLS = {'XAUUSD', 'XAGUSD', 'USOIL', 'UKOIL', 'NATGAS', 'BTCUSD', 'ETHUSD', 'US30', 'NAS100', 'SPX500'}
CRITICAL_SIGNAL_RELAX_IF_ACTIVE_COUNT_LE = max(0, int(os.environ.get('CRITICAL_SIGNAL_RELAX_IF_ACTIVE_COUNT_LE', '3')))
CRITICAL_SIGNAL_MIN_QUALITY = int(os.environ.get('CRITICAL_SIGNAL_MIN_QUALITY', '35'))
CRITICAL_SIGNAL_MIN_RR = float(os.environ.get('CRITICAL_SIGNAL_MIN_RR', '0.75'))
CRITICAL_SIGNAL_MAX_VOLATILITY = float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY', '9.5'))
CRITICAL_SIGNAL_STRONG_RR_TRIGGER = float(os.environ.get('CRITICAL_SIGNAL_STRONG_RR_TRIGGER', '1.35'))
CRITICAL_SIGNAL_MIN_QUALITY_STRONG_RR = int(os.environ.get('CRITICAL_SIGNAL_MIN_QUALITY_STRONG_RR', '34'))
CRITICAL_SIGNAL_MAX_VOLATILITY_BY_SYMBOL = {
    'XAUUSD': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_XAUUSD', '18.0')),
    'XAGUSD': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_XAGUSD', '20.0')),
    'USOIL': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_USOIL', '28.0')),
    'UKOIL': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_UKOIL', '28.0')),
    'NATGAS': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_NATGAS', '20.0')),
    'US30': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_US30', '18.0')),
    'NAS100': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_NAS100', '20.0')),
    'SPX500': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_SPX500', '18.0')),
    'BTCUSD': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_BTCUSD', '45.0')),
    'ETHUSD': float(os.environ.get('CRITICAL_SIGNAL_MAX_VOLATILITY_ETHUSD', '50.0')),
}

CONTINUOUS_ANALYZER_STATE = {
    'running': False,
    'interval_seconds': CONTINUOUS_ANALYZER_INTERVAL_DEFAULT,
    'started_at': None,
    'last_cycle_started_at': None,
    'cycle_stage': 'idle',
    'current_symbol': None,
    'current_interval': None,
    'current_symbol_index': 0,
    'symbols_total': 0,
    'last_run': None,
    'last_error': None,
    'last_analyzed_count': 0,
    'last_failed_count': 0,
    'last_no_signal_count': 0,
    'last_failed_symbols': [],
    'last_rejection_reasons': {},
    'last_rejection_samples': [],
    'last_active_signals_count': 0,
    'last_new_signals': 0,
    'last_deduplicated': 0,
    'total_generated': 0,
    'total_broadcasted': 0
}
CONTINUOUS_ANALYZER_THREAD = None
CONTINUOUS_ANALYZER_LOCK = threading.Lock()
VIP_SIGNALS_DB_LOCK = threading.RLock()
CLEANUP_AUDIT_FILE = Path(__file__).parent / 'cleanup_audit_log.json'
CLEANUP_SCHEDULER_STATE = {
    'running': False,
    'interval_seconds': CLEANUP_INTERVAL_DEFAULT,
    'last_run': None,
    'last_error': None,
    'last_cleaned_closed': 0,
    'last_deduplicated': 0,
    'last_site_synced': 0,
    'total_cleaned_closed': 0,
    'total_deduplicated': 0,
    'total_site_synced': 0
}
CLEANUP_SCHEDULER_THREAD = None
CLEANUP_SCHEDULER_LOCK = threading.Lock()

APP_BASE_DIR = Path(__file__).parent.resolve()


def _ensure_backup_dir():
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def _prune_backups(prefix):
    try:
        _ensure_backup_dir()
        files = sorted(BACKUPS_DIR.glob(f'{prefix}_*.db'), key=lambda p: p.stat().st_mtime, reverse=True)
        for stale in files[BACKUPS_KEEP:]:
            try:
                stale.unlink()
            except Exception:
                pass
    except Exception:
        pass


def _backup_database_file(db_path, prefix):
    """نسخ احتياطي سريع لقاعدة البيانات مع حفظ عدد محدد من النسخ."""
    try:
        path = Path(str(db_path))
        if not path.exists() or not path.is_file():
            return None
        if not _ensure_backup_dir():
            return None
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        target = BACKUPS_DIR / f'{prefix}_{stamp}.db'
        shutil.copy2(str(path), str(target))
        _prune_backups(prefix)
        return str(target)
    except Exception:
        return None


def _snapshot_core_databases(reason='manual', actor='system'):
    """أخذ snapshot لقاعدتي المستخدمين/الاشتراكات قبل العمليات الحساسة."""
    users_backup = _backup_database_file(USERS_DB_PATH, 'users')
    vip_backup = _backup_database_file(VIP_SUBSCRIPTIONS_DB_PATH, 'vip_subscriptions')
    return {
        'reason': str(reason or 'manual'),
        'actor': str(actor or 'system'),
        'users_backup': users_backup,
        'vip_backup': vip_backup,
        'created_at': datetime.now().isoformat()
    }


def _ensure_admin_audit_table():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS admin_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_username TEXT,
                action TEXT,
                target_user_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _log_admin_audit(action, target_user_id=None, details=None):
    try:
        _ensure_admin_audit_table()
        admin_username = session.get('local_admin_username') if isinstance(session, dict) else None
        if not admin_username:
            info = get_current_user()
            if isinstance(info, dict) and info.get('success'):
                admin_username = info.get('username')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute(
            '''
            INSERT INTO admin_audit_log (admin_username, action, target_user_id, details)
            VALUES (?, ?, ?, ?)
            ''',
            (str(admin_username or 'system'), str(action or ''), target_user_id, json.dumps(details or {}, ensure_ascii=False))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _table_row_count(db_path, table_name):
    """إرجاع عدد الصفوف في جدول محدد أو 0 عند الفشل."""
    try:
        conn = _ORIGINAL_SQLITE_CONNECT(str(db_path))
        c = conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = int((c.fetchone() or [0])[0] or 0)
        conn.close()
        return count
    except Exception:
        return 0


def _legacy_db_candidates(primary_filename, backup_glob_pattern):
    """تجميع ملفات قواعد بيانات قديمة يمكن الاسترجاع منها."""
    candidates = []

    direct = [
        APP_BASE_DIR / primary_filename,
        APP_BASE_DIR / 'instance' / primary_filename,
        APP_BASE_DIR / 'backups' / primary_filename,
        DATA_DIR / primary_filename,
        DATA_DIR / 'backups' / primary_filename,
    ]
    for path in direct:
        if path.exists() and path.is_file():
            candidates.append(path)

    for root in [APP_BASE_DIR / 'backups', DATA_DIR / 'backups']:
        if not root.exists() or not root.is_dir():
            continue
        for path in sorted(root.glob(backup_glob_pattern), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.exists() and path.is_file():
                candidates.append(path)

    unique = []
    seen = set()
    for item in candidates:
        key = str(item.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _merge_users_from_source_db(source_db):
    """دمج مستخدمين من ملف users.db محدد إلى قاعدة المستخدمين الحالية."""
    source_db = Path(str(source_db))
    if not source_db.exists() or not source_db.is_file():
        return {'merged': 0, 'source': str(source_db), 'reason': 'source_missing'}

    target_db = USERS_DB_PATH
    target_key = str(target_db.resolve()).lower()
    source_key = str(source_db.resolve()).lower()
    if source_key == target_key:
        return {'merged': 0, 'source': str(source_db), 'reason': 'same_as_target'}

    if _table_row_count(source_db, 'users') <= 0:
        return {'merged': 0, 'source': str(source_db), 'reason': 'source_empty'}

    try:
        src_conn = _ORIGINAL_SQLITE_CONNECT(str(source_db))
        src_conn.row_factory = sqlite3.Row
        src_cur = src_conn.cursor()
        src_cur.execute('PRAGMA table_info(users)')
        src_cols = {row[1] for row in src_cur.fetchall()}

        target_conn = _ORIGINAL_SQLITE_CONNECT(str(target_db))
        target_cur = target_conn.cursor()
        target_cur.execute('PRAGMA table_info(users)')
        target_cols = {row[1] for row in target_cur.fetchall()}

        required = {'username', 'email', 'password_hash'}
        if not required.issubset(src_cols) or not required.issubset(target_cols):
            src_conn.close()
            target_conn.close()
            return {'merged': 0, 'source': str(source_db), 'reason': 'missing_required_columns'}

        preferred_cols = [
            'id', 'username', 'email', 'password_hash', 'full_name', 'plan',
            'created_at', 'last_login', 'is_active', 'is_admin',
            'role', 'phone', 'country', 'nickname',
            'deleted_at', 'deleted_by', 'delete_reason'
        ]
        selected_cols = [col for col in preferred_cols if col in src_cols and col in target_cols]

        src_cur.execute(f"SELECT {', '.join(selected_cols)} FROM users")
        rows = src_cur.fetchall()
        if not rows:
            src_conn.close()
            target_conn.close()
            return {'merged': 0, 'source': str(source_db), 'reason': 'no_rows'}

        placeholders = ', '.join(['?'] * len(selected_cols))
        insert_sql = f"INSERT OR IGNORE INTO users ({', '.join(selected_cols)}) VALUES ({placeholders})"

        merged = 0
        for row in rows:
            values = [row[col] for col in selected_cols]
            target_cur.execute(insert_sql, values)
            if target_cur.rowcount:
                merged += 1

        target_conn.commit()
        src_conn.close()
        target_conn.close()
        return {'merged': merged, 'source': str(source_db), 'reason': 'merged'}
    except Exception as e:
        return {'merged': 0, 'source': str(source_db), 'reason': str(e)}


def _merge_users_from_legacy_sources(limit_sources=10):
    """دمج مستخدمي users.db المفقودين من قواعد قديمة/نسخ احتياطية حتى لو القاعدة الحالية غير فارغة."""
    target_db = USERS_DB_PATH
    target_key = str(target_db.resolve()).lower()
    merged_total = 0
    used_sources = []

    sources = _legacy_db_candidates('users.db', 'users_*.db')[:max(1, int(limit_sources or 10))]
    for source_db in sources:
        source_key = str(source_db.resolve()).lower()
        if source_key == target_key:
            continue
        result = _merge_users_from_source_db(source_db)
        merged_from_source = int(result.get('merged', 0) or 0)
        if merged_from_source > 0:
            merged_total += merged_from_source
            used_sources.append(str(source_db))

    return {'merged': merged_total, 'sources': used_sources}


def _merge_vip_users_from_source_db(source_db):
    """دمج مشتركي VIP من ملف vip_subscriptions.db محدد إلى قاعدة الاشتراكات الحالية."""
    source_db = Path(str(source_db))
    if not source_db.exists() or not source_db.is_file():
        return {'merged': 0, 'source': str(source_db), 'reason': 'source_missing'}

    target_db = VIP_SUBSCRIPTIONS_DB_PATH
    target_key = str(target_db.resolve()).lower()
    source_key = str(source_db.resolve()).lower()
    if source_key == target_key:
        return {'merged': 0, 'source': str(source_db), 'reason': 'same_as_target'}

    if _table_row_count(source_db, 'users') <= 0:
        return {'merged': 0, 'source': str(source_db), 'reason': 'source_empty'}

    try:
        src_conn = _ORIGINAL_SQLITE_CONNECT(str(source_db))
        src_conn.row_factory = sqlite3.Row
        src_cur = src_conn.cursor()
        src_cur.execute('PRAGMA table_info(users)')
        src_cols = {row[1] for row in src_cur.fetchall()}

        target_conn = _ORIGINAL_SQLITE_CONNECT(str(target_db))
        target_cur = target_conn.cursor()
        target_cur.execute('PRAGMA table_info(users)')
        target_cols = {row[1] for row in target_cur.fetchall()}

        if 'user_id' not in src_cols or 'user_id' not in target_cols:
            src_conn.close()
            target_conn.close()
            return {'merged': 0, 'source': str(source_db), 'reason': 'missing_user_id'}

        preferred_cols = [
            'user_id', 'username', 'first_name', 'plan', 'subscription_start',
            'subscription_end', 'status', 'referral_code', 'referred_by',
            'total_paid', 'created_at', 'password_hash', 'email',
            'activation_token', 'chat_id', 'telegram_id',
            'deleted_at', 'deleted_by', 'delete_reason', 'updated_at'
        ]
        selected_cols = [col for col in preferred_cols if col in src_cols and col in target_cols]

        src_cur.execute(f"SELECT {', '.join(selected_cols)} FROM users")
        rows = src_cur.fetchall()
        if not rows:
            src_conn.close()
            target_conn.close()
            return {'merged': 0, 'source': str(source_db), 'reason': 'no_rows'}

        placeholders = ', '.join(['?'] * len(selected_cols))
        insert_sql = f"INSERT OR IGNORE INTO users ({', '.join(selected_cols)}) VALUES ({placeholders})"

        merged = 0
        for row in rows:
            values = [row[col] for col in selected_cols]
            target_cur.execute(insert_sql, values)
            if target_cur.rowcount:
                merged += 1

        target_conn.commit()
        src_conn.close()
        target_conn.close()
        return {'merged': merged, 'source': str(source_db), 'reason': 'merged'}
    except Exception as e:
        return {'merged': 0, 'source': str(source_db), 'reason': str(e)}


def _merge_vip_users_from_legacy_sources(limit_sources=10):
    """دمج مشتركي vip_subscriptions.db المفقودين من قواعد قديمة/نسخ احتياطية."""
    target_db = VIP_SUBSCRIPTIONS_DB_PATH
    target_key = str(target_db.resolve()).lower()
    merged_total = 0
    used_sources = []

    sources = _legacy_db_candidates('vip_subscriptions.db', 'vip_subscriptions*.db')[:max(1, int(limit_sources or 10))]
    for source_db in sources:
        source_key = str(source_db.resolve()).lower()
        if source_key == target_key:
            continue
        result = _merge_vip_users_from_source_db(source_db)
        merged_from_source = int(result.get('merged', 0) or 0)
        if merged_from_source > 0:
            merged_total += merged_from_source
            used_sources.append(str(source_db))

    return {'merged': merged_total, 'sources': used_sources}


def _recover_users_db_if_empty():
    """استرجاع users.db من ملفات قديمة/نسخ احتياطية عندما تكون القاعدة الحالية فارغة."""
    target_db = USERS_DB_PATH
    current_count = _table_row_count(target_db, 'users')
    if current_count > 0:
        return {'attempted': False, 'restored': 0, 'source': None, 'reason': 'target_not_empty'}

    sources = _legacy_db_candidates('users.db', 'users_*.db')
    target_key = str(target_db.resolve()).lower()

    for source_db in sources:
        source_key = str(source_db.resolve()).lower()
        if source_key == target_key:
            continue

        source_count = _table_row_count(source_db, 'users')
        if source_count <= 0:
            continue

        try:
            src_conn = _ORIGINAL_SQLITE_CONNECT(str(source_db))
            src_conn.row_factory = sqlite3.Row
            src_cur = src_conn.cursor()
            src_cur.execute('PRAGMA table_info(users)')
            src_cols = {row[1] for row in src_cur.fetchall()}

            target_conn = _ORIGINAL_SQLITE_CONNECT(str(target_db))
            target_cur = target_conn.cursor()
            target_cur.execute('PRAGMA table_info(users)')
            target_cols = {row[1] for row in target_cur.fetchall()}

            required = {'username', 'email', 'password_hash'}
            if not required.issubset(src_cols) or not required.issubset(target_cols):
                src_conn.close()
                target_conn.close()
                continue

            selected_cols = [
                'username', 'email', 'password_hash', 'full_name', 'plan',
                'created_at', 'last_login', 'is_active', 'is_admin',
                'role', 'phone', 'country', 'nickname'
            ]
            selected_cols = [col for col in selected_cols if col in src_cols and col in target_cols]

            src_cur.execute(f"SELECT {', '.join(selected_cols)} FROM users")
            rows = src_cur.fetchall()

            if not rows:
                src_conn.close()
                target_conn.close()
                continue

            placeholders = ', '.join(['?'] * len(selected_cols))
            insert_sql = f"INSERT OR IGNORE INTO users ({', '.join(selected_cols)}) VALUES ({placeholders})"

            restored = 0
            for row in rows:
                values = [row[col] for col in selected_cols]
                target_cur.execute(insert_sql, values)
                if target_cur.rowcount:
                    restored += 1

            target_conn.commit()
            src_conn.close()
            target_conn.close()

            if restored > 0:
                return {
                    'attempted': True,
                    'restored': restored,
                    'source': str(source_db),
                    'reason': 'restored_from_legacy'
                }
        except Exception:
            continue

    return {'attempted': True, 'restored': 0, 'source': None, 'reason': 'no_valid_source'}


def _recover_vip_subscriptions_if_empty():
    """استرجاع vip_subscriptions.db من ملفات قديمة/نسخ احتياطية عندما تكون فارغة."""
    target_db = VIP_SUBSCRIPTIONS_DB_PATH
    current_count = _table_row_count(target_db, 'users')
    if current_count > 0:
        return {'attempted': False, 'restored': 0, 'source': None, 'reason': 'target_not_empty'}

    sources = _legacy_db_candidates('vip_subscriptions.db', 'vip_subscriptions*.db')
    target_key = str(target_db.resolve()).lower()

    for source_db in sources:
        source_key = str(source_db.resolve()).lower()
        if source_key == target_key:
            continue

        source_count = _table_row_count(source_db, 'users')
        if source_count <= 0:
            continue

        try:
            src_conn = _ORIGINAL_SQLITE_CONNECT(str(source_db))
            src_conn.row_factory = sqlite3.Row
            src_cur = src_conn.cursor()
            src_cur.execute('PRAGMA table_info(users)')
            src_cols = {row[1] for row in src_cur.fetchall()}

            target_conn = _ORIGINAL_SQLITE_CONNECT(str(target_db))
            target_cur = target_conn.cursor()
            target_cur.execute('PRAGMA table_info(users)')
            target_cols = {row[1] for row in target_cur.fetchall()}

            if 'user_id' not in src_cols or 'user_id' not in target_cols:
                src_conn.close()
                target_conn.close()
                continue

            selected_cols = [
                'user_id', 'username', 'first_name', 'plan', 'subscription_start',
                'subscription_end', 'status', 'referral_code', 'referred_by',
                'total_paid', 'created_at', 'password_hash', 'email',
                'activation_token', 'chat_id', 'telegram_id'
            ]
            selected_cols = [col for col in selected_cols if col in src_cols and col in target_cols]

            src_cur.execute(f"SELECT {', '.join(selected_cols)} FROM users")
            rows = src_cur.fetchall()

            if not rows:
                src_conn.close()
                target_conn.close()
                continue

            placeholders = ', '.join(['?'] * len(selected_cols))
            insert_sql = f"INSERT OR REPLACE INTO users ({', '.join(selected_cols)}) VALUES ({placeholders})"

            restored = 0
            for row in rows:
                values = [row[col] for col in selected_cols]
                target_cur.execute(insert_sql, values)
                if target_cur.rowcount:
                    restored += 1

            target_conn.commit()
            src_conn.close()
            target_conn.close()

            if restored > 0:
                return {
                    'attempted': True,
                    'restored': restored,
                    'source': str(source_db),
                    'reason': 'restored_from_legacy'
                }
        except Exception:
            continue

    return {'attempted': True, 'restored': 0, 'source': None, 'reason': 'no_valid_source'}


def _bootstrap_persistent_databases():
    """تهيئة مسارات قواعد البيانات الدائمة واسترجاع البيانات عند الحاجة."""
    _ensure_backup_dir()
    _ensure_admin_audit_table()

    try:
        if hasattr(subscription_manager, 'db_path'):
            subscription_manager.db_path = str(VIP_SUBSCRIPTIONS_DB_PATH)
            subscription_manager.init_database()
    except Exception:
        pass

    users_result = _recover_users_db_if_empty()
    vip_result = _recover_vip_subscriptions_if_empty()
    users_merge_result = {'merged': 0, 'sources': []}
    vip_merge_result = {'merged': 0, 'sources': []}
    if AUTO_MERGE_LEGACY_ON_STARTUP:
        users_merge_result = _merge_users_from_legacy_sources(limit_sources=8)
        vip_merge_result = _merge_vip_users_from_legacy_sources(limit_sources=8)
    sync_result = _sync_registered_users_to_subscriptions(prefer_trial_for_missing=False)
    startup_backup = _snapshot_core_databases(reason='startup_bootstrap', actor='system') if BACKUP_ON_ADMIN_WRITE else None

    _log_admin_audit(
        action='startup_bootstrap',
        target_user_id=None,
        details={
            'users_result': users_result,
            'vip_result': vip_result,
            'users_merge_result': users_merge_result,
            'vip_merge_result': vip_merge_result,
            'sync_result': sync_result,
            'startup_backup': startup_backup
        }
    )

    if users_result.get('restored', 0) > 0 or vip_result.get('restored', 0) > 0 or users_merge_result.get('merged', 0) > 0 or vip_merge_result.get('merged', 0) > 0:
        print(f"[RECOVERY] users={users_result} vip={vip_result} users_merge={users_merge_result} vip_merge={vip_merge_result} sync={sync_result}")
    elif int(sync_result.get('linked', 0) or 0) > 0:
        print(f"[RECOVERY-SYNC] sync={sync_result}")


_bootstrap_persistent_databases()


def _ensure_user_pairs_preferences_table():
    """إنشاء جدول تفضيلات الأزواج لكل مستخدم داخل users.db."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS user_pairs_preferences (
            user_id INTEGER NOT NULL,
            pair_symbol TEXT NOT NULL,
            updated_at TEXT,
            PRIMARY KEY (user_id, pair_symbol)
        )
        '''
    )
    conn.commit()
    conn.close()


def _migrate_preferences_from_json_if_needed():
    """ترحيل التفضيلات القديمة من JSON إلى users.db لمرة واحدة عند الحاجة."""
    try:
        _ensure_user_pairs_preferences_table()
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM user_pairs_preferences')
        rows_count = int((c.fetchone() or [0])[0] or 0)
        if rows_count > 0:
            conn.close()
            return

        if not USER_PREFERENCES_FILE.exists():
            conn.close()
            return

        with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
            all_prefs = json.load(f)

        now_iso = datetime.now().isoformat()
        inserted = 0
        for raw_user_id, prefs in (all_prefs or {}).items():
            try:
                user_id = int(raw_user_id)
            except Exception:
                continue

            user_pairs = prefs.get('pairs', []) if isinstance(prefs, dict) else []
            if not isinstance(user_pairs, list):
                continue

            for pair in user_pairs:
                normalized = _normalize_symbol_key(pair)
                if not normalized:
                    continue
                c.execute(
                    '''
                    INSERT OR REPLACE INTO user_pairs_preferences (user_id, pair_symbol, updated_at)
                    VALUES (?, ?, ?)
                    ''',
                    (user_id, normalized, now_iso)
                )
                inserted += 1

        conn.commit()
        conn.close()

        if inserted > 0:
            backup_file = USER_PREFERENCES_FILE.with_suffix('.json.migrated')
            try:
                USER_PREFERENCES_FILE.replace(backup_file)
            except Exception:
                pass
    except Exception:
        pass


def _load_user_selected_pairs(user_id):
    """تحميل الأزواج المختارة لمستخدم واحد من قاعدة البيانات."""
    try:
        uid = int(user_id)
    except Exception:
        return []

    _migrate_preferences_from_json_if_needed()
    _ensure_user_pairs_preferences_table()

    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT pair_symbol FROM user_pairs_preferences WHERE user_id = ? ORDER BY pair_symbol ASC', (uid,))
        rows = c.fetchall()
        conn.close()
        return [str(row[0]) for row in rows if row and row[0]]
    except Exception:
        return []


def _save_user_selected_pairs(user_id, pairs):
    """حفظ الأزواج المختارة لمستخدم داخل قاعدة البيانات بشكل ذري."""
    try:
        uid = int(user_id)
    except Exception:
        return False

    if not isinstance(pairs, list):
        pairs = []

    normalized_pairs = sorted({
        _normalize_symbol_key(p) for p in pairs if _normalize_symbol_key(p)
    })

    _ensure_user_pairs_preferences_table()
    now_iso = datetime.now().isoformat()
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('DELETE FROM user_pairs_preferences WHERE user_id = ?', (uid,))
        for symbol in normalized_pairs:
            c.execute(
                '''
                INSERT OR REPLACE INTO user_pairs_preferences (user_id, pair_symbol, updated_at)
                VALUES (?, ?, ?)
                ''',
                (uid, symbol, now_iso)
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def _load_selected_pairs_distribution():
    """إرجاع توزيع عدد المستخدمين لكل زوج مختار."""
    _migrate_preferences_from_json_if_needed()
    _ensure_user_pairs_preferences_table()
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute(
            '''
            SELECT pair_symbol, COUNT(*)
            FROM user_pairs_preferences
            GROUP BY pair_symbol
            '''
        )
        rows = c.fetchall()
        conn.close()
        return {str(pair): int(count or 0) for pair, count in rows}
    except Exception:
        return {}


def _selected_pairs_union_supported():
    """تجميع كل الأزواج المختارة من المستخدمين والمسموح بتحليلها."""
    selected = {k for k, v in _load_selected_pairs_distribution().items() if int(v or 0) > 0}
    supported = {_normalize_symbol_key(s) for s in list(YF_SYMBOLS.keys()) + list(CONTINUOUS_ANALYZER_SYMBOLS)}
    selected = {s for s in selected if s in supported}
    return sorted(selected)


def _resolve_symbols_for_continuous_analyzer(max_symbols=None):
    """تحديد قائمة الرموز التي سيحللها النظام: المختارة من المستخدمين أولًا ثم الافتراضي."""
    default_symbols = [_normalize_symbol_key(symbol) for symbol in CONTINUOUS_ANALYZER_SYMBOLS if _normalize_symbol_key(symbol)]
    selected_symbols = _selected_pairs_union_supported()

    symbols = []
    seen = set()

    def _append_symbol_list(values):
        for raw_symbol in values:
            normalized_symbol = _normalize_symbol_key(raw_symbol)
            if not normalized_symbol or normalized_symbol in seen:
                continue
            seen.add(normalized_symbol)
            symbols.append(normalized_symbol)

    critical_defaults = [symbol for symbol in default_symbols if symbol in CRITICAL_SIGNAL_SYMBOLS]
    non_critical_defaults = [symbol for symbol in default_symbols if symbol not in CRITICAL_SIGNAL_SYMBOLS]

    _append_symbol_list(critical_defaults)
    _append_symbol_list(selected_symbols)
    _append_symbol_list(non_critical_defaults)

    if not symbols:
        symbols = list(default_symbols)

    if isinstance(max_symbols, int) and max_symbols > 0:
        symbols = symbols[:max_symbols]
    return symbols


def _resolve_intervals_for_symbol(symbol):
    normalized_symbol = _normalize_symbol_key(symbol)
    if normalized_symbol in HIGH_FREQUENCY_ANALYZER_SYMBOLS or normalized_symbol in CRITICAL_SIGNAL_SYMBOLS:
        base_intervals = list(HIGH_FREQUENCY_ANALYZER_INTERVALS)
    else:
        base_intervals = list(DEFAULT_ANALYZER_INTERVALS)

    if not ANALYZER_ENABLE_INTERVAL_FALLBACK:
        return base_intervals[:ANALYZER_MAX_INTERVALS_PER_SYMBOL] if base_intervals else ['1h']

    merged = []
    for interval in list(base_intervals) + list(ANALYZER_FALLBACK_INTERVALS):
        if interval not in merged:
            merged.append(interval)
    return merged[:ANALYZER_MAX_INTERVALS_PER_SYMBOL] if merged else ['1h']


def _analysis_outcome_score(item):
    if not isinstance(item, dict):
        return (-9999.0, -9999.0, -9999.0, -9999.0)

    quality_score = float(item.get('quality_score') or 0)
    rr_tp1 = float(item.get('rr_tp1') or 0)
    volatility = float(item.get('volatility') or 0)
    effective_min_quality = float(item.get('effective_min_quality') or MIN_SIGNAL_QUALITY_SCORE)
    effective_min_rr = float(item.get('effective_min_rr') or MIN_SIGNAL_RR)
    effective_max_volatility = float(item.get('effective_max_volatility') or MAX_SIGNAL_VOLATILITY)
    quality_margin = quality_score - effective_min_quality
    rr_margin = rr_tp1 - effective_min_rr
    volatility_headroom = effective_max_volatility - volatility
    score_gap = float(item.get('score_gap') or 0)
    return (quality_margin, rr_margin, volatility_headroom, score_gap)


def _select_preferred_analysis_outcome(outcomes):
    valid_outcomes = [item for item in (outcomes or []) if isinstance(item, dict)]
    if not valid_outcomes:
        return None

    generated = [item for item in valid_outcomes if item.get('ok')]
    if generated:
        return max(generated, key=_analysis_outcome_score)

    duplicates = [item for item in valid_outcomes if item.get('reason') == 'duplicate_recent_signal']
    if duplicates:
        return max(duplicates, key=_analysis_outcome_score)

    active_existing = [item for item in valid_outcomes if item.get('reason') == 'active_signal_exists']
    if active_existing:
        return max(active_existing, key=_analysis_outcome_score)

    def _sort_key(item):
        reason_rank = {
            'active_signal_exists': 0,
            'quality_below_threshold': 0,
            'volatility_above_threshold': 1,
            'rr_below_threshold': 2,
            'neutral_recommendation': 3,
            'analysis_failed': 4,
        }.get(str(item.get('reason') or ''), 9)
        quality_margin, rr_margin, volatility_headroom, score_gap = _analysis_outcome_score(item)
        return (reason_rank, -quality_margin, -rr_margin, -volatility_headroom, -score_gap)

    return sorted(valid_outcomes, key=_sort_key)[0]

DELIVERY_REPORT_DAILY_TIME = os.environ.get('DELIVERY_REPORT_DAILY_TIME', '23:55').strip() or '23:55'
DELIVERY_REPORT_CHECK_INTERVAL_SECONDS = max(15, int(os.environ.get('DELIVERY_REPORT_CHECK_INTERVAL_SECONDS', '30')))
DELIVERY_REPORT_SCHEDULER_STATE = {
    'running': False,
    'daily_time': DELIVERY_REPORT_DAILY_TIME,
    'check_interval_seconds': DELIVERY_REPORT_CHECK_INTERVAL_SECONDS,
    'last_run': None,
    'last_generated_date': None,
    'last_csv_path': None,
    'last_rows': 0,
    'last_error': None,
    'total_runs': 0
}
DELIVERY_REPORT_SCHEDULER_THREAD = None
DELIVERY_REPORT_SCHEDULER_LOCK = threading.Lock()


def _normalize_symbol_for_engine(symbol):
    """تحويل الرمز لصيغة محلل TwelveData (مثال EURUSD -> EUR/USD)."""
    clean_symbol = (symbol or '').upper().replace('-', '').replace('_', '').replace(' ', '')
    aliases = {
        'WTI': 'USOIL',
        'BRENT': 'UKOIL',
        'NGAS': 'NATGAS'
    }
    clean_symbol = aliases.get(clean_symbol, clean_symbol)

    non_fx_symbols = {
        'US30', 'NAS100', 'SPX500',
        'XAUUSD', 'XAGUSD',
        'USOIL', 'UKOIL', 'NATGAS',
        'BTCUSD', 'ETHUSD'
    }
    if clean_symbol in non_fx_symbols:
        return clean_symbol

    fx_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD'}
    if '/' in clean_symbol:
        return clean_symbol
    if len(clean_symbol) == 6 and clean_symbol[:3] in fx_currencies and clean_symbol[3:] in fx_currencies:
        return f"{clean_symbol[:3]}/{clean_symbol[3:]}"
    return clean_symbol


def _ensure_signals_table():
    """التأكد من وجود جدول الإشارات الأساسي."""
    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            signal_type TEXT,
            entry_price REAL,
            stop_loss REAL,
            take_profit_1 REAL,
            take_profit_2 REAL,
            take_profit_3 REAL,
            quality_score INTEGER DEFAULT 80,
            timeframe TEXT DEFAULT '1h',
            status TEXT DEFAULT 'active',
            result TEXT,
            current_price REAL,
            close_price REAL,
            tp1_locked INTEGER DEFAULT 0,
            tp2_locked INTEGER DEFAULT 0,
            tp3_locked INTEGER DEFAULT 0,
            activated INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def _ensure_signals_archive_table():
    """إنشاء جدول أرشيف الصفقات المنتهية للاحتفاظ بالنتائج والمقارنات والتقارير."""
    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS signals_archive (
            signal_id INTEGER PRIMARY KEY,
            symbol TEXT,
            signal_type TEXT,
            entry_price REAL,
            stop_loss REAL,
            take_profit_1 REAL,
            take_profit_2 REAL,
            take_profit_3 REAL,
            quality_score INTEGER,
            timeframe TEXT,
            status TEXT,
            result TEXT,
            current_price REAL,
            close_price REAL,
            tp1_locked INTEGER DEFAULT 0,
            tp2_locked INTEGER DEFAULT 0,
            tp3_locked INTEGER DEFAULT 0,
            activated INTEGER DEFAULT 1,
            created_at TEXT,
            archived_at TEXT,
            archive_reason TEXT
        )
    ''')
    conn.commit()
    conn.close()


def _deduplicate_signals_continuously():
    """إزالة الإشارات المكررة بشكل دوري مع الاحتفاظ بأحدث سجل."""
    _ensure_signals_table()
    lock_acquired = VIP_SIGNALS_DB_LOCK.acquire(timeout=2)
    if not lock_acquired:
        return 0

    try:
        conn = sqlite3.connect('vip_signals.db')
        c = conn.cursor()

        c.execute('SELECT COUNT(*) FROM signals')
        before_count = c.fetchone()[0] or 0

        c.execute('''
            DELETE FROM signals
            WHERE status = 'active'
              AND signal_id NOT IN (
                  SELECT MAX(signal_id)
                  FROM signals
                  WHERE status = 'active'
                  GROUP BY symbol
              )
        ''')

        c.execute('''
            DELETE FROM signals
            WHERE signal_id NOT IN (
                SELECT MAX(signal_id)
                FROM signals
                GROUP BY symbol, signal_type, COALESCE(timeframe, '1h'), strftime('%Y-%m-%d %H', created_at)
            )
        ''')

        c.execute('''
            SELECT signal_id, symbol, signal_type, COALESCE(timeframe, '1h') AS timeframe, COALESCE(entry_price, 0) AS entry_price
            FROM signals
            WHERE status = 'active'
            ORDER BY signal_id DESC
        ''')
        active_rows = c.fetchall()
        kept_rows = []
        duplicate_ids = []

        for row in active_rows:
            signal_id, symbol, signal_type, timeframe, entry_price = row
            entry_val = float(entry_price or 0)
            tolerance = max(0.0005, abs(entry_val) * 0.0015)

            is_duplicate = False
            for kept in kept_rows:
                if kept['symbol'] != symbol:
                    continue
                if kept['signal_type'] != signal_type:
                    continue
                if kept['timeframe'] != timeframe:
                    continue
                if abs(float(kept['entry_price']) - entry_val) <= tolerance:
                    is_duplicate = True
                    break

            if is_duplicate:
                duplicate_ids.append(signal_id)
            else:
                kept_rows.append({
                    'signal_id': signal_id,
                    'symbol': symbol,
                    'signal_type': signal_type,
                    'timeframe': timeframe,
                    'entry_price': entry_val
                })

        if duplicate_ids:
            placeholders = ','.join(['?'] * len(duplicate_ids))
            c.execute(f"DELETE FROM signals WHERE signal_id IN ({placeholders})", duplicate_ids)

        conn.commit()
        c.execute('SELECT COUNT(*) FROM signals')
        after_count = c.fetchone()[0] or 0
        conn.close()
        return max(0, before_count - after_count)
    finally:
        VIP_SIGNALS_DB_LOCK.release()


def _compute_risk_reward(entry_price, stop_loss, take_profit_1):
    """حساب نسبة المخاطرة/العائد للهدف الأول بشكل آمن."""
    try:
        entry_val = float(entry_price or 0)
        sl_val = float(stop_loss or 0)
        tp1_val = float(take_profit_1 or 0)
        risk = abs(entry_val - sl_val)
        reward = abs(tp1_val - entry_val)
        if risk <= 0:
            return 0.0
        return round(reward / risk, 2)
    except Exception:
        return 0.0


def _calculate_quality_score(analysis_result):
    """تقدير جودة الإشارة من نتيجة التحليل عبر نموذج نقاط متعدد العوامل."""
    recommendation = str(analysis_result.get('recommendation', analysis_result.get('signal', '')))
    confidence = str(analysis_result.get('confidence', ''))

    score = 50

    # 1) مستوى الثقة النصي
    conf_upper = confidence.upper()
    if 'قوي' in recommendation or 'STRONG' in recommendation.upper() or 'HIGH' in conf_upper or 'عالية' in confidence or 'عالي' in confidence:
        score += 20
    elif 'محتمل' in recommendation or 'LOW' in conf_upper or 'منخفض' in confidence:
        score -= 8
    elif 'MEDIUM' in conf_upper or 'متوسطة' in confidence or 'متوسط' in confidence:
        score += 6

    # 2) قوة التفوق بين الشراء/البيع من المحلل
    try:
        buy_score = float(analysis_result.get('buy_score') or 0)
        sell_score = float(analysis_result.get('sell_score') or 0)
        score_gap = float(analysis_result.get('score_gap') or abs(buy_score - sell_score))
        dominant_score = max(buy_score, sell_score)

        if dominant_score >= 4:
            score += 12
        elif dominant_score >= 3:
            score += 8
        elif dominant_score >= 2.5:
            score += 4

        if score_gap >= 2:
            score += 10
        elif score_gap >= 1:
            score += 6
        elif score_gap < 0.4:
            score -= 8
    except Exception:
        pass

    # 3) نسبة العائد إلى المخاطرة
    rr_tp1 = analysis_result.get('risk_reward_tp1')
    try:
        rr_tp1 = float(rr_tp1) if rr_tp1 is not None else _compute_risk_reward(
            analysis_result.get('entry_point'),
            analysis_result.get('stop_loss'),
            analysis_result.get('take_profit1')
        )
    except Exception:
        rr_tp1 = 0.0

    if rr_tp1 >= 2.0:
        score += 16
    elif rr_tp1 >= 1.6:
        score += 12
    elif rr_tp1 >= 1.35:
        score += 8
    elif rr_tp1 >= 1.2:
        score += 3
    else:
        score -= 14

    # 4) فلتر التقلبات
    try:
        volatility = float(analysis_result.get('volatility') or 0)
        if volatility >= 4.5:
            score -= 16
        elif volatility >= MAX_SIGNAL_VOLATILITY:
            score -= 10
        elif 0.4 <= volatility <= 2.8:
            score += 6
    except Exception:
        pass

    if 'حياد' in recommendation or 'NEUTRAL' in recommendation.upper():
        score = min(score, 58)

    return max(0, min(100, int(round(score))))


def _extract_signal_type(recommendation_text):
    text = str(recommendation_text or '').upper()
    if 'BUY' in text or 'شراء' in text:
        return 'buy'
    if 'SELL' in text or 'بيع' in text:
        return 'sell'
    return None


def _normalize_signal_type(signal_type, default='buy'):
    value = str(signal_type or '').strip().lower()
    if value == 'sell':
        return 'sell'
    if value == 'buy':
        return 'buy'
    return default


def _signal_exists_recently(symbol, signal_type, timeframe, entry_price):
    try:
        entry_val = float(entry_price or 0)
    except Exception:
        entry_val = 0.0

    # 0.15% من السعر أو 0.0005 كحد أدنى
    tolerance = max(0.0005, abs(entry_val) * 0.0015)

    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    c.execute('''
        SELECT 1
        FROM signals
        WHERE symbol = ?
          AND signal_type = ?
          AND COALESCE(timeframe, '1h') = ?
          AND ABS(COALESCE(entry_price, 0) - ?) <= ?
          AND datetime(created_at) >= datetime('now', '-12 hours')
        LIMIT 1
    ''', (symbol, signal_type, timeframe, entry_val, tolerance))
    exists = c.fetchone() is not None
    conn.close()
    return exists


def _has_active_signal_for_symbol(symbol):
    normalized_symbol = _normalize_symbol_key(symbol)
    if not normalized_symbol:
        return False

    try:
        conn = sqlite3.connect('vip_signals.db')
        c = conn.cursor()
        c.execute('''
            SELECT 1
            FROM signals
            WHERE symbol = ?
              AND status = 'active'
            LIMIT 1
        ''', (normalized_symbol,))
        exists = c.fetchone() is not None
        conn.close()
        return exists
    except Exception:
        return False


def _get_adaptive_thresholds(symbol, timeframe='1h'):
    """ضبط حدود الاختيار تلقائياً حسب أداء الزوج/الفريم في الصفقات المغلقة."""
    adaptive = {
        'min_quality_score': int(MIN_SIGNAL_QUALITY_SCORE),
        'min_rr': float(MIN_SIGNAL_RR),
        'max_volatility': float(MAX_SIGNAL_VOLATILITY),
        'sample_size': 0,
        'win_rate': 0.0,
        'recent_win_rate': 0.0,
        'mode': 'baseline'
    }

    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT result, quality_score
            FROM signals
            WHERE symbol = ?
              AND COALESCE(timeframe, '1h') = ?
              AND status = 'closed'
              AND result IN ('win', 'loss')
            ORDER BY signal_id DESC
            LIMIT 40
        ''', (symbol, timeframe))
        rows = c.fetchall()
        conn.close()
    except Exception:
        rows = []

    if not rows:
        return adaptive

    sample_size = len(rows)
    wins = sum(1 for row in rows if str(row['result']).lower() == 'win')
    win_rate = wins / sample_size if sample_size > 0 else 0.0

    recent_rows = rows[:10]
    recent_size = len(recent_rows)
    recent_wins = sum(1 for row in recent_rows if str(row['result']).lower() == 'win')
    recent_win_rate = (recent_wins / recent_size) if recent_size > 0 else 0.0

    avg_quality = 0.0
    try:
        avg_quality = sum(float(row['quality_score'] or 0) for row in rows) / sample_size
    except Exception:
        avg_quality = 0.0

    min_quality_score = float(MIN_SIGNAL_QUALITY_SCORE)
    min_rr = float(MIN_SIGNAL_RR)
    max_volatility = float(MAX_SIGNAL_VOLATILITY)
    mode = 'baseline'

    # لا نطبق التكيف إلا بعينة كافية
    if sample_size >= 8:
        if win_rate >= 0.68 and recent_win_rate >= 0.6:
            # أداء جيد => مرونة بسيطة لزيادة الفرص
            min_quality_score -= 4
            min_rr -= 0.10
            max_volatility += 0.35
            mode = 'aggressive'
        elif win_rate <= 0.50 or recent_win_rate <= 0.40:
            # أداء ضعيف => تشديد الفلترة
            min_quality_score += 4
            min_rr += 0.10
            max_volatility -= 0.30
            mode = 'defensive'

        # طبقة ضبط إضافية للأداء الحديث
        if sample_size >= 15:
            if recent_win_rate <= 0.30:
                min_quality_score += 3
                min_rr += 0.08
                max_volatility -= 0.15
                mode = 'defensive'
            elif recent_win_rate >= 0.75 and avg_quality >= 82:
                min_quality_score -= 2
                min_rr -= 0.05
                max_volatility += 0.15
                mode = 'aggressive'

    adaptive['min_quality_score'] = int(max(55, min(92, round(min_quality_score))))
    adaptive['min_rr'] = round(max(1.00, min(2.20, float(min_rr))), 2)
    adaptive['max_volatility'] = round(max(2.20, min(5.20, float(max_volatility))), 2)
    adaptive['sample_size'] = sample_size
    adaptive['win_rate'] = round(win_rate, 3)
    adaptive['recent_win_rate'] = round(recent_win_rate, 3)
    adaptive['mode'] = mode
    return adaptive


def _build_adaptive_thresholds_overview(limit_rows=30):
    """إنشاء نظرة عامة عن حدود الاختيار التكيفية لكل زوج/فريم (للأدمن)."""
    pair_timeframes = set()

    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT symbol, COALESCE(timeframe, '1h') AS timeframe
            FROM signals
            GROUP BY symbol, COALESCE(timeframe, '1h')
            ORDER BY MAX(signal_id) DESC
            LIMIT 120
        ''')
        rows = c.fetchall()
        conn.close()

        for row in rows:
            symbol = str(row['symbol'] or '').upper().strip()
            timeframe = str(row['timeframe'] or '1h').strip()
            if symbol:
                pair_timeframes.add((symbol, timeframe))
    except Exception:
        pass

    # ضمان وجود الأزواج الافتراضية حتى لو لم تتوفر بيانات تاريخية
    for symbol in CONTINUOUS_ANALYZER_SYMBOLS:
        normalized_symbol = str(symbol or '').upper().replace('/', '').strip()
        if normalized_symbol:
            pair_timeframes.add((normalized_symbol, '1h'))

    rows_out = []
    for symbol, timeframe in sorted(pair_timeframes):
        adaptive = _get_adaptive_thresholds(symbol, timeframe)
        rows_out.append({
            'symbol': symbol,
            'timeframe': timeframe,
            'mode': adaptive.get('mode', 'baseline'),
            'sample_size': int(adaptive.get('sample_size', 0) or 0),
            'win_rate': float(adaptive.get('win_rate', 0) or 0),
            'recent_win_rate': float(adaptive.get('recent_win_rate', 0) or 0),
            'min_quality_score': int(adaptive.get('min_quality_score', MIN_SIGNAL_QUALITY_SCORE) or MIN_SIGNAL_QUALITY_SCORE),
            'min_rr': float(adaptive.get('min_rr', MIN_SIGNAL_RR) or MIN_SIGNAL_RR),
            'max_volatility': float(adaptive.get('max_volatility', MAX_SIGNAL_VOLATILITY) or MAX_SIGNAL_VOLATILITY)
        })

    rows_out.sort(key=lambda item: (item.get('sample_size', 0), item.get('win_rate', 0)), reverse=True)
    rows_out = rows_out[:max(1, int(limit_rows or 30))]

    tracked_pairs = len(rows_out)
    defensive_pairs = sum(1 for row in rows_out if row.get('mode') == 'defensive')
    aggressive_pairs = sum(1 for row in rows_out if row.get('mode') == 'aggressive')
    baseline_pairs = tracked_pairs - defensive_pairs - aggressive_pairs
    avg_win_rate = round(
        (sum(float(row.get('win_rate') or 0) for row in rows_out) / tracked_pairs), 3
    ) if tracked_pairs > 0 else 0.0

    return {
        'summary': {
            'tracked_pairs': tracked_pairs,
            'defensive_pairs': defensive_pairs,
            'aggressive_pairs': aggressive_pairs,
            'baseline_pairs': baseline_pairs,
            'avg_win_rate': avg_win_rate
        },
        'rows': rows_out
    }


def _insert_generated_signal(signal_row):
    _ensure_signals_table()
    signal_row['symbol'] = _normalize_symbol_key(signal_row.get('symbol'))
    signal_row['signal_type'] = _normalize_signal_type(signal_row.get('signal_type'))
    with VIP_SIGNALS_DB_LOCK:
        conn = sqlite3.connect('vip_signals.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO signals (
                symbol, signal_type, entry_price, stop_loss,
                take_profit_1, take_profit_2, take_profit_3,
                quality_score, timeframe, status, result,
                current_price, close_price, tp1_locked, tp2_locked, tp3_locked, activated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?, NULL, 0, 0, 0, 1)
        ''', (
            signal_row['symbol'],
            signal_row['signal_type'],
            signal_row['entry_price'],
            signal_row['stop_loss'],
            signal_row['take_profit_1'],
            signal_row['take_profit_2'],
            signal_row['take_profit_3'],
            signal_row['quality_score'],
            signal_row['timeframe'],
            signal_row['entry_price']
        ))
        conn.commit()
        signal_id = c.lastrowid

        c.execute('''
            DELETE FROM signals
            WHERE symbol = ?
              AND status = 'active'
              AND signal_id <> ?
                ''', (signal_row['symbol'], signal_id))
        conn.commit()
        conn.close()
        return signal_id


def _ensure_signal_payload_persisted(signal_payload, default_timeframe='1h'):
    """حفظ حمولة إشارة مرسلة يدوياً/من توصية داخل قاعدة الإشارات لضمان ظهورها في الواجهة."""
    try:
        payload = signal_payload or {}
        symbol = str(payload.get('symbol') or payload.get('pair') or '').upper().replace('/', '').strip()
        if not symbol:
            return None

        signal_type = str(payload.get('signal') or payload.get('signal_type') or payload.get('rec') or '').lower().strip()
        if signal_type not in ('buy', 'sell'):
            return None

        timeframe = str(payload.get('timeframe') or payload.get('tf') or default_timeframe or '1h').strip() or '1h'

        entry = payload.get('entry')
        if entry in (None, '', 0):
            entry = payload.get('entry_price')
        entry = float(entry or 0)
        if entry <= 0:
            return None

        stop_loss = payload.get('sl')
        if stop_loss in (None, '', 0):
            stop_loss = payload.get('stop_loss')
        stop_loss = float(stop_loss or 0)

        tp1 = payload.get('tp1')
        if tp1 in (None, '', 0):
            tp1 = payload.get('take_profit_1')
        tp1 = float(tp1 or 0)

        tp2 = payload.get('tp2')
        if tp2 in (None, '', 0):
            tp2 = payload.get('take_profit_2')
        tp2 = float(tp2 or 0)

        tp3 = payload.get('tp3')
        if tp3 in (None, '', 0):
            tp3 = payload.get('take_profit_3')
        tp3 = float(tp3 or 0)

        if signal_type == 'buy':
            if stop_loss <= 0:
                stop_loss = round(entry * 0.995, 6)
            if tp1 <= 0:
                tp1 = round(entry * 1.003, 6)
            if tp2 <= 0:
                tp2 = round(entry * 1.006, 6)
            if tp3 <= 0:
                tp3 = round(entry * 1.009, 6)
        else:
            if stop_loss <= 0:
                stop_loss = round(entry * 1.005, 6)
            if tp1 <= 0:
                tp1 = round(entry * 0.997, 6)
            if tp2 <= 0:
                tp2 = round(entry * 0.994, 6)
            if tp3 <= 0:
                tp3 = round(entry * 0.991, 6)

        quality_score = int(payload.get('quality_score') or 75)

        if _has_active_signal_for_symbol(symbol):
            return None

        if _signal_exists_recently(symbol, signal_type, timeframe, entry):
            return None

        signal_row = {
            'symbol': symbol,
            'signal_type': signal_type,
            'entry_price': float(entry),
            'stop_loss': float(stop_loss),
            'take_profit_1': float(tp1),
            'take_profit_2': float(tp2),
            'take_profit_3': float(tp3),
            'quality_score': quality_score,
            'timeframe': timeframe,
            'timestamp': payload.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return _insert_generated_signal(signal_row)
    except Exception:
        return None


def _analyze_and_generate_signal(symbol, interval='1h', force_live=False, return_diagnostics=False):
    """تحليل رمز واحد وتوليد إشارة إذا كانت صالحة وغير مكررة."""
    def _reject(reason, **extra):
        if not return_diagnostics:
            return None
        payload = {
            'ok': False,
            'symbol': str(symbol or '').upper().replace('/', ''),
            'interval': interval,
            'reason': reason
        }
        payload.update(extra)
        return payload

    try:
        from advanced_analyzer_engine import perform_full_analysis  # type: ignore
    except ImportError:
        analyzer_path = Path(__file__).parent / 'advanced_analyzer_engine.py'
        spec = importlib.util.spec_from_file_location('advanced_analyzer_engine', str(analyzer_path))
        analyzer_module = importlib.util.module_from_spec(spec)
        sys.modules['advanced_analyzer_engine'] = analyzer_module
        spec.loader.exec_module(analyzer_module)
        perform_full_analysis = analyzer_module.perform_full_analysis

    engine_symbol = _normalize_symbol_for_engine(symbol)
    result = perform_full_analysis(engine_symbol, interval, force_live=force_live)

    if not result or not result.get('success'):
        return _reject('analysis_failed', error=None if not result else result.get('error'))

    recommendation = result.get('recommendation', result.get('signal', ''))
    signal_type = _extract_signal_type(recommendation)
    if not signal_type:
        return _reject(
            'neutral_recommendation',
            recommendation=recommendation,
            confidence=result.get('confidence'),
            buy_score=result.get('buy_score'),
            sell_score=result.get('sell_score'),
            score_gap=result.get('score_gap'),
            volatility=result.get('volatility')
        )

    entry_price = result.get('entry_point')
    if entry_price in (None, 0):
        return _reject('missing_entry_price', recommendation=recommendation, signal_type=signal_type)

    stop_loss = float(result.get('stop_loss') or 0)
    take_profit_1 = float(result.get('take_profit1') or 0)
    take_profit_2 = float(result.get('take_profit2') or 0)
    take_profit_3 = float(result.get('take_profit3') or 0)
    entry_price = float(entry_price)

    if stop_loss <= 0 or take_profit_1 <= 0 or take_profit_2 <= 0 or take_profit_3 <= 0:
        return _reject(
            'invalid_levels',
            recommendation=recommendation,
            signal_type=signal_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3
        )

    if signal_type == 'buy':
        if not (stop_loss < entry_price < take_profit_1 <= take_profit_2 <= take_profit_3):
            return _reject(
                'buy_structure_invalid',
                recommendation=recommendation,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                take_profit_3=take_profit_3
            )
    elif signal_type == 'sell':
        if not (stop_loss > entry_price > take_profit_1 >= take_profit_2 >= take_profit_3):
            return _reject(
                'sell_structure_invalid',
                recommendation=recommendation,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                take_profit_3=take_profit_3
            )

    normalized_symbol = symbol.upper().replace('/', '')
    adaptive_thresholds = _get_adaptive_thresholds(normalized_symbol, interval)
    min_quality_score = int(adaptive_thresholds.get('min_quality_score', MIN_SIGNAL_QUALITY_SCORE))
    min_rr = float(adaptive_thresholds.get('min_rr', MIN_SIGNAL_RR))
    max_volatility = float(adaptive_thresholds.get('max_volatility', MAX_SIGNAL_VOLATILITY))

    active_signals_now = _count_current_active_signals()
    relaxed_mode = bool(
        RELAX_SIGNAL_FILTERS_WHEN_EMPTY
        and active_signals_now <= RELAX_SIGNAL_FILTERS_IF_ACTIVE_COUNT_LE
    )
    effective_min_quality = min_quality_score
    effective_min_rr = min_rr
    effective_max_volatility = max_volatility
    if relaxed_mode:
        effective_min_quality = min(min_quality_score, int(MIN_SIGNAL_QUALITY_WHEN_EMPTY))
        effective_min_rr = min(min_rr, float(MIN_SIGNAL_RR_WHEN_EMPTY))
        effective_max_volatility = max(max_volatility, float(MAX_SIGNAL_VOLATILITY_WHEN_EMPTY))

    critical_relaxed_mode = bool(normalized_symbol in CRITICAL_SIGNAL_SYMBOLS)
    if critical_relaxed_mode:
        critical_max_volatility = float(CRITICAL_SIGNAL_MAX_VOLATILITY_BY_SYMBOL.get(normalized_symbol, CRITICAL_SIGNAL_MAX_VOLATILITY))
        effective_min_quality = min(effective_min_quality, int(CRITICAL_SIGNAL_MIN_QUALITY))
        effective_min_rr = min(effective_min_rr, float(CRITICAL_SIGNAL_MIN_RR))
        effective_max_volatility = max(effective_max_volatility, critical_max_volatility)

    adaptive_mode = (
        'critical_relaxed' if critical_relaxed_mode else
        'relaxed_empty' if relaxed_mode else
        adaptive_thresholds.get('mode')
    )

    rr_tp1 = _compute_risk_reward(entry_price, stop_loss, take_profit_1)
    if rr_tp1 < effective_min_rr:
        return _reject(
            'rr_below_threshold',
            recommendation=recommendation,
            signal_type=signal_type,
            quality_score=_calculate_quality_score(result),
            rr_tp1=rr_tp1,
            effective_min_quality=effective_min_quality,
            effective_min_rr=effective_min_rr,
            effective_max_volatility=effective_max_volatility,
            score_gap=result.get('score_gap'),
            adaptive_mode=adaptive_mode,
            active_signals_now=active_signals_now
        )

    if critical_relaxed_mode and rr_tp1 >= float(CRITICAL_SIGNAL_STRONG_RR_TRIGGER):
        effective_min_quality = min(effective_min_quality, int(CRITICAL_SIGNAL_MIN_QUALITY_STRONG_RR))

    quality_score = _calculate_quality_score(result)
    if quality_score < effective_min_quality:
        return _reject(
            'quality_below_threshold',
            recommendation=recommendation,
            signal_type=signal_type,
            quality_score=quality_score,
            effective_min_quality=effective_min_quality,
            rr_tp1=rr_tp1,
            effective_min_rr=effective_min_rr,
            effective_max_volatility=effective_max_volatility,
            adaptive_mode=adaptive_mode,
            active_signals_now=active_signals_now,
            confidence=result.get('confidence'),
            buy_score=result.get('buy_score'),
            sell_score=result.get('sell_score'),
            score_gap=result.get('score_gap')
        )

    try:
        volatility = float(result.get('volatility') or 0)
    except Exception:
        volatility = 0.0
    if volatility > effective_max_volatility and quality_score < 90:
        return _reject(
            'volatility_above_threshold',
            recommendation=recommendation,
            signal_type=signal_type,
            quality_score=quality_score,
            rr_tp1=rr_tp1,
            volatility=volatility,
            effective_max_volatility=effective_max_volatility,
            effective_min_quality=effective_min_quality,
            effective_min_rr=effective_min_rr,
            score_gap=result.get('score_gap'),
            adaptive_mode=adaptive_mode,
            active_signals_now=active_signals_now
        )

    if _has_active_signal_for_symbol(normalized_symbol):
        return _reject(
            'active_signal_exists',
            recommendation=recommendation,
            signal_type=signal_type,
            quality_score=quality_score,
            rr_tp1=rr_tp1,
            volatility=volatility,
            effective_min_quality=effective_min_quality,
            effective_min_rr=effective_min_rr,
            effective_max_volatility=effective_max_volatility,
            score_gap=result.get('score_gap'),
            adaptive_mode=adaptive_mode,
            active_signals_now=active_signals_now
        )

    if _signal_exists_recently(normalized_symbol, signal_type, interval, entry_price):
        return _reject(
            'duplicate_recent_signal',
            recommendation=recommendation,
            signal_type=signal_type,
            quality_score=quality_score,
            rr_tp1=rr_tp1,
            volatility=volatility,
            effective_min_quality=effective_min_quality,
            effective_min_rr=effective_min_rr,
            effective_max_volatility=effective_max_volatility,
            score_gap=result.get('score_gap'),
            adaptive_mode=adaptive_mode,
            active_signals_now=active_signals_now
        )

    signal_row = {
        'symbol': normalized_symbol,
        'signal_type': signal_type,
        'entry_price': float(entry_price),
        'stop_loss': stop_loss,
        'take_profit_1': take_profit_1,
        'take_profit_2': take_profit_2,
        'take_profit_3': take_profit_3,
        'quality_score': int(quality_score),
        'timeframe': interval,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'risk_reward_tp1': rr_tp1,
        'confidence': str(result.get('confidence') or ''),
        'score_gap': float(result.get('score_gap') or 0),
        'volatility': volatility,
        'adaptive_mode': adaptive_mode,
        'adaptive_min_quality_score': effective_min_quality,
        'adaptive_min_rr': effective_min_rr,
        'adaptive_max_volatility': effective_max_volatility,
        'adaptive_sample_size': adaptive_thresholds.get('sample_size', 0),
        'adaptive_win_rate': adaptive_thresholds.get('win_rate', 0)
    }
    signal_id = _insert_generated_signal(signal_row)
    signal_row['signal_id'] = signal_id
    signal_row['signal'] = signal_type
    signal_row['rec'] = signal_type.upper()
    signal_row['sl'] = signal_row['stop_loss']
    signal_row['tp1'] = signal_row['take_profit_1']
    signal_row['tp2'] = signal_row['take_profit_2']
    signal_row['tp3'] = signal_row['take_profit_3']
    signal_row['entry'] = signal_row['entry_price']
    if return_diagnostics:
        return {
            'ok': True,
            'reason': 'generated',
            'symbol': normalized_symbol,
            'interval': interval,
            'signal': signal_row,
            'quality_score': quality_score,
            'rr_tp1': rr_tp1,
            'volatility': volatility,
            'effective_min_quality': effective_min_quality,
            'effective_min_rr': effective_min_rr,
            'effective_max_volatility': effective_max_volatility,
            'score_gap': result.get('score_gap'),
            'active_signals_now': active_signals_now,
            'adaptive_mode': adaptive_mode
        }
    return signal_row


def _create_bootstrap_signal_if_empty(symbol='XAUUSD', timeframe='1h'):
    """إنشاء إشارة Bootstrap واحدة إذا كانت القاعدة فارغة لتفادي صفحة إشارات خالية."""
    if _count_recent_active_signals() > 0:
        return None

    normalized_symbol = str(symbol or 'XAUUSD').upper().replace('/', '')
    live_price = get_live_price(normalized_symbol)
    if not live_price:
        fallback_prices = {
            'XAUUSD': 2050.0,
            'BTCUSD': 60000.0,
            'EURUSD': 1.08
        }
        live_price = fallback_prices.get(normalized_symbol, 100.0)

    entry = float(live_price)
    stop_loss = round(entry * 0.995, 6)
    tp1 = round(entry * 1.003, 6)
    tp2 = round(entry * 1.006, 6)
    tp3 = round(entry * 1.009, 6)

    if _signal_exists_recently(normalized_symbol, 'buy', timeframe, entry):
        return None

    rr_tp1 = _compute_risk_reward(entry, stop_loss, tp1)
    signal_row = {
        'symbol': normalized_symbol,
        'signal_type': 'buy',
        'entry_price': entry,
        'stop_loss': stop_loss,
        'take_profit_1': tp1,
        'take_profit_2': tp2,
        'take_profit_3': tp3,
        'quality_score': max(40, int(MIN_SIGNAL_QUALITY_WHEN_EMPTY)),
        'timeframe': timeframe,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'risk_reward_tp1': rr_tp1,
        'confidence': 'bootstrap',
        'score_gap': 0.0,
        'volatility': 0.0,
        'adaptive_mode': 'bootstrap_empty',
        'adaptive_min_quality_score': int(MIN_SIGNAL_QUALITY_WHEN_EMPTY),
        'adaptive_min_rr': float(MIN_SIGNAL_RR_WHEN_EMPTY),
        'adaptive_max_volatility': float(MAX_SIGNAL_VOLATILITY_WHEN_EMPTY),
        'adaptive_sample_size': 0,
        'adaptive_win_rate': 0
    }

    signal_id = _insert_generated_signal(signal_row)
    signal_row['signal_id'] = signal_id
    signal_row['signal'] = 'buy'
    signal_row['rec'] = 'BUY'
    signal_row['sl'] = signal_row['stop_loss']
    signal_row['tp1'] = signal_row['take_profit_1']
    signal_row['tp2'] = signal_row['take_profit_2']
    signal_row['tp3'] = signal_row['take_profit_3']
    signal_row['entry'] = signal_row['entry_price']
    return signal_row


def _continuous_analyzer_loop():
    """حلقة التحليل والبث المستمر لجميع الأزواج المتاحة."""
    while CONTINUOUS_ANALYZER_STATE.get('running'):
        CONTINUOUS_ANALYZER_STATE['last_cycle_started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'refreshing_active_signals'
        CONTINUOUS_ANALYZER_STATE['current_symbol'] = None
        CONTINUOUS_ANALYZER_STATE['current_interval'] = None
        CONTINUOUS_ANALYZER_STATE['current_symbol_index'] = 0
        CONTINUOUS_ANALYZER_STATE['symbols_total'] = 0
        analyzed_count = 0
        generated_count = 0
        broadcast_count = 0
        deduplicated_count = 0
        failed_symbols = []
        no_signal_count = 0
        rejection_reasons = {}
        rejection_samples = []

        try:
            _refresh_active_signal_statuses()
            symbols_to_analyze = _resolve_symbols_for_continuous_analyzer()
            CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'analyzing_symbols'
            CONTINUOUS_ANALYZER_STATE['symbols_total'] = len(symbols_to_analyze)
            for index, symbol in enumerate(symbols_to_analyze, start=1):
                if not CONTINUOUS_ANALYZER_STATE.get('running'):
                    break

                CONTINUOUS_ANALYZER_STATE['current_symbol'] = symbol
                CONTINUOUS_ANALYZER_STATE['current_symbol_index'] = index

                try:
                    analyzed_count += 1
                    interval_outcomes = []
                    for interval in _resolve_intervals_for_symbol(symbol):
                        CONTINUOUS_ANALYZER_STATE['current_interval'] = interval
                        candidate_outcome = _analyze_and_generate_signal(symbol, interval=interval, return_diagnostics=True)
                        if isinstance(candidate_outcome, dict):
                            candidate_outcome['symbol'] = symbol
                            candidate_outcome['interval'] = interval
                        interval_outcomes.append(candidate_outcome)

                    analysis_outcome = _select_preferred_analysis_outcome(interval_outcomes)

                    if not analysis_outcome or not analysis_outcome.get('ok'):
                        no_signal_count += 1
                        reason = str((analysis_outcome or {}).get('reason') or 'no_signal')
                        rejection_reasons[reason] = int(rejection_reasons.get(reason, 0) or 0) + 1
                        if len(rejection_samples) < 8:
                            rejection_samples.append({
                                'symbol': symbol,
                                'interval': (analysis_outcome or {}).get('interval'),
                                'tried_intervals': [item.get('interval') for item in interval_outcomes if isinstance(item, dict) and item.get('interval')],
                                'reason': reason,
                                'recommendation': (analysis_outcome or {}).get('recommendation'),
                                'quality_score': (analysis_outcome or {}).get('quality_score'),
                                'effective_min_quality': (analysis_outcome or {}).get('effective_min_quality'),
                                'rr_tp1': (analysis_outcome or {}).get('rr_tp1'),
                                'effective_min_rr': (analysis_outcome or {}).get('effective_min_rr'),
                                'volatility': (analysis_outcome or {}).get('volatility'),
                                'effective_max_volatility': (analysis_outcome or {}).get('effective_max_volatility'),
                                'adaptive_mode': (analysis_outcome or {}).get('adaptive_mode'),
                                'active_signals_now': (analysis_outcome or {}).get('active_signals_now')
                            })
                        continue
                    signal_data = analysis_outcome.get('signal') or {}

                    generated_count += 1
                    send_result = telegram_sender.send_signal_to_subscribers(
                        signal_data,
                        quality_score=signal_data.get('quality_score', 80)
                    )
                    formatted_message = telegram_sender.format_signal_message(signal_data)
                    targets_result = telegram_sender.send_broadcast_to_configured_targets(formatted_message)
                    if isinstance(send_result, dict):
                        broadcast_count += int(send_result.get('sent_count', 0) or 0)
                    if isinstance(targets_result, dict):
                        broadcast_count += int(targets_result.get('sent_count', 0) or 0)
                except Exception as symbol_error:
                    failed_symbols.append(f"{symbol}:{symbol_error}")

                time.sleep(1)

            CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'bootstrap_if_empty'
            CONTINUOUS_ANALYZER_STATE['current_symbol'] = None
            CONTINUOUS_ANALYZER_STATE['current_interval'] = None
            if generated_count == 0 and _count_recent_active_signals() == 0:
                bootstrap_signal = _create_bootstrap_signal_if_empty(symbol='XAUUSD', timeframe='1h')
                if bootstrap_signal:
                    generated_count += 1
                    send_result = telegram_sender.send_signal_to_subscribers(
                        bootstrap_signal,
                        quality_score=bootstrap_signal.get('quality_score', 50)
                    )
                    formatted_message = telegram_sender.format_signal_message(bootstrap_signal)
                    targets_result = telegram_sender.send_broadcast_to_configured_targets(formatted_message)
                    if isinstance(send_result, dict):
                        broadcast_count += int(send_result.get('sent_count', 0) or 0)
                    if isinstance(targets_result, dict):
                        broadcast_count += int(targets_result.get('sent_count', 0) or 0)

            CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'cleanup'
            deduplicated_count = _deduplicate_signals_continuously()
            deduplicated_count += archive_and_cleanup_closed_signals()

            CONTINUOUS_ANALYZER_STATE['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'sleeping'
            CONTINUOUS_ANALYZER_STATE['current_symbol'] = None
            CONTINUOUS_ANALYZER_STATE['current_interval'] = None
            CONTINUOUS_ANALYZER_STATE['current_symbol_index'] = 0
            CONTINUOUS_ANALYZER_STATE['last_analyzed_count'] = analyzed_count
            CONTINUOUS_ANALYZER_STATE['last_failed_count'] = len(failed_symbols)
            CONTINUOUS_ANALYZER_STATE['last_no_signal_count'] = no_signal_count
            CONTINUOUS_ANALYZER_STATE['last_failed_symbols'] = failed_symbols[:8]
            CONTINUOUS_ANALYZER_STATE['last_rejection_reasons'] = rejection_reasons
            CONTINUOUS_ANALYZER_STATE['last_rejection_samples'] = rejection_samples
            CONTINUOUS_ANALYZER_STATE['last_active_signals_count'] = _count_current_active_signals()
            CONTINUOUS_ANALYZER_STATE['last_new_signals'] = generated_count
            CONTINUOUS_ANALYZER_STATE['last_deduplicated'] = deduplicated_count
            CONTINUOUS_ANALYZER_STATE['total_generated'] += generated_count
            CONTINUOUS_ANALYZER_STATE['total_broadcasted'] += broadcast_count
            CONTINUOUS_ANALYZER_STATE['last_error'] = None if not failed_symbols else '; '.join(failed_symbols[:8])
        except Exception as e:
            CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'error'
            CONTINUOUS_ANALYZER_STATE['last_analyzed_count'] = analyzed_count
            CONTINUOUS_ANALYZER_STATE['last_failed_count'] = len(failed_symbols)
            CONTINUOUS_ANALYZER_STATE['last_no_signal_count'] = no_signal_count
            CONTINUOUS_ANALYZER_STATE['last_failed_symbols'] = failed_symbols[:8]
            CONTINUOUS_ANALYZER_STATE['last_rejection_reasons'] = rejection_reasons
            CONTINUOUS_ANALYZER_STATE['last_rejection_samples'] = rejection_samples
            CONTINUOUS_ANALYZER_STATE['last_error'] = str(e)

        sleep_seconds = int(CONTINUOUS_ANALYZER_STATE.get('interval_seconds', 300))
        for _ in range(max(1, sleep_seconds)):
            if not CONTINUOUS_ANALYZER_STATE.get('running'):
                break
            time.sleep(1)


def start_continuous_analyzer(interval_seconds=300):
    """تشغيل خدمة التحليل المستمر."""
    global CONTINUOUS_ANALYZER_THREAD
    with CONTINUOUS_ANALYZER_LOCK:
        if CONTINUOUS_ANALYZER_STATE.get('running') and CONTINUOUS_ANALYZER_THREAD and CONTINUOUS_ANALYZER_THREAD.is_alive():
            return False, 'الخدمة تعمل بالفعل'

        CONTINUOUS_ANALYZER_STATE['interval_seconds'] = int(interval_seconds or CONTINUOUS_ANALYZER_INTERVAL_DEFAULT)
        CONTINUOUS_ANALYZER_STATE['running'] = True
        CONTINUOUS_ANALYZER_STATE['started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        CONTINUOUS_ANALYZER_STATE['last_cycle_started_at'] = None
        CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'starting'
        CONTINUOUS_ANALYZER_STATE['current_symbol'] = None
        CONTINUOUS_ANALYZER_STATE['current_interval'] = None
        CONTINUOUS_ANALYZER_STATE['current_symbol_index'] = 0
        CONTINUOUS_ANALYZER_STATE['symbols_total'] = 0
        CONTINUOUS_ANALYZER_STATE['last_rejection_reasons'] = {}
        CONTINUOUS_ANALYZER_STATE['last_rejection_samples'] = []
        CONTINUOUS_ANALYZER_THREAD = threading.Thread(target=_continuous_analyzer_loop, daemon=True)
        CONTINUOUS_ANALYZER_THREAD.start()
        return True, 'تم تشغيل خدمة التحليل المستمر'


def stop_continuous_analyzer():
    """إيقاف خدمة التحليل المستمر."""
    with CONTINUOUS_ANALYZER_LOCK:
        CONTINUOUS_ANALYZER_STATE['running'] = False
        CONTINUOUS_ANALYZER_STATE['cycle_stage'] = 'stopped'
        CONTINUOUS_ANALYZER_STATE['current_symbol'] = None
        CONTINUOUS_ANALYZER_STATE['current_interval'] = None
        CONTINUOUS_ANALYZER_STATE['current_symbol_index'] = 0
    return True, 'تم إيقاف خدمة التحليل المستمر'


def _is_continuous_analyzer_alive():
    return bool(CONTINUOUS_ANALYZER_THREAD and CONTINUOUS_ANALYZER_THREAD.is_alive())


def _run_continuous_analyzer_once(interval='1h', max_symbols=None, force_live=False):
    """تشغيل دورة تحليل واحدة لجميع الأزواج (بدون حلقة لا نهائية)."""
    symbols = _resolve_symbols_for_continuous_analyzer(max_symbols=max_symbols)

    generated_count = 0
    broadcast_count = 0
    analyzed_count = 0
    failed_count = 0
    rejection_reasons = {}
    details = []

    try:
        from forex_analyzer import get_last_fetch_metadata  # type: ignore
    except Exception:
        get_last_fetch_metadata = None  # type: ignore

    for symbol in symbols:
        analyzed_count += 1
        item = {'symbol': symbol, 'generated': False, 'source': None, 'error': None}
        try:
            interval_candidates = _resolve_intervals_for_symbol(symbol) if interval == '1h' else [interval]
            interval_outcomes = []
            for candidate_interval in interval_candidates:
                candidate_outcome = _analyze_and_generate_signal(symbol, interval=candidate_interval, force_live=force_live, return_diagnostics=True)
                if isinstance(candidate_outcome, dict):
                    candidate_outcome['symbol'] = symbol
                    candidate_outcome['interval'] = candidate_interval
                interval_outcomes.append(candidate_outcome)

            analysis_outcome = _select_preferred_analysis_outcome(interval_outcomes)

            if callable(get_last_fetch_metadata):
                try:
                    meta = get_last_fetch_metadata() or {}
                    item['source'] = meta.get('source')
                    item['cache_used'] = meta.get('cache_used')
                    item['stale_cache_used'] = meta.get('stale_cache_used')
                except Exception:
                    pass

            if not analysis_outcome or not analysis_outcome.get('ok'):
                item['reason'] = str((analysis_outcome or {}).get('reason') or 'no_signal')
                item['interval'] = (analysis_outcome or {}).get('interval')
                item['tried_intervals'] = [entry.get('interval') for entry in interval_outcomes if isinstance(entry, dict) and entry.get('interval')]
                rejection_reasons[item['reason']] = int(rejection_reasons.get(item['reason'], 0) or 0) + 1
                item['quality_score'] = (analysis_outcome or {}).get('quality_score')
                item['effective_min_quality'] = (analysis_outcome or {}).get('effective_min_quality')
                item['rr_tp1'] = (analysis_outcome or {}).get('rr_tp1')
                item['effective_min_rr'] = (analysis_outcome or {}).get('effective_min_rr')
                item['volatility'] = (analysis_outcome or {}).get('volatility')
                item['effective_max_volatility'] = (analysis_outcome or {}).get('effective_max_volatility')
                item['adaptive_mode'] = (analysis_outcome or {}).get('adaptive_mode')
                details.append(item)
                continue
            signal_data = analysis_outcome.get('signal') or {}

            generated_count += 1
            item['generated'] = True
            item['reason'] = 'generated'
            item['interval'] = (analysis_outcome or {}).get('interval')

            send_result = telegram_sender.send_signal_to_subscribers(
                signal_data,
                quality_score=signal_data.get('quality_score', 80)
            )
            formatted_message = telegram_sender.format_signal_message(signal_data)
            targets_result = telegram_sender.send_broadcast_to_configured_targets(formatted_message)

            if isinstance(send_result, dict):
                broadcast_count += int(send_result.get('sent_count', 0) or 0)
            if isinstance(targets_result, dict):
                broadcast_count += int(targets_result.get('sent_count', 0) or 0)
        except Exception as e:
            failed_count += 1
            item['error'] = str(e)

        details.append(item)

    CONTINUOUS_ANALYZER_STATE['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    CONTINUOUS_ANALYZER_STATE['last_analyzed_count'] = analyzed_count
    CONTINUOUS_ANALYZER_STATE['last_failed_count'] = failed_count
    CONTINUOUS_ANALYZER_STATE['last_no_signal_count'] = max(0, analyzed_count - generated_count - failed_count)
    CONTINUOUS_ANALYZER_STATE['last_failed_symbols'] = [
        f"{item.get('symbol')}:{item.get('error')}"
        for item in details if item.get('error')
    ][:8]
    CONTINUOUS_ANALYZER_STATE['last_rejection_reasons'] = rejection_reasons
    CONTINUOUS_ANALYZER_STATE['last_rejection_samples'] = [
        {
            'symbol': item.get('symbol'),
            'interval': item.get('interval'),
            'tried_intervals': item.get('tried_intervals'),
            'reason': item.get('reason'),
            'quality_score': item.get('quality_score'),
            'effective_min_quality': item.get('effective_min_quality'),
            'rr_tp1': item.get('rr_tp1'),
            'effective_min_rr': item.get('effective_min_rr'),
            'volatility': item.get('volatility'),
            'effective_max_volatility': item.get('effective_max_volatility'),
            'adaptive_mode': item.get('adaptive_mode')
        }
        for item in details if not item.get('generated')
    ][:8]
    CONTINUOUS_ANALYZER_STATE['last_active_signals_count'] = _count_current_active_signals()
    CONTINUOUS_ANALYZER_STATE['last_new_signals'] = generated_count
    CONTINUOUS_ANALYZER_STATE['total_generated'] += generated_count
    CONTINUOUS_ANALYZER_STATE['total_broadcasted'] += broadcast_count
    CONTINUOUS_ANALYZER_STATE['last_error'] = None if failed_count == 0 else f'failed_symbols={failed_count}'

    return {
        'success': True,
        'analyzed_count': analyzed_count,
        'generated_count': generated_count,
        'broadcast_count': broadcast_count,
        'failed_count': failed_count,
        'details': details[:60],
        'timestamp': datetime.now().isoformat()
    }


def _probe_data_sources(interval='1h', outputsize=120, force_live=False):
    """فحص مصدر البيانات لكل الأزواج لمعرفة هل الجلب حي أم لا."""
    try:
        from forex_analyzer import fetch_data, get_last_fetch_metadata  # type: ignore
    except Exception as e:
        return {
            'success': False,
            'error': f'forex_analyzer import failed: {e}'
        }

    report = []
    ok = 0
    failed = 0

    for symbol in _resolve_symbols_for_continuous_analyzer():
        item = {'symbol': symbol, 'ok': False, 'rows': 0, 'source': None, 'error': None}
        try:
            df = fetch_data(symbol, interval, outputsize=outputsize, force_live=force_live)
            meta = get_last_fetch_metadata() or {}
            item['ok'] = True
            item['rows'] = int(len(df) if df is not None else 0)
            item['source'] = meta.get('source')
            item['cache_used'] = meta.get('cache_used')
            item['stale_cache_used'] = meta.get('stale_cache_used')
            ok += 1
        except Exception as e:
            item['error'] = str(e)
            failed += 1
        report.append(item)

    return {
        'success': True,
        'interval': interval,
        'symbols_total': len(CONTINUOUS_ANALYZER_SYMBOLS),
        'ok': ok,
        'failed': failed,
        'report': report,
        'timestamp': datetime.now().isoformat()
    }


def get_live_price_detailed(symbol):
    """
    الحصول على السعر الحالي للزوج مع بيانات التحديث
    Returns {price, updated_at, source, cache_used}
    """
    clean_symbol = (symbol or '').upper().replace('/', '').replace('-', '').replace('_', '').strip()
    now_ts = time.time()

    if not clean_symbol:
        return None

    with LIVE_PRICE_CACHE_LOCK:
        cached_item = LIVE_PRICE_CACHE.get(clean_symbol)
        if cached_item and cached_item.get('expires_at', 0) > now_ts:
            return {
                'price': cached_item.get('price'),
                'updated_at': cached_item.get('updated_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': cached_item.get('source') or 'CACHE',
                'cache_used': True
            }

    def _is_valid_price(value):
        try:
            price = float(value)
            return price if price > 0 else None
        except Exception:
            return None

    def _price_from_twelvedata():
        if not TWELVEDATA_API_KEY:
            return None
        try:
            import requests
            td_symbol = _normalize_symbol_for_engine(clean_symbol)
            resp = requests.get(
                TWELVEDATA_PRICE_URL,
                params={'symbol': td_symbol, 'apikey': TWELVEDATA_API_KEY},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json() or {}
            return _is_valid_price(data.get('price'))
        except Exception:
            return None

    def _price_from_binance():
        try:
            import requests
            binance_symbol = BINANCE_SYMBOLS.get(clean_symbol)
            if not binance_symbol:
                return None
            resp = requests.get(BINANCE_PRICE_URL, params={'symbol': binance_symbol}, timeout=10)
            resp.raise_for_status()
            data = resp.json() or {}
            return _is_valid_price(data.get('price'))
        except Exception:
            return None

    def _price_from_yfinance():
        yf_symbol = YF_SYMBOLS.get(clean_symbol)
        if not yf_symbol:
            return None

        now_local = time.time()
        with LIVE_PRICE_CACHE_LOCK:
            blocked_until = float(YF_FAILURE_UNTIL.get(clean_symbol, 0) or 0)
        if blocked_until > now_local:
            return None

        try:
            import yfinance as yf
        except Exception:
            return None

        for attempt in range(max(1, YF_MAX_RETRIES)):
            try:
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                price_fields = ['regularMarketPrice', 'currentPrice', 'bid', 'ask']
                for field in price_fields:
                    price = _is_valid_price(info.get(field)) if isinstance(info, dict) else None
                    if price:
                        with LIVE_PRICE_CACHE_LOCK:
                            YF_FAILURE_UNTIL.pop(clean_symbol, None)
                        return price
            except Exception:
                pass

            try:
                ticker = yf.Ticker(yf_symbol)
                periods_intervals = [('1d', '1m'), ('5d', '5m'), ('1mo', '1h')]
                for period, interval in periods_intervals:
                    try:
                        hist = ticker.history(period=period, interval=interval)
                        if not hist.empty:
                            price = _is_valid_price(hist['Close'].iloc[-1])
                            if price:
                                with LIVE_PRICE_CACHE_LOCK:
                                    YF_FAILURE_UNTIL.pop(clean_symbol, None)
                                return price
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                data = yf.download(yf_symbol, period='1d', interval='1m', progress=False)
                if not data.empty:
                    close_val = data['Close'].iloc[-1]
                    price = _is_valid_price(close_val.iloc[0] if hasattr(close_val, 'iloc') else close_val)
                    if price:
                        with LIVE_PRICE_CACHE_LOCK:
                            YF_FAILURE_UNTIL.pop(clean_symbol, None)
                        return price
            except Exception:
                pass

            if attempt < max(1, YF_MAX_RETRIES) - 1:
                time.sleep(YF_RETRY_BACKOFF_SECONDS * (attempt + 1))

        with LIVE_PRICE_CACHE_LOCK:
            YF_FAILURE_UNTIL[clean_symbol] = time.time() + max(1, YF_COOLDOWN_SECONDS)

        return None

    def _price_from_yahoo_chart():
        yf_symbol = YF_SYMBOLS.get(clean_symbol)
        if not yf_symbol:
            return None
        try:
            import requests
            response = requests.get(
                f'https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}',
                params={'interval': '1m', 'range': '1d'},
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response.raise_for_status()
            payload = response.json() or {}
            result = (((payload.get('chart') or {}).get('result') or [None])[0])
            if not isinstance(result, dict):
                return None

            meta = result.get('meta') or {}
            meta_price = _is_valid_price(meta.get('regularMarketPrice'))
            if meta_price:
                return meta_price

            closes = (((result.get('indicators') or {}).get('quote') or [{}])[0]).get('close') or []
            for value in reversed(closes):
                price = _is_valid_price(value)
                if price:
                    return price
        except Exception:
            return None
        return None

    price = _price_from_twelvedata()
    if price:
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with LIVE_PRICE_CACHE_LOCK:
            LIVE_PRICE_CACHE[clean_symbol] = {
                'price': price,
                'expires_at': time.time() + max(1, LIVE_PRICE_CACHE_TTL_SECONDS),
                'updated_at': updated_at,
                'source': 'TwelveData'
            }
        return {
            'price': price,
            'updated_at': updated_at,
            'source': 'TwelveData',
            'cache_used': False
        }

    price = _price_from_binance()
    if price:
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with LIVE_PRICE_CACHE_LOCK:
            LIVE_PRICE_CACHE[clean_symbol] = {
                'price': price,
                'expires_at': time.time() + max(1, LIVE_PRICE_CACHE_TTL_SECONDS),
                'updated_at': updated_at,
                'source': 'Binance'
            }
        return {
            'price': price,
            'updated_at': updated_at,
            'source': 'Binance',
            'cache_used': False
        }

    price = _price_from_yahoo_chart()
    if price:
        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with LIVE_PRICE_CACHE_LOCK:
            LIVE_PRICE_CACHE[clean_symbol] = {
                'price': price,
                'expires_at': time.time() + max(1, LIVE_PRICE_CACHE_TTL_SECONDS),
                'updated_at': updated_at,
                'source': 'YahooChart'
            }
        return {
            'price': price,
            'updated_at': updated_at,
            'source': 'YahooChart',
            'cache_used': False
        }

    price = _price_from_yfinance()
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with LIVE_PRICE_CACHE_LOCK:
        LIVE_PRICE_CACHE[clean_symbol] = {
            'price': price,
            'expires_at': time.time() + (max(1, LIVE_PRICE_CACHE_TTL_SECONDS) if price else max(1, LIVE_PRICE_FAIL_CACHE_TTL_SECONDS)),
            'updated_at': updated_at,
            'source': 'YahooFinance' if price else 'UNAVAILABLE'
        }
    return {
        'price': price,
        'updated_at': updated_at,
        'source': 'YahooFinance' if price else 'UNAVAILABLE',
        'cache_used': False
    }


def get_live_price(symbol):
    """توافق خلفي: إرجاع السعر فقط."""
    details = get_live_price_detailed(symbol)
    if isinstance(details, dict):
        return details.get('price')
    return None


def _touch_authenticated_session(session_token):
    """تحديث last_seen بشكل مركزي للمستخدمين الحقيقيين فقط."""
    if not session_token or _is_local_admin_session():
        return False
    try:
        return bool(user_manager.touch_session(session_token, LAST_SEEN_TOUCH_THROTTLE_SECONDS))
    except Exception:
        return False


def _enrich_subscriptions_with_activity(subscriptions):
    """إضافة آخر تسجيل دخول وآخر ظهور وحالة الاتصال لكل اشتراك."""
    if not isinstance(subscriptions, list) or not subscriptions:
        return subscriptions if isinstance(subscriptions, list) else []

    user_ids = []
    for sub in subscriptions:
        try:
            user_ids.append(int((sub or {}).get('user_id')))
        except Exception:
            continue

    presence_map = user_manager.get_users_presence(user_ids=user_ids, online_window_minutes=ONLINE_ACTIVITY_WINDOW_MINUTES)
    enriched = []
    for sub in subscriptions:
        row = dict(sub or {})
        try:
            presence = presence_map.get(int(row.get('user_id') or 0), {})
        except Exception:
            presence = {}
        row['last_login'] = presence.get('last_login')
        row['last_seen'] = presence.get('last_seen')
        row['is_online_now'] = bool(presence.get('is_online_now'))
        row['activity_status'] = presence.get('activity_status') or ('never_logged_in' if not presence.get('last_login') else 'offline')
        enriched.append(row)
    return enriched


def login_required(f):
    """Decorator للتحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if _is_local_admin_session():
            return f(*args, **kwargs)

        session_token = session.get('session_token')
        if not session_token:
            return redirect(url_for('login'))
        
        user_info = user_manager.verify_session(session_token)
        if not user_info['success']:
            session.clear()
            return redirect(url_for('login'))

        _touch_authenticated_session(session_token)
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """الحصول على بيانات المستخدم الحالي"""
    if _is_local_admin_session():
        return {
            'success': True,
            'user_id': 0,
            'username': ADMIN_USERNAME,
            'full_name': 'Administrator',
            'email': 'admin@local',
            'plan': 'enterprise',
            'is_admin': True,
        }

    session_token = session.get('session_token')
    if session_token:
        user_info = user_manager.verify_session(session_token)
        if user_info.get('success'):
            _touch_authenticated_session(session_token)
        return user_info
    return {'success': False}


LEGACY_SITE_SETTINGS_FILE = Path(__file__).parent / 'site_settings.json'
LEGACY_TUTORIAL_UPLOAD_DIR = Path(__file__).parent / 'static' / 'uploads' / 'tutorials'
LEGACY_TUTORIAL_VIDEOS_FILE = Path(__file__).parent / 'tutorial_videos.json'
SITE_SETTINGS_FILE = Path(os.environ.get('SITE_SETTINGS_FILE', str(DATA_DIR / 'site_settings.json')))
TUTORIAL_UPLOAD_DIR = Path(os.environ.get('TUTORIAL_UPLOAD_DIR', str(DATA_DIR / 'tutorial_uploads' / 'tutorials')))
TUTORIAL_VIDEOS_FILE = Path(os.environ.get('TUTORIAL_VIDEOS_FILE', str(DATA_DIR / 'tutorial_videos.json')))
ALLOWED_TUTORIAL_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'm4v'}

DEFAULT_SITE_SETTINGS = {
    'support_email': 'mahmoodalqaise750@gmail.com',
    'support_phone': '00962770078321',
    'support_whatsapp': '00962770078321',
    'support_help_url': '/plans',
    'support_bug_url': '/profile',
    'support_feature_url': '/profile',
    'payment_cliq_number': '00962770078321',
    'payment_cliq_alias': 'jakel2008',
    'payment_iban': 'JO94CBJO0010000000000131000302',
    'payment_account_name': 'mahmoud atef alqaisi',
    'payment_bank_name': 'بنك الاسكان للتجاره والتمويل',
    'crypto_btc_address': '',
    'crypto_eth_address': '',
    'crypto_usdt_address': '',
    'recommendation_footer_enabled': True,
    'recommendation_footer_message': '',
    'recommendation_footer_link': '',
    'news_ticker_mode': 'both'
}

SITE_CONTENT_STORAGE_READY = False
SITE_CONTENT_STORAGE_LOCK = threading.Lock()


def ensure_site_content_storage():
    """ضمان بقاء إعدادات الموقع وفيديوهات الشروحات داخل التخزين الدائم مع ترحيل القديم مرة واحدة."""
    global SITE_CONTENT_STORAGE_READY

    if SITE_CONTENT_STORAGE_READY:
        return

    with SITE_CONTENT_STORAGE_LOCK:
        if SITE_CONTENT_STORAGE_READY:
            return

        try:
            SITE_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        try:
            TUTORIAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        try:
            if (not SITE_SETTINGS_FILE.exists()) and LEGACY_SITE_SETTINGS_FILE.exists() and LEGACY_SITE_SETTINGS_FILE != SITE_SETTINGS_FILE:
                shutil.copy2(str(LEGACY_SITE_SETTINGS_FILE), str(SITE_SETTINGS_FILE))
        except Exception as e:
            print(f"[WARN] Could not migrate site settings: {e}")

        try:
            if (not TUTORIAL_VIDEOS_FILE.exists()) and LEGACY_TUTORIAL_VIDEOS_FILE.exists() and LEGACY_TUTORIAL_VIDEOS_FILE != TUTORIAL_VIDEOS_FILE:
                shutil.copy2(str(LEGACY_TUTORIAL_VIDEOS_FILE), str(TUTORIAL_VIDEOS_FILE))
        except Exception as e:
            print(f"[WARN] Could not migrate tutorial metadata: {e}")

        try:
            if LEGACY_TUTORIAL_UPLOAD_DIR.exists() and LEGACY_TUTORIAL_UPLOAD_DIR != TUTORIAL_UPLOAD_DIR:
                for legacy_file in LEGACY_TUTORIAL_UPLOAD_DIR.iterdir():
                    if not legacy_file.is_file():
                        continue
                    target_file = TUTORIAL_UPLOAD_DIR / legacy_file.name
                    if target_file.exists():
                        continue
                    shutil.copy2(str(legacy_file), str(target_file))
        except Exception as e:
            print(f"[WARN] Could not migrate tutorial videos: {e}")

        SITE_CONTENT_STORAGE_READY = True


def get_site_settings():
    """قراءة إعدادات الدفع والدعم مع قيم افتراضية آمنة."""
    ensure_site_content_storage()
    settings = DEFAULT_SITE_SETTINGS.copy()
    try:
        if SITE_SETTINGS_FILE.exists():
            with open(SITE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for key in DEFAULT_SITE_SETTINGS:
                    value = data.get(key)
                    default_value = DEFAULT_SITE_SETTINGS[key]
                    if isinstance(default_value, bool):
                        if isinstance(value, bool):
                            settings[key] = value
                        elif isinstance(value, str):
                            lowered = value.strip().lower()
                            if lowered in ('1', 'true', 'yes', 'on'):
                                settings[key] = True
                            elif lowered in ('0', 'false', 'no', 'off'):
                                settings[key] = False
                    elif isinstance(value, str):
                        settings[key] = value.strip()
    except Exception as e:
        print(f"[WARN] Could not load site settings: {e}")
    return settings


def save_site_settings(new_values):
    """حفظ إعدادات الدفع والدعم بعد التحقق من المفاتيح المسموح بها."""
    ensure_site_content_storage()
    settings = get_site_settings()
    for key in DEFAULT_SITE_SETTINGS:
        if key in new_values:
            value = new_values.get(key)
            default_value = DEFAULT_SITE_SETTINGS[key]
            if isinstance(default_value, bool):
                if isinstance(value, bool):
                    settings[key] = value
                elif isinstance(value, str):
                    settings[key] = value.strip().lower() in ('1', 'true', 'yes', 'on')
                elif isinstance(value, (int, float)):
                    settings[key] = bool(value)
            elif isinstance(value, str):
                settings[key] = value.strip()

    with open(SITE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

    return settings


def ensure_tutorial_storage():
    """التأكد من وجود مجلد حفظ فيديوهات الشروحات."""
    ensure_site_content_storage()
    TUTORIAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def is_allowed_tutorial_video(filename):
    """التحقق من امتداد ملف الفيديو."""
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_TUTORIAL_VIDEO_EXTENSIONS


def load_tutorial_videos():
    """تحميل قائمة الفيديوهات التعليمية مع تجاهل الملفات غير المتاحة."""
    ensure_tutorial_storage()
    videos = []
    try:
        if TUTORIAL_VIDEOS_FILE.exists():
            with open(TUTORIAL_VIDEOS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    filename = str(item.get('filename') or '').strip()
                    if not filename:
                        continue
                    if not (TUTORIAL_UPLOAD_DIR / filename).exists():
                        continue

                    videos.append({
                        'id': str(item.get('id') or ''),
                        'title': str(item.get('title') or 'فيديو تعليمي').strip() or 'فيديو تعليمي',
                        'description': str(item.get('description') or '').strip(),
                        'filename': filename,
                        'uploaded_at': str(item.get('uploaded_at') or '').strip(),
                        'uploaded_by': str(item.get('uploaded_by') or '').strip(),
                    })
    except Exception as e:
        print(f"[WARN] Could not load tutorial videos: {e}")

    videos.sort(key=lambda row: row.get('uploaded_at', ''), reverse=True)
    return videos


def save_tutorial_videos(videos):
    """حفظ قائمة الفيديوهات التعليمية."""
    ensure_site_content_storage()
    with open(TUTORIAL_VIDEOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


def validate_crypto_addresses(settings_payload):
    """التحقق من صيغ عناوين العملات المشفرة عند التحديث."""
    if not isinstance(settings_payload, dict):
        return False, 'تنسيق إعدادات العملات المشفرة غير صالح'

    btc_address = str(settings_payload.get('crypto_btc_address', '') or '').strip()
    eth_address = str(settings_payload.get('crypto_eth_address', '') or '').strip()
    usdt_address = str(settings_payload.get('crypto_usdt_address', '') or '').strip()

    if btc_address:
        btc_pattern = r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$'
        if not re.match(btc_pattern, btc_address):
            return False, 'عنوان BTC غير صالح. استخدم عنوان يبدأ بـ bc1 أو 1 أو 3'

    if eth_address:
        eth_pattern = r'^0x[a-fA-F0-9]{40}$'
        if not re.match(eth_pattern, eth_address):
            return False, 'عنوان ETH غير صالح. يجب أن يبدأ بـ 0x ويتكون من 40 خانة Hex'

    if usdt_address:
        usdt_trc20_pattern = r'^T[1-9A-HJ-NP-Za-km-z]{33}$'
        usdt_erc20_pattern = r'^0x[a-fA-F0-9]{40}$'
        if not re.match(usdt_trc20_pattern, usdt_address) and not re.match(usdt_erc20_pattern, usdt_address):
            return False, 'عنوان USDT غير صالح. استخدم TRC20 (يبدأ بـ T) أو ERC20 (يبدأ بـ 0x)'

    return True, ''



# Context processor لتوفير المعلومات للقوالب + الروابط المركزية
@app.context_processor
def inject_user_and_links():
    """إضافة معلومات المستخدم وجميع الروابط لجميع القوالب"""
    user_info = get_current_user()
    return {
        'is_logged_in': user_info['success'],
        'user': user_info if user_info['success'] else None,
        'site_links': site_links.links,
        'site_settings': get_site_settings()
    }


@app.after_request
def add_no_cache_headers(response):
    """منع كاش الصفحات لضمان عدم إظهار الصفحات المحمية بعد تسجيل الخروج."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.before_request
def ensure_background_services_running():
    """ضمان تشغيل خدمات الخلفية عند العمل عبر WSGI (مثل Render/Gunicorn)."""
    if request.path == '/healthz':
        return

    if not BACKGROUND_SERVICES_ENABLED or BACKGROUND_SERVICES_BOOTSTRAPPED:
        return

    _schedule_background_services_bootstrap()

# Decorator لصلاحيات الأدمن
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_api_request = request.path.startswith('/api/')

        if _is_local_admin_session():
            return f(*args, **kwargs)

        session_token = session.get('session_token')
        if not session_token:
            if is_api_request:
                return jsonify({'success': False, 'error': 'Unauthorized', 'code': 'AUTH_REQUIRED'}), 401
            return redirect(url_for('login'))
        user_info = user_manager.verify_session(session_token)
        if not user_info['success'] or not user_info.get('is_admin'):
            if is_api_request:
                return jsonify({'success': False, 'error': 'Forbidden', 'code': 'ADMIN_REQUIRED'}), 403
            return redirect(url_for('home'))
        _touch_authenticated_session(session_token)
        return f(*args, **kwargs)
    return decorated_function




@app.route('/api/admin/telegram-command-bot/status', methods=['GET'])
@admin_required
def api_telegram_command_bot_status():
    if TELEGRAM_COMMAND_BOT is None:
        return jsonify({'success': False, 'enabled': TELEGRAM_COMMAND_BOT_ENABLED, 'error': 'telegram command bot module unavailable'}), 500
    return jsonify({'success': True, 'enabled': TELEGRAM_COMMAND_BOT_ENABLED, 'status': TELEGRAM_COMMAND_BOT.get_status()})


@app.route('/api/admin/telegram-command-bot/start', methods=['POST'])
@admin_required
def api_telegram_command_bot_start():
    ok, msg = start_telegram_command_bot()
    return jsonify({'success': ok, 'message': msg, 'enabled': TELEGRAM_COMMAND_BOT_ENABLED, 'status': TELEGRAM_COMMAND_BOT.get_status() if TELEGRAM_COMMAND_BOT else None})


@app.route('/api/admin/telegram-command-bot/stop', methods=['POST'])
@admin_required
def api_telegram_command_bot_stop():
    if TELEGRAM_COMMAND_BOT is None:
        return jsonify({'success': False, 'error': 'telegram command bot module unavailable'}), 500
    ok, msg = TELEGRAM_COMMAND_BOT.stop()
    return jsonify({'success': ok, 'message': msg, 'enabled': TELEGRAM_COMMAND_BOT_ENABLED, 'status': TELEGRAM_COMMAND_BOT.get_status()})


def archive_and_cleanup_closed_signals():
    """أرشفة الصفقات المنتهية وحذفها من الجدول النشط أولاً بأول."""
    archived_count = 0
    try:
        _ensure_signals_archive_table()
        archived = []
        if CLOSED_TRADES_ARCHIVE_FILE.exists():
            try:
                with open(CLOSED_TRADES_ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                    archived = json.load(f) or []
            except Exception:
                archived = []

        archived_ids = {item.get('signal_id') for item in archived if isinstance(item, dict)}
        archived_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rows_to_append = []

        lock_acquired = VIP_SIGNALS_DB_LOCK.acquire(timeout=2)
        if not lock_acquired:
            return 0

        try:
            conn = sqlite3.connect('vip_signals.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute('''
                SELECT *
                FROM signals
                WHERE status = 'closed' OR result IN ('win', 'loss')
                ORDER BY created_at ASC
            ''')
            closed_rows = c.fetchall()

            if not closed_rows:
                conn.close()
                return 0

            for row in closed_rows:
                row_dict = dict(row)
                signal_id = row_dict.get('signal_id')
                if signal_id in archived_ids:
                    continue

                try:
                    c.execute('''
                        INSERT OR REPLACE INTO signals_archive (
                            signal_id, symbol, signal_type, entry_price, stop_loss,
                            take_profit_1, take_profit_2, take_profit_3,
                            quality_score, timeframe, status, result,
                            current_price, close_price,
                            tp1_locked, tp2_locked, tp3_locked, activated,
                            created_at, archived_at, archive_reason
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row_dict.get('signal_id'), row_dict.get('symbol'), row_dict.get('signal_type'),
                        row_dict.get('entry_price'), row_dict.get('stop_loss'), row_dict.get('take_profit_1'),
                        row_dict.get('take_profit_2'), row_dict.get('take_profit_3'), row_dict.get('quality_score'),
                        row_dict.get('timeframe'), row_dict.get('status'), row_dict.get('result'),
                        row_dict.get('current_price'), row_dict.get('close_price'), row_dict.get('tp1_locked', 0),
                        row_dict.get('tp2_locked', 0), row_dict.get('tp3_locked', 0), row_dict.get('activated', 1),
                        row_dict.get('created_at'), archived_at, 'auto_cleanup_protocol'
                    ))
                except Exception:
                    pass

                row_dict['archived_at'] = archived_at
                row_dict['archive_reason'] = 'auto_cleanup_protocol'
                rows_to_append.append(row_dict)
                archived_ids.add(signal_id)
                archived_count += 1

            c.execute("DELETE FROM signals WHERE status = 'closed' OR result IN ('win', 'loss')")
            conn.commit()
            conn.close()
        finally:
            VIP_SIGNALS_DB_LOCK.release()

        if archived_count > 0:
            archived.extend(rows_to_append)
            archived = _deduplicate_archived_trade_rows(archived)
            with open(CLOSED_TRADES_ARCHIVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(archived, f, ensure_ascii=False, indent=2)

        return archived_count
    except Exception as e:
        print(f"[WARN] Could not archive closed signals: {e}")
        return archived_count


def _deduplicate_archived_trade_rows(trade_rows):
    """إزالة التكرار المنطقي من الصفقات المغلقة قبل احتساب الإحصائيات أو عرضها."""
    if not isinstance(trade_rows, list) or not trade_rows:
        return []

    normalized_rows = [row for row in trade_rows if isinstance(row, dict)]
    if not normalized_rows:
        return []

    def _sort_key(row):
        return (
            _parse_datetime_flexible(row.get('archived_at') or row.get('closed_at') or row.get('created_at')) or datetime.min,
            str(row.get('signal_id') or ''),
        )

    def _numeric_value(row, *keys):
        for key in keys:
            value = row.get(key)
            if value in (None, ''):
                continue
            try:
                return float(value)
            except Exception:
                continue
        return 0.0

    def _price_tolerance(value):
        try:
            numeric = abs(float(value or 0))
        except Exception:
            numeric = 0.0
        return max(0.0005, numeric * 0.0015)

    def _close_enough(first, second):
        tolerance = max(_price_tolerance(first), _price_tolerance(second))
        return abs(float(first or 0) - float(second or 0)) <= tolerance

    normalized_rows.sort(key=_sort_key, reverse=True)

    seen_signal_ids = set()
    deduplicated = []

    for row in normalized_rows:
        signal_id = row.get('signal_id')
        signal_id_key = None
        if signal_id not in (None, ''):
            signal_id_key = str(signal_id).strip()
            if signal_id_key in seen_signal_ids:
                continue

        symbol = _normalize_symbol_key(row.get('symbol') or row.get('pair') or '')
        signal_type = _normalize_signal_type(row.get('signal_type') or row.get('signal') or '', default='unknown')
        timeframe = str(row.get('timeframe') or row.get('tf') or '1h').strip().lower()
        result = str(row.get('result') or '').strip().lower()
        entry_price = round(_numeric_value(row, 'entry_price', 'entry'), 5)
        close_price = round(_numeric_value(row, 'close_price', 'current_price'), 5)
        stop_loss = round(_numeric_value(row, 'stop_loss'), 5)
        take_profit_1 = round(_numeric_value(row, 'take_profit_1', 'take_profit1', 'tp1'), 5)
        closed_at_dt = _parse_datetime_flexible(row.get('archived_at') or row.get('closed_at') or row.get('created_at'))

        is_logical_duplicate = False
        for kept in deduplicated:
            kept_symbol = _normalize_symbol_key(kept.get('symbol') or kept.get('pair') or '')
            kept_signal_type = _normalize_signal_type(kept.get('signal_type') or kept.get('signal') or '', default='unknown')
            kept_timeframe = str(kept.get('timeframe') or kept.get('tf') or '1h').strip().lower()
            kept_result = str(kept.get('result') or '').strip().lower()

            if symbol != kept_symbol or signal_type != kept_signal_type or timeframe != kept_timeframe or result != kept_result:
                continue

            kept_closed_at_dt = _parse_datetime_flexible(kept.get('archived_at') or kept.get('closed_at') or kept.get('created_at'))
            if closed_at_dt and kept_closed_at_dt:
                if abs((kept_closed_at_dt - closed_at_dt).total_seconds()) > 21600:
                    continue

            kept_entry_price = round(_numeric_value(kept, 'entry_price', 'entry'), 5)
            kept_close_price = round(_numeric_value(kept, 'close_price', 'current_price'), 5)
            kept_stop_loss = round(_numeric_value(kept, 'stop_loss'), 5)
            kept_take_profit_1 = round(_numeric_value(kept, 'take_profit_1', 'take_profit1', 'tp1'), 5)

            close_match = _close_enough(close_price, kept_close_price)
            entry_match = _close_enough(entry_price, kept_entry_price)
            stop_match = _close_enough(stop_loss, kept_stop_loss)
            target_match = True
            if take_profit_1 and kept_take_profit_1:
                target_match = _close_enough(take_profit_1, kept_take_profit_1)

            recent_close_cluster = False
            if closed_at_dt and kept_closed_at_dt:
                recent_close_cluster = abs((kept_closed_at_dt - closed_at_dt).total_seconds()) <= 3600

            if not close_match:
                continue
            if (entry_match and stop_match and target_match) or (recent_close_cluster and (entry_match or stop_match or target_match)):
                is_logical_duplicate = True
                break

        if is_logical_duplicate:
            continue

        if signal_id_key is not None:
            seen_signal_ids.add(signal_id_key)
        deduplicated.append(row)

    return deduplicated


def _load_raw_archived_trade_rows(limit=100000):
    """تحميل صفوف الأرشيف الخام من قاعدة البيانات وملف JSON قبل إزالة التكرار."""
    _ensure_signals_archive_table()

    safe_limit = max(1, int(limit or 100000))
    database_rows = []
    json_rows = []

    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT *
            FROM signals_archive
            ORDER BY COALESCE(archived_at, created_at) DESC
            LIMIT ?
        ''', (safe_limit,))
        database_rows = [dict(item) for item in c.fetchall()]
        conn.close()
    except Exception:
        database_rows = []

    if CLOSED_TRADES_ARCHIVE_FILE.exists():
        try:
            with open(CLOSED_TRADES_ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f) or []
            if isinstance(data, list):
                json_rows = [row for row in reversed(data[-safe_limit:]) if isinstance(row, dict)]
        except Exception:
            json_rows = []

    return {
        'database_rows': database_rows,
        'json_rows': json_rows,
        'combined_rows': list(database_rows) + list(json_rows),
    }


def _archived_trade_storage_row(row):
    """تحويل صف أرشيف عام إلى الصفوف المدعومة في جدول signals_archive وملف JSON."""
    if not isinstance(row, dict):
        return None

    def _safe_int(value):
        try:
            if value in (None, ''):
                return None
            return int(value)
        except Exception:
            return None

    return {
        'signal_id': _safe_int(row.get('signal_id')),
        'symbol': row.get('symbol') or row.get('pair'),
        'signal_type': row.get('signal_type') or row.get('signal'),
        'entry_price': row.get('entry_price') if row.get('entry_price') is not None else row.get('entry'),
        'stop_loss': row.get('stop_loss'),
        'take_profit_1': row.get('take_profit_1') if row.get('take_profit_1') is not None else row.get('take_profit1'),
        'take_profit_2': row.get('take_profit_2'),
        'take_profit_3': row.get('take_profit_3'),
        'quality_score': row.get('quality_score'),
        'timeframe': row.get('timeframe') or row.get('tf') or '1h',
        'status': row.get('status') or 'closed',
        'result': row.get('result'),
        'current_price': row.get('current_price'),
        'close_price': row.get('close_price'),
        'tp1_locked': row.get('tp1_locked', 0),
        'tp2_locked': row.get('tp2_locked', 0),
        'tp3_locked': row.get('tp3_locked', 0),
        'activated': row.get('activated', 1),
        'created_at': row.get('created_at'),
        'archived_at': row.get('archived_at') or row.get('closed_at') or row.get('created_at'),
        'archive_reason': row.get('archive_reason') or 'normalized_archive',
    }


def _write_archived_trades_to_database(trade_rows, replace_all=True):
    """مزامنة الصفقات المؤرشفة المنزوعة التكرار إلى قاعدة البيانات."""
    _ensure_signals_archive_table()

    safe_rows = []
    for row in trade_rows or []:
        normalized = _archived_trade_storage_row(row)
        if normalized is not None:
            safe_rows.append(normalized)

    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    if replace_all:
        c.execute('DELETE FROM signals_archive')

    for row in safe_rows:
        c.execute('''
            INSERT INTO signals_archive (
                signal_id, symbol, signal_type, entry_price, stop_loss,
                take_profit_1, take_profit_2, take_profit_3,
                quality_score, timeframe, status, result,
                current_price, close_price,
                tp1_locked, tp2_locked, tp3_locked, activated,
                created_at, archived_at, archive_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row.get('signal_id'),
            row.get('symbol'),
            row.get('signal_type'),
            row.get('entry_price'),
            row.get('stop_loss'),
            row.get('take_profit_1'),
            row.get('take_profit_2'),
            row.get('take_profit_3'),
            row.get('quality_score'),
            row.get('timeframe'),
            row.get('status'),
            row.get('result'),
            row.get('current_price'),
            row.get('close_price'),
            row.get('tp1_locked'),
            row.get('tp2_locked'),
            row.get('tp3_locked'),
            row.get('activated'),
            row.get('created_at'),
            row.get('archived_at'),
            row.get('archive_reason'),
        ))

    conn.commit()
    conn.close()
    return len(safe_rows)


def _write_archived_trades_to_json(trade_rows, backup_existing=False):
    """حفظ نسخة JSON نظيفة من الأرشيف مع عمل backup اختياري."""
    backup_path = None
    if backup_existing and CLOSED_TRADES_ARCHIVE_FILE.exists():
        try:
            BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
            backup_path = BACKUPS_DIR / f"closed_trades_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(CLOSED_TRADES_ARCHIVE_FILE, backup_path)
        except Exception:
            backup_path = None

    safe_rows = []
    for row in trade_rows or []:
        normalized = _archived_trade_storage_row(row)
        if normalized is not None:
            safe_rows.append(normalized)

    with open(CLOSED_TRADES_ARCHIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(safe_rows, f, ensure_ascii=False, indent=2)

    return str(backup_path) if backup_path else None


def _build_archive_stats(raw_payload=None, deduplicated_rows=None):
    """إحصاءات الأرشيف الخام مقابل الفعلي بعد إزالة التكرار."""
    raw_payload = raw_payload or _load_raw_archived_trade_rows(limit=100000)
    combined_rows = list(raw_payload.get('combined_rows') or [])
    deduplicated_rows = deduplicated_rows if deduplicated_rows is not None else _deduplicate_archived_trade_rows(combined_rows)

    def _count_results(rows):
        wins = 0
        losses = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            result = str(row.get('result') or '').strip().lower()
            if result == 'win':
                wins += 1
            elif result == 'loss':
                losses += 1
        return wins, losses

    raw_wins, raw_losses = _count_results(combined_rows)
    actual_wins, actual_losses = _count_results(deduplicated_rows)
    raw_closed_total = raw_wins + raw_losses
    actual_closed_total = actual_wins + actual_losses

    return {
        'database_rows': len(raw_payload.get('database_rows') or []),
        'json_rows': len(raw_payload.get('json_rows') or []),
        'raw_combined_rows': len(combined_rows),
        'raw_closed_total': raw_closed_total,
        'raw_wins': raw_wins,
        'raw_losses': raw_losses,
        'actual_closed_total': actual_closed_total,
        'actual_wins': actual_wins,
        'actual_losses': actual_losses,
        'duplicates_removed': max(0, raw_closed_total - actual_closed_total),
        'storage_source': 'database' if len(raw_payload.get('database_rows') or []) > 0 else ('json' if len(raw_payload.get('json_rows') or []) > 0 else 'none'),
    }


def _normalize_archived_trades_storage(backup_json=True):
    """تنظيف الأرشيف وترحيله إلى قاعدة البيانات مع الحفاظ على نسخة JSON نظيفة."""
    raw_payload = _load_raw_archived_trade_rows(limit=100000)
    deduplicated_rows = _deduplicate_archived_trade_rows(raw_payload.get('combined_rows') or [])

    backup_path = _write_archived_trades_to_json(deduplicated_rows, backup_existing=backup_json)
    stored_count = _write_archived_trades_to_database(deduplicated_rows, replace_all=True)

    stats = _build_archive_stats(raw_payload=raw_payload, deduplicated_rows=deduplicated_rows)
    stats['backup_path'] = backup_path
    stats['stored_rows'] = stored_count
    return stats


def _load_archived_trades(limit=2000):
    """تحميل الصفقات المنتهية من أرشيف قاعدة البيانات مع رجوع احتياطي لملف JSON."""
    _ensure_signals_archive_table()

    rows = []
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT *
            FROM signals_archive
            ORDER BY COALESCE(archived_at, created_at) DESC
            LIMIT ?
        ''', (max(1, int(limit or 2000)),))
        rows = _deduplicate_archived_trade_rows([dict(item) for item in c.fetchall()])
        conn.close()
    except Exception:
        rows = []

    if rows:
        return rows[:max(1, int(limit or 2000))]

    if CLOSED_TRADES_ARCHIVE_FILE.exists():
        try:
            with open(CLOSED_TRADES_ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f) or []
            if isinstance(data, list):
                deduplicated_rows = _deduplicate_archived_trade_rows(list(reversed(data)))
                try:
                    _write_archived_trades_to_database(deduplicated_rows, replace_all=True)
                except Exception:
                    pass
                return deduplicated_rows[:max(1, int(limit or 2000))]
        except Exception:
            return []

    return []


def _calc_archived_profit_percent(row):
    """حساب نسبة الربح التقريبية للصفقة المؤرشفة."""
    try:
        entry = float(row.get('entry_price') or row.get('entry') or 0)
        close_price = float(row.get('close_price') or row.get('current_price') or 0)
        signal_type = str(row.get('signal_type') or row.get('signal') or '').lower()
        if entry <= 0 or close_price <= 0:
            return 0.0
        if signal_type == 'sell':
            profit = ((entry - close_price) / entry) * 100
        else:
            profit = ((close_price - entry) / entry) * 100

        # حماية التقارير من القيم الشاذة في السجلات القديمة
        if profit > 60:
            profit = 60
        elif profit < -60:
            profit = -60

        return round(profit, 2)
    except Exception:
        return 0.0

def _build_closed_trades_comparison_report(days=7):
    """تقرير مقارنة الأداء بين نافذتين زمنيتين من الصفقات المؤرشفة."""
    rows = _load_archived_trades(limit=4000)
    now = datetime.now()
    window_days = max(1, int(days or 7))
    current_start = now - timedelta(days=window_days)
    previous_start = now - timedelta(days=window_days * 2)

    current_period = []
    previous_period = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        ts_raw = row.get('archived_at') or row.get('created_at')
        if not ts_raw:
            continue

        ts = None
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
            if ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)
        except Exception:
            ts = None

        if ts is None:
            continue

        if ts >= current_start:
            current_period.append(row)
        elif previous_start <= ts < current_start:
            previous_period.append(row)

    def _summarize(data_rows):
        wins = 0
        losses = 0
        quality_sum = 0.0
        quality_count = 0
        profit_sum = 0.0

        for item in data_rows:
            result = str(item.get('result') or '').lower()
            if result == 'win':
                wins += 1
            elif result == 'loss':
                losses += 1

            try:
                quality_sum += float(item.get('quality_score') or 0)
                quality_count += 1
            except Exception:
                pass

            profit_sum += _calc_archived_profit_percent(item)

        total = wins + losses
        win_rate = round((wins / total) * 100, 2) if total > 0 else 0.0
        avg_quality = round((quality_sum / quality_count), 2) if quality_count > 0 else 0.0

        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_quality': avg_quality,
            'net_profit_percent': round(profit_sum, 2)
        }

    current_stats = _summarize(current_period)
    previous_stats = _summarize(previous_period)

    return {
        'window_days': window_days,
        'current_period': current_stats,
        'previous_period': previous_stats,
        'delta': {
            'win_rate': round(current_stats['win_rate'] - previous_stats['win_rate'], 2),
            'net_profit_percent': round(current_stats['net_profit_percent'] - previous_stats['net_profit_percent'], 2),
            'total_trades': current_stats['total'] - previous_stats['total']
        }
    }


def _parse_report_datetime(value):
    """تحويل طوابع الوقت المتعددة الصيغ إلى datetime موحد بدون منطقة زمنية."""
    if not value:
        return None

    raw_text = str(value).strip()
    if not raw_text:
        return None

    candidates = [raw_text]
    if 'Z' in raw_text:
        candidates.append(raw_text.replace('Z', '+00:00'))

    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)
            return parsed
        except Exception:
            continue

    sanitized = raw_text.split('.')[0].strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(sanitized, fmt)
        except Exception:
            continue

    return None


def _resolve_periodic_report_window(period, now=None):
    """تحديد نافذة التقرير الحالية والسابقة حسب الفترة المطلوبة."""
    now = now or datetime.now()
    normalized = str(period or 'daily').strip().lower()

    if normalized not in ('daily', 'weekly', 'monthly'):
        normalized = 'daily'

    if normalized == 'daily':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_start = start - timedelta(days=1)
        label = 'يومي'
        icon = '📊'
    elif normalized == 'weekly':
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        previous_start = start - timedelta(days=7)
        label = 'أسبوعي'
        icon = '📈'
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_end_anchor = start - timedelta(days=1)
        previous_start = previous_end_anchor.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = 'شهري'
        icon = '🗓️'

    return {
        'period': normalized,
        'label': label,
        'icon': icon,
        'start': start,
        'end': now,
        'previous_start': previous_start,
        'previous_end': start,
    }


def _summarize_periodic_archived_trades(rows, active_count=0):
    """تلخيص الصفقات المؤرشفة لإنتاج بطاقات ومقارنات وتقارير جاهزة للعرض."""
    normalized_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        closed_at = _parse_report_datetime(row.get('archived_at') or row.get('closed_at') or row.get('created_at'))
        if closed_at is None:
            continue

        result = str(row.get('result') or '').strip().lower()
        if result not in ('win', 'loss'):
            continue

        symbol = str(row.get('symbol') or row.get('pair') or 'N/A').strip().upper()
        timeframe = str(row.get('timeframe') or row.get('tf') or '1h').strip().lower() or '1h'
        signal_type = _normalize_signal_type(row.get('signal_type') or row.get('signal') or '', default='buy')
        profit_percent = _calc_archived_profit_percent(row)

        try:
            quality_score = float(row.get('quality_score') or 0)
        except Exception:
            quality_score = 0.0

        try:
            risk_reward = float(_compute_risk_reward(
                row.get('entry_price') or row.get('entry'),
                row.get('stop_loss'),
                row.get('take_profit_1') or row.get('take_profit1')
            ) or 0)
        except Exception:
            risk_reward = 0.0

        normalized_rows.append({
            'symbol': symbol,
            'timeframe': timeframe,
            'signal_type': signal_type,
            'result': result,
            'profit_percent': profit_percent,
            'quality_score': quality_score,
            'risk_reward': round(risk_reward, 2),
            'closed_at': closed_at,
            'closed_at_text': closed_at.strftime('%Y-%m-%d %H:%M'),
            'entry_price': row.get('entry_price') or row.get('entry') or 0,
            'close_price': row.get('close_price') or row.get('current_price') or 0,
            'signal_id': row.get('signal_id'),
        })

    normalized_rows.sort(key=lambda item: item.get('closed_at') or datetime.min, reverse=True)

    wins = sum(1 for item in normalized_rows if item['result'] == 'win')
    losses = sum(1 for item in normalized_rows if item['result'] == 'loss')
    total = wins + losses
    win_rate = round((wins / total) * 100, 2) if total > 0 else 0.0
    net_profit_percent = round(sum(float(item.get('profit_percent') or 0) for item in normalized_rows), 2)
    avg_quality = round(
        sum(float(item.get('quality_score') or 0) for item in normalized_rows) / total,
        2
    ) if total > 0 else 0.0
    avg_rr = round(
        sum(float(item.get('risk_reward') or 0) for item in normalized_rows) / total,
        2
    ) if total > 0 else 0.0

    symbol_map = {}
    timeframe_map = {}
    for item in normalized_rows:
        symbol_key = item['symbol']
        timeframe_key = item['timeframe']

        if symbol_key not in symbol_map:
            symbol_map[symbol_key] = {
                'symbol': symbol_key,
                'total': 0,
                'wins': 0,
                'losses': 0,
                'net_profit_percent': 0.0,
            }
        if timeframe_key not in timeframe_map:
            timeframe_map[timeframe_key] = {
                'timeframe': timeframe_key,
                'total': 0,
                'wins': 0,
                'losses': 0,
            }

        symbol_map[symbol_key]['total'] += 1
        symbol_map[symbol_key]['net_profit_percent'] += float(item.get('profit_percent') or 0)
        timeframe_map[timeframe_key]['total'] += 1

        if item['result'] == 'win':
            symbol_map[symbol_key]['wins'] += 1
            timeframe_map[timeframe_key]['wins'] += 1
        else:
            symbol_map[symbol_key]['losses'] += 1
            timeframe_map[timeframe_key]['losses'] += 1

    top_symbols = []
    for symbol_data in symbol_map.values():
        symbol_total = int(symbol_data['total'] or 0)
        symbol_data['win_rate'] = round((symbol_data['wins'] / symbol_total) * 100, 2) if symbol_total > 0 else 0.0
        symbol_data['net_profit_percent'] = round(float(symbol_data['net_profit_percent'] or 0), 2)
        top_symbols.append(symbol_data)

    top_symbols.sort(
        key=lambda item: (item.get('wins', 0), item.get('win_rate', 0), item.get('total', 0), item.get('net_profit_percent', 0)),
        reverse=True
    )

    timeframe_breakdown = []
    for timeframe_data in timeframe_map.values():
        timeframe_total = int(timeframe_data['total'] or 0)
        timeframe_data['win_rate'] = round((timeframe_data['wins'] / timeframe_total) * 100, 2) if timeframe_total > 0 else 0.0
        timeframe_breakdown.append(timeframe_data)

    timeframe_breakdown.sort(key=lambda item: (item.get('total', 0), item.get('win_rate', 0)), reverse=True)

    return {
        'total_closed_trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'net_profit_percent': net_profit_percent,
        'avg_quality': avg_quality,
        'avg_rr': avg_rr,
        'active_trades': int(active_count or 0),
        'top_symbols': top_symbols[:5],
        'timeframe_breakdown': timeframe_breakdown[:5],
        'recent_closed': normalized_rows[:10],
    }


def _build_periodic_report_message(report_payload):
    """صياغة نص احترافي جاهز للإرسال عبر تيليجرام أو المعاينة داخل الواجهة."""
    summary = report_payload.get('summary') or {}
    top_symbols = report_payload.get('top_symbols') or []
    timeframe_breakdown = report_payload.get('timeframes') or []
    comparison = report_payload.get('comparison') or {}

    delta_trades = comparison.get('trades_delta', 0)
    delta_win_rate = comparison.get('win_rate_delta', 0)
    delta_profit = comparison.get('profit_delta', 0)

    lines = [
        f"{report_payload.get('icon', '📋')} <b>التقرير {report_payload.get('period_label', '')} - GOLD PRO</b>",
        '',
        f"📅 <b>الفترة:</b> {report_payload.get('date_range_text', '-')}",
        f"🕒 <b>وقت الإنشاء:</b> {report_payload.get('generated_at', '-')}",
        '',
        '📌 <b>الملخص التنفيذي</b>',
        f"• الصفقات المغلقة: <b>{summary.get('total_closed_trades', 0)}</b>",
        f"• الرابحة / الخاسرة: <b>{summary.get('wins', 0)}</b> / <b>{summary.get('losses', 0)}</b>",
        f"• معدل النجاح: <b>{summary.get('win_rate', 0)}%</b>",
        f"• صافي الأداء: <b>{summary.get('net_profit_percent', 0)}%</b>",
        f"• متوسط الجودة: <b>{summary.get('avg_quality', 0)}</b>",
        f"• متوسط RR: <b>{summary.get('avg_rr', 0)}</b>",
        f"• الصفقات النشطة الآن: <b>{summary.get('active_trades', 0)}</b>",
        '',
        '📉 <b>مقارنة بالفترة السابقة</b>',
        f"• فرق عدد الصفقات: <b>{delta_trades:+}</b>",
        f"• فرق معدل النجاح: <b>{delta_win_rate:+.2f}%</b>",
        f"• فرق صافي الأداء: <b>{delta_profit:+.2f}%</b>",
    ]

    if top_symbols:
        lines.extend(['', '🏆 <b>أفضل الأزواج</b>'])
        for index, item in enumerate(top_symbols[:3], start=1):
            lines.append(
                f"{index}. <b>{item.get('symbol')}</b> | {item.get('wins', 0)}/{item.get('total', 0)} نجاح | {item.get('win_rate', 0)}% | {item.get('net_profit_percent', 0)}%"
            )

    if timeframe_breakdown:
        lines.extend(['', '⏱ <b>الأطر الزمنية الأفضل</b>'])
        for item in timeframe_breakdown[:3]:
            lines.append(
                f"• <b>{item.get('timeframe')}</b> | {item.get('total', 0)} صفقة | {item.get('win_rate', 0)}% نجاح"
            )

    recent_closed = summary.get('recent_closed') or []
    if recent_closed:
        lines.extend(['', '🧾 <b>آخر الإغلاقات</b>'])
        for item in recent_closed[:3]:
            result_label = 'رابحة' if item.get('result') == 'win' else 'خاسرة'
            lines.append(
                f"• {item.get('symbol')} | {result_label} | {item.get('profit_percent', 0)}% | {item.get('closed_at_text', '-') }"
            )

    lines.extend(['', 'GOLD PRO | Professional Trading Intelligence'])
    return '\n'.join(lines)


def _build_periodic_report(period='daily'):
    """إنشاء تقرير زمني موحد للعرض والإرسال اليومي أو الأسبوعي أو الشهري."""
    window = _resolve_periodic_report_window(period)
    active_rows = load_signals(include_closed=False)
    active_count = len([
        row for row in active_rows
        if isinstance(row, dict) and (row.get('status') or 'active').lower() == 'active'
    ]) if isinstance(active_rows, list) else 0

    archived_rows = _load_archived_trades(limit=6000)
    current_rows = []
    previous_rows = []

    for row in archived_rows:
        if not isinstance(row, dict):
            continue
        closed_at = _parse_report_datetime(row.get('archived_at') or row.get('closed_at') or row.get('created_at'))
        if closed_at is None:
            continue

        if window['start'] <= closed_at <= window['end']:
            current_rows.append(row)
        elif window['previous_start'] <= closed_at < window['previous_end']:
            previous_rows.append(row)

    current_summary = _summarize_periodic_archived_trades(current_rows, active_count=active_count)
    previous_summary = _summarize_periodic_archived_trades(previous_rows, active_count=active_count)

    report = {
        'period': window['period'],
        'period_label': window['label'],
        'icon': window['icon'],
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range_text': f"{window['start'].strftime('%Y-%m-%d %H:%M')} → {window['end'].strftime('%Y-%m-%d %H:%M')}",
        'summary': current_summary,
        'comparison': {
            'previous_total_closed_trades': previous_summary.get('total_closed_trades', 0),
            'previous_win_rate': previous_summary.get('win_rate', 0),
            'previous_net_profit_percent': previous_summary.get('net_profit_percent', 0),
            'trades_delta': int(current_summary.get('total_closed_trades', 0) - previous_summary.get('total_closed_trades', 0)),
            'win_rate_delta': round(float(current_summary.get('win_rate', 0) - previous_summary.get('win_rate', 0)), 2),
            'profit_delta': round(float(current_summary.get('net_profit_percent', 0) - previous_summary.get('net_profit_percent', 0)), 2),
        },
        'top_symbols': current_summary.get('top_symbols', []),
        'timeframes': current_summary.get('timeframe_breakdown', []),
    }
    report['message_html'] = _build_periodic_report_message(report)
    return report


def _deduplicate_signal_objects(signal_rows):
    """إزالة التكرار/التشابه من البيانات قبل العرض للمستخدم."""
    if not isinstance(signal_rows, list) or not signal_rows:
        return []

    normalized_rows = []
    for row in signal_rows:
        if isinstance(row, dict):
            normalized_rows.append(row)

    normalized_rows.sort(
        key=lambda item: (
            str(item.get('timestamp') or item.get('created_at') or ''),
            float(item.get('quality_score') or 0),
            str(item.get('signal_id') or '')
        ),
        reverse=True
    )

    deduplicated = []
    for row in normalized_rows:
        symbol = str(row.get('symbol') or row.get('pair') or '').upper().replace('/', '').strip()
        signal_type = str(row.get('signal') or row.get('signal_type') or '').lower().strip()
        timeframe = str(row.get('timeframe') or row.get('tf') or '1h').strip()
        try:
            entry = float(row.get('entry') or row.get('entry_price') or 0)
        except Exception:
            entry = 0.0

        tolerance = max(0.0005, abs(entry) * 0.0015)
        is_duplicate = False

        for kept in deduplicated:
            kept_symbol = str(kept.get('symbol') or kept.get('pair') or '').upper().replace('/', '').strip()
            kept_signal_type = str(kept.get('signal') or kept.get('signal_type') or '').lower().strip()
            kept_timeframe = str(kept.get('timeframe') or kept.get('tf') or '1h').strip()
            try:
                kept_entry = float(kept.get('entry') or kept.get('entry_price') or 0)
            except Exception:
                kept_entry = 0.0

            if symbol == kept_symbol and signal_type == kept_signal_type and timeframe == kept_timeframe:
                if abs(entry - kept_entry) <= tolerance:
                    is_duplicate = True
                    break

        if not is_duplicate:
            deduplicated.append(row)

    return deduplicated


def _append_cleanup_audit_log(log_row):
    """إضافة سجل تدقيق لعمليات التنظيف مع احتفاظ بآخر 2000 سجل."""
    try:
        records = []
        if CLEANUP_AUDIT_FILE.exists():
            try:
                with open(CLEANUP_AUDIT_FILE, 'r', encoding='utf-8') as f:
                    records = json.load(f) or []
            except Exception:
                records = []

        if not isinstance(records, list):
            records = []

        records.append(log_row)
        with open(CLEANUP_AUDIT_FILE, 'w', encoding='utf-8') as f:
            json.dump(records[-2000:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _get_cleanup_audit_logs(limit=20):
    """قراءة آخر سجلات تدقيق التنظيف بحد أقصى قابل للتحديد."""
    safe_limit = max(1, min(500, int(limit or 20)))
    if not CLEANUP_AUDIT_FILE.exists():
        return []

    try:
        with open(CLEANUP_AUDIT_FILE, 'r', encoding='utf-8') as f:
            records = json.load(f) or []
        if not isinstance(records, list):
            return []
        return list(reversed(records[-safe_limit:]))
    except Exception:
        return []


def _run_cleanup_protocol_once():
    """تشغيل دورة تنظيف واحدة: إزالة التكرار + أرشفة الصفقات المنتهية."""
    deduplicated_count = 0
    cleaned_closed_count = 0
    error_text = None
    started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        deduplicated_count = _deduplicate_signals_continuously()
        cleaned_closed_count = archive_and_cleanup_closed_signals()
    except Exception as e:
        error_text = str(e)

    finished_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _append_cleanup_audit_log({
        'started_at': started_at,
        'finished_at': finished_at,
        'deduplicated_count': int(deduplicated_count or 0),
        'cleaned_closed_count': int(cleaned_closed_count or 0),
        'success': error_text is None,
        'error': error_text
    })

    return int(deduplicated_count or 0), int(cleaned_closed_count or 0), error_text


def _load_auto_broadcast_registry():
    """تحميل سجل الإشارات التي تم بثها تلقائياً لتجنب الإرسال المكرر."""
    if not AUTO_BROADCAST_REGISTRY_FILE.exists():
        return {}
    try:
        with open(AUTO_BROADCAST_REGISTRY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _save_auto_broadcast_registry(registry):
    """حفظ سجل البث التلقائي مع الاحتفاظ بآخر 5000 إشارة."""
    try:
        if not isinstance(registry, dict):
            return
        items = list(registry.items())[-5000:]
        trimmed = {k: v for k, v in items}
        with open(AUTO_BROADCAST_REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(trimmed, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _signal_broadcast_key(row_dict):
    """مفتاح فريد للإشارة لأغراض منع إعادة البث."""
    signal_id = row_dict.get('signal_id')
    if signal_id not in (None, ''):
        return str(signal_id)
    return f"{row_dict.get('symbol','')}_{row_dict.get('signal_type','')}_{row_dict.get('timeframe','1h')}_{row_dict.get('created_at','')}"


def _parse_datetime_flexible(value):
    if value in (None, ''):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for candidate in (text, text.replace('T', ' ').replace('Z', '')):
        try:
            return datetime.fromisoformat(candidate)
        except Exception:
            pass
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            pass
    return None


def _should_resend_signal(registry_entry, now_dt):
    if not AUTO_BROADCAST_ALLOW_RESEND:
        return False
    if not isinstance(registry_entry, dict):
        return True
    synced_at = _parse_datetime_flexible(registry_entry.get('synced_at'))
    if not synced_at:
        return True
    return (now_dt - synced_at) >= timedelta(minutes=AUTO_BROADCAST_RESEND_INTERVAL_MINUTES)


def _build_signal_payload_from_row(row_dict):
    """تحويل سجل DB إلى حمولة إشارة موحدة للبث."""
    signal_type = str(row_dict.get('signal_type') or '').lower()
    normalized_symbol = _normalize_symbol_key(row_dict.get('symbol'))
    return {
        'signal_id': row_dict.get('signal_id'),
        'symbol': normalized_symbol,
        'signal': signal_type,
        'rec': signal_type.upper() if signal_type else 'N/A',
        'timeframe': row_dict.get('timeframe') or '1h',
        'entry': float(row_dict.get('entry_price') or 0),
        'sl': float(row_dict.get('stop_loss') or 0),
        'tp1': float(row_dict.get('take_profit_1') or 0),
        'tp2': float(row_dict.get('take_profit_2') or 0),
        'tp3': float(row_dict.get('take_profit_3') or 0),
        'quality_score': int(row_dict.get('quality_score') or 80),
        'timestamp': row_dict.get('created_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'risk_reward_tp1': _compute_risk_reward(
            row_dict.get('entry_price'),
            row_dict.get('stop_loss'),
            row_dict.get('take_profit_1')
        ),
        'follow_up_status': (
            'closed' if (row_dict.get('status') == 'closed') else
            'tp3_locked' if int(row_dict.get('tp3_locked') or 0) else
            'tp2_locked' if int(row_dict.get('tp2_locked') or 0) else
            'tp1_locked' if int(row_dict.get('tp1_locked') or 0) else
            'active'
        )
    }


def _sync_site_signals_to_active_bots(limit=30):
    """مزامنة الإشارات الحديثة إلى البوتات/الأهداف النشطة مع إعادة بث دورية."""
    synced_count = 0
    now_dt = datetime.now()
    registry = _load_auto_broadcast_registry()
    selected_symbols = set(_selected_pairs_union_supported())

    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM signals WHERE status = 'active' ORDER BY created_at DESC LIMIT ?", (max(1, int(limit or 30)),))
        rows = [dict(item) for item in c.fetchall()]
        conn.close()
    except Exception:
        rows = []

    recent_threshold = now_dt - timedelta(minutes=AUTO_BROADCAST_RECENT_WINDOW_MINUTES)

    for row_dict in rows:
        row_symbol = _normalize_symbol_key(row_dict.get('symbol'))
        if selected_symbols and row_symbol not in selected_symbols:
            continue

        created_at_dt = _parse_datetime_flexible(row_dict.get('created_at'))
        if created_at_dt and created_at_dt < recent_threshold:
            continue

        key = _signal_broadcast_key(row_dict)
        if not key:
            continue
        if key in registry and not _should_resend_signal(registry.get(key), now_dt):
            continue

        signal_data = _build_signal_payload_from_row(row_dict)
        quality_score = int(signal_data.get('quality_score') or 80)

        subscribers_result = telegram_sender.send_signal_to_subscribers(signal_data, quality_score)
        formatted_message = telegram_sender.format_signal_message(signal_data)
        targets_result = telegram_sender.send_broadcast_to_configured_targets(formatted_message)

        sent_total = int(subscribers_result.get('sent_count', 0) or 0) + int(targets_result.get('sent_count', 0) or 0)
        failed_total = int(subscribers_result.get('failed_count', 0) or 0) + int(targets_result.get('failed_count', 0) or 0)

        registry[key] = {
            'synced_at': now_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': signal_data.get('symbol'),
            'timeframe': signal_data.get('timeframe'),
            'quality_score': quality_score,
            'sent_count': sent_total,
            'failed_count': failed_total
        }
        synced_count += 1

    _save_auto_broadcast_registry(registry)
    return synced_count

def _cleanup_scheduler_loop():
    """جدولة بروتوكول التنظيف بشكل دوري."""
    while CLEANUP_SCHEDULER_STATE.get('running'):
        deduplicated_count = 0
        cleaned_closed_count = 0
        synced_site_count = 0
        error_text = None

        try:
            _refresh_active_signal_statuses()
            deduplicated_count, cleaned_closed_count, error_text = _run_cleanup_protocol_once()
            synced_site_count = _sync_site_signals_to_active_bots(limit=40)
        except Exception as e:
            error_text = str(e)

        CLEANUP_SCHEDULER_STATE['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        CLEANUP_SCHEDULER_STATE['last_error'] = error_text
        CLEANUP_SCHEDULER_STATE['last_deduplicated'] = int(deduplicated_count or 0)
        CLEANUP_SCHEDULER_STATE['last_cleaned_closed'] = int(cleaned_closed_count or 0)
        CLEANUP_SCHEDULER_STATE['last_site_synced'] = int(synced_site_count or 0)
        CLEANUP_SCHEDULER_STATE['total_deduplicated'] += int(deduplicated_count or 0)
        CLEANUP_SCHEDULER_STATE['total_cleaned_closed'] += int(cleaned_closed_count or 0)
        CLEANUP_SCHEDULER_STATE['total_site_synced'] += int(synced_site_count or 0)

        sleep_seconds = int(CLEANUP_SCHEDULER_STATE.get('interval_seconds', CLEANUP_INTERVAL_DEFAULT))
        for _ in range(max(1, sleep_seconds)):
            if not CLEANUP_SCHEDULER_STATE.get('running'):
                break
            time.sleep(1)


def start_cleanup_scheduler(interval_seconds=None):
    """تشغيل مجدول تنظيف الصفقات."""
    global CLEANUP_SCHEDULER_THREAD
    with CLEANUP_SCHEDULER_LOCK:
        if CLEANUP_SCHEDULER_STATE.get('running') and CLEANUP_SCHEDULER_THREAD and CLEANUP_SCHEDULER_THREAD.is_alive():
            return False, 'مجدول التنظيف يعمل بالفعل'

        if interval_seconds is None:
            interval_seconds = CLEANUP_INTERVAL_DEFAULT

        CLEANUP_SCHEDULER_STATE['interval_seconds'] = int(interval_seconds or CLEANUP_INTERVAL_DEFAULT)
        CLEANUP_SCHEDULER_STATE['running'] = True
        CLEANUP_SCHEDULER_THREAD = threading.Thread(target=_cleanup_scheduler_loop, daemon=True)
        CLEANUP_SCHEDULER_THREAD.start()
        return True, 'تم تشغيل مجدول التنظيف'


def stop_cleanup_scheduler():
    """إيقاف مجدول تنظيف الصفقات."""
    with CLEANUP_SCHEDULER_LOCK:
        CLEANUP_SCHEDULER_STATE['running'] = False
    return True, 'تم إيقاف مجدول التنظيف'


def _generate_delivery_csv_now():
    if fetch_delivery_rows is None or write_delivery_csv is None:
        raise RuntimeError('delivery csv generator unavailable')

    report_date = datetime.now().strftime('%Y-%m-%d')
    rows = fetch_delivery_rows(report_date)
    csv_path = write_delivery_csv(report_date, rows)

    DELIVERY_REPORT_SCHEDULER_STATE['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    DELIVERY_REPORT_SCHEDULER_STATE['last_generated_date'] = report_date
    DELIVERY_REPORT_SCHEDULER_STATE['last_csv_path'] = str(csv_path)
    DELIVERY_REPORT_SCHEDULER_STATE['last_rows'] = len(rows)
    DELIVERY_REPORT_SCHEDULER_STATE['last_error'] = None
    DELIVERY_REPORT_SCHEDULER_STATE['total_runs'] += 1


def _delivery_report_scheduler_loop():
    while DELIVERY_REPORT_SCHEDULER_STATE.get('running'):
        try:
            now = datetime.now()
            hhmm = now.strftime('%H:%M')
            target_hhmm = str(DELIVERY_REPORT_SCHEDULER_STATE.get('daily_time') or DELIVERY_REPORT_DAILY_TIME)
            if hhmm == target_hhmm and DELIVERY_REPORT_SCHEDULER_STATE.get('last_generated_date') != now.strftime('%Y-%m-%d'):
                _generate_delivery_csv_now()
        except Exception as e:
            DELIVERY_REPORT_SCHEDULER_STATE['last_error'] = str(e)

        sleep_seconds = int(DELIVERY_REPORT_SCHEDULER_STATE.get('check_interval_seconds', DELIVERY_REPORT_CHECK_INTERVAL_SECONDS))
        for _ in range(max(1, sleep_seconds)):
            if not DELIVERY_REPORT_SCHEDULER_STATE.get('running'):
                break
            time.sleep(1)


def start_delivery_report_scheduler(daily_time=None, check_interval_seconds=None):
    global DELIVERY_REPORT_SCHEDULER_THREAD
    with DELIVERY_REPORT_SCHEDULER_LOCK:
        if DELIVERY_REPORT_SCHEDULER_STATE.get('running') and DELIVERY_REPORT_SCHEDULER_THREAD and DELIVERY_REPORT_SCHEDULER_THREAD.is_alive():
            return False, 'مجدول تقرير التوزيع يعمل بالفعل'

        if daily_time:
            DELIVERY_REPORT_SCHEDULER_STATE['daily_time'] = str(daily_time)
        if check_interval_seconds is not None:
            DELIVERY_REPORT_SCHEDULER_STATE['check_interval_seconds'] = max(15, int(check_interval_seconds))

        DELIVERY_REPORT_SCHEDULER_STATE['running'] = True
        DELIVERY_REPORT_SCHEDULER_THREAD = threading.Thread(target=_delivery_report_scheduler_loop, daemon=True)
        DELIVERY_REPORT_SCHEDULER_THREAD.start()
        return True, 'تم تشغيل مجدول تقرير التوزيع اليومي'


def stop_delivery_report_scheduler():
    with DELIVERY_REPORT_SCHEDULER_LOCK:
        DELIVERY_REPORT_SCHEDULER_STATE['running'] = False
    return True, 'تم إيقاف مجدول تقرير التوزيع اليومي'


def _safe_execute_vip_signals_write(sql, params=()):
    """تنفيذ كتابة قصيرة وآمنة على vip_signals مع إغلاق الاتصال دائماً."""
    import sqlite3
    conn = None
    try:
        conn = sqlite3.connect('vip_signals.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _refresh_active_signal_statuses(lookback_days=None):
    """تحديث أسعار وحالات الإشارات النشطة ضمن نافذة أوسع لتفادي تراكم الصفقات القديمة."""
    import sqlite3

    stats = {
        'processed': 0,
        'changed': 0,
        'prices_updated': 0,
        'lookback_days': max(1, int(lookback_days or ACTIVE_SIGNAL_STATUS_LOOKBACK_DAYS)),
        'active_rows': 0,
        'lock_skipped': False
    }
    price_cache = {}
    rows = []

    try:
        start_date = (datetime.now() - timedelta(days=stats['lookback_days'])).strftime('%Y-%m-%d')
        lock_acquired = VIP_SIGNALS_DB_LOCK.acquire(timeout=2)
        if not lock_acquired:
            stats['lock_skipped'] = True
            return stats

        conn = None
        try:
            conn = sqlite3.connect('vip_signals.db', timeout=30)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('PRAGMA busy_timeout = 30000')
            c.execute('''
                SELECT signal_id, symbol, signal_type, entry_price, stop_loss,
                       take_profit_1, take_profit_2, take_profit_3,
                       tp1_locked, tp2_locked, tp3_locked
                FROM signals
                WHERE status = 'active'
                  AND DATE(created_at) >= ?
                ORDER BY created_at DESC
            ''', (start_date,))
            rows = c.fetchall()
            stats['active_rows'] = len(rows)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            VIP_SIGNALS_DB_LOCK.release()

        if not rows:
            return stats

        row_updates = []
        for row in rows:
            symbol = _normalize_symbol_key(row['symbol'])
            if symbol not in price_cache:
                price_cache[symbol] = get_live_price(symbol)
            current_price = price_cache.get(symbol)
            if not current_price:
                continue

            stats['processed'] += 1
            stats['prices_updated'] += 1

            update_item = {
                'signal_id': row['signal_id'],
                'current_price': current_price,
                'close_status': None,
                'close_result': None,
                'close_price': None,
                'set_tp1_locked': None,
                'set_tp2_locked': None,
                'set_tp3_locked': None,
                'set_stop_loss': None,
                'set_result': None
            }

            signal_type = _normalize_signal_type(row['signal_type'])
            entry = float(row['entry_price'] or 0)
            sl = float(row['stop_loss'] or 0)
            tp1 = float(row['take_profit_1'] or 0)
            tp2 = float(row['take_profit_2'] or 0)
            tp3 = float(row['take_profit_3'] or 0)
            tp1_locked = int(row['tp1_locked'] or 0)
            tp2_locked = int(row['tp2_locked'] or 0)
            tp3_locked = int(row['tp3_locked'] or 0)

            if signal_type == 'buy':
                if current_price <= sl:
                    update_item['close_status'] = 'closed'
                    update_item['close_result'] = 'win' if (tp1_locked or tp2_locked or tp3_locked) else 'loss'
                    update_item['close_price'] = current_price
                    stats['changed'] += 1
                elif current_price >= tp3 and not tp3_locked:
                    update_item['close_status'] = 'closed'
                    update_item['close_result'] = 'win'
                    update_item['close_price'] = current_price
                    update_item['set_tp1_locked'] = 1
                    update_item['set_tp2_locked'] = 1
                    update_item['set_tp3_locked'] = 1
                    stats['changed'] += 1
                elif current_price >= tp2 and not tp2_locked:
                    current_sl = sl if sl > 0 else entry
                    update_item['set_result'] = 'win'
                    update_item['set_tp1_locked'] = 1
                    update_item['set_tp2_locked'] = 1
                    update_item['set_stop_loss'] = max(current_sl, tp1 or entry)
                    stats['changed'] += 1
                elif current_price >= tp1 and not tp1_locked:
                    current_sl = sl if sl > 0 else entry
                    update_item['set_result'] = 'win'
                    update_item['set_tp1_locked'] = 1
                    update_item['set_stop_loss'] = max(current_sl, entry)
                    stats['changed'] += 1
            else:
                if current_price >= sl:
                    update_item['close_status'] = 'closed'
                    update_item['close_result'] = 'win' if (tp1_locked or tp2_locked or tp3_locked) else 'loss'
                    update_item['close_price'] = current_price
                    stats['changed'] += 1
                elif current_price <= tp3 and not tp3_locked:
                    update_item['close_status'] = 'closed'
                    update_item['close_result'] = 'win'
                    update_item['close_price'] = current_price
                    update_item['set_tp1_locked'] = 1
                    update_item['set_tp2_locked'] = 1
                    update_item['set_tp3_locked'] = 1
                    stats['changed'] += 1
                elif current_price <= tp2 and not tp2_locked:
                    current_sl = sl if sl > 0 else entry
                    update_item['set_result'] = 'win'
                    update_item['set_tp1_locked'] = 1
                    update_item['set_tp2_locked'] = 1
                    update_item['set_stop_loss'] = min(current_sl, tp1 or entry)
                    stats['changed'] += 1
                elif current_price <= tp1 and not tp1_locked:
                    current_sl = sl if sl > 0 else entry
                    update_item['set_result'] = 'win'
                    update_item['set_tp1_locked'] = 1
                    update_item['set_stop_loss'] = min(current_sl, entry)
                    stats['changed'] += 1

            row_updates.append(update_item)

        lock_acquired = VIP_SIGNALS_DB_LOCK.acquire(timeout=2)
        if not lock_acquired:
            stats['lock_skipped'] = True
            return stats

        conn = None
        try:
            conn = sqlite3.connect('vip_signals.db', timeout=30)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('PRAGMA busy_timeout = 30000')

            for item in row_updates:
                c.execute('UPDATE signals SET current_price=? WHERE signal_id=?', (item['current_price'], item['signal_id']))

                if item['close_status']:
                    c.execute('''
                        UPDATE signals
                        SET status=?, result=?, close_price=?,
                            tp1_locked=COALESCE(?, tp1_locked),
                            tp2_locked=COALESCE(?, tp2_locked),
                            tp3_locked=COALESCE(?, tp3_locked)
                        WHERE signal_id=?
                    ''', (
                        item['close_status'],
                        item['close_result'],
                        item['close_price'],
                        item['set_tp1_locked'],
                        item['set_tp2_locked'],
                        item['set_tp3_locked'],
                        item['signal_id']
                    ))
                    continue

                if any(value is not None for value in (item['set_result'], item['set_tp1_locked'], item['set_tp2_locked'], item['set_stop_loss'])):
                    c.execute('''
                        UPDATE signals
                        SET result=COALESCE(?, result),
                            tp1_locked=COALESCE(?, tp1_locked),
                            tp2_locked=COALESCE(?, tp2_locked),
                            stop_loss=COALESCE(?, stop_loss)
                        WHERE signal_id=?
                    ''', (
                        item['set_result'],
                        item['set_tp1_locked'],
                        item['set_tp2_locked'],
                        item['set_stop_loss'],
                        item['signal_id']
                    ))

            conn.commit()
            return stats
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            VIP_SIGNALS_DB_LOCK.release()
    except Exception:
        return stats


def _build_signal_object_from_row(row):
    symbol = _normalize_symbol_key(row['symbol'])
    signal_type = _normalize_signal_type(row['signal_type'])
    entry = float(row['entry_price'] or 0)
    sl = float(row['stop_loss'] or 0)
    tp1 = float(row['take_profit_1'] or 0)
    tp2 = float(row['take_profit_2'] or 0)
    tp3 = float(row['take_profit_3'] or 0)
    status = row['status'] or 'pending'
    result = row['result'] if 'result' in row.keys() else None
    close_price = row['close_price'] if 'close_price' in row.keys() else None
    current_price = row['current_price'] if 'current_price' in row.keys() else None
    activated = row['activated'] if 'activated' in row.keys() else 0
    tp1_locked = row['tp1_locked'] if 'tp1_locked' in row.keys() else 0
    tp2_locked = row['tp2_locked'] if 'tp2_locked' in row.keys() else 0
    tp3_locked = row['tp3_locked'] if 'tp3_locked' in row.keys() else 0

    pips = 0
    progress = 0
    tp_levels_hit = int(tp1_locked or 0) + int(tp2_locked or 0) + int(tp3_locked or 0)
    total_range = 0

    try:
        current_price_val = float(current_price) if current_price is not None else None
    except Exception:
        current_price_val = None

    if current_price_val is not None:
        if signal_type == 'buy':
            pips = current_price_val - entry
            total_range = tp1 - entry
        else:
            pips = entry - current_price_val
            total_range = entry - tp1
        if total_range != 0:
            progress = int((pips / total_range) * 100)

    return {
        'signal_id': row['signal_id'],
        'file': str(row['signal_id']),
        'pair': symbol,
        'symbol': symbol,
        'signal': signal_type,
        'signal_type': signal_type,
        'rec': signal_type.upper(),
        'entry': entry,
        'entry_price': entry,
        'sl': sl,
        'stop_loss': sl,
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3,
        'take_profit_1': tp1,
        'take_profit_2': tp2,
        'take_profit_3': tp3,
        'quality_score': row['quality_score'],
        'timeframe': row['timeframe'] or '5m',
        'timestamp': row['created_at'],
        'created_at': row['created_at'],
        'status': status,
        'result': result,
        'current_price': current_price,
        'current_price_updated_at': None,
        'close_price': close_price,
        'pips': pips,
        'progress': progress,
        'tp_levels_hit': tp_levels_hit,
        'tp1_locked': tp1_locked,
        'tp2_locked': tp2_locked,
        'tp3_locked': tp3_locked,
        'activated': activated,
        'follow_up_status': (
            'closed' if status == 'closed' else
            'tp3_locked' if tp3_locked else
            'tp2_locked' if tp2_locked else
            'tp1_locked' if tp1_locked else
            'active' if activated else
            'pending'
        )
    }


def load_signals_snapshot(include_closed=False, limit=50):
    """تحميل خفيف للإشارات من قاعدة البيانات بدون تحديث أسعار حي أو تنظيف ثقيل."""
    signals = []
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        start_date = (datetime.now() - timedelta(days=SIGNALS_LOOKBACK_DAYS)).strftime('%Y-%m-%d')
        if include_closed:
            c.execute('''
                SELECT * FROM signals
                WHERE DATE(created_at) >= ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (start_date, int(limit or 50)))
        else:
            c.execute('''
                SELECT * FROM signals
                WHERE DATE(created_at) >= ?
                  AND status = 'active'
                ORDER BY created_at DESC
                LIMIT ?
            ''', (start_date, int(limit or 50)))
        rows = c.fetchall()
        conn.close()

        for row in rows:
            signals.append(_build_signal_object_from_row(row))
    except Exception as e:
        print(f"❌ خطأ في تحميل snapshot الإشارات: {e}")

    return _deduplicate_signal_objects(signals)


def load_signals(include_closed=False):
    """تحميل الإشارات من قاعدة البيانات مع الأسعار الحالية والنتائج"""
    import sqlite3
    signals = []

    # بروتوكول التنظيف قبل فتح اتصال القراءة لتجنب تعارض قفل قاعدة البيانات
    _run_cleanup_protocol_once()
    _refresh_active_signal_statuses()

    conn = None
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # جلب الإشارات من نافذة زمنية حديثة بدلاً من يوم واحد فقط
        start_date = (datetime.now() - timedelta(days=SIGNALS_LOOKBACK_DAYS)).strftime('%Y-%m-%d')
        if include_closed:
            c.execute('''
                SELECT * FROM signals
                WHERE DATE(created_at) >= ?
                ORDER BY created_at DESC
                LIMIT 50
            ''', (start_date,))
        else:
            c.execute('''
                SELECT * FROM signals
                WHERE DATE(created_at) >= ?
                  AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 50
            ''', (start_date,))
        
        rows = c.fetchall()
        allow_recent_any = False
        if (not rows) and (not include_closed):
            c.execute('''
                SELECT * FROM signals
                WHERE DATE(created_at) >= ?
                ORDER BY created_at DESC
                LIMIT 20
            ''', (start_date,))
            rows = c.fetchall()
            allow_recent_any = bool(rows)

        conn.close()
        conn = None

        for row in rows:
            symbol = _normalize_symbol_key(row['symbol'])
            signal_type = _normalize_signal_type(row['signal_type'])
            entry = row['entry_price']
            sl = row['stop_loss']
            tp1 = row['take_profit_1']
            tp2 = row['take_profit_2']
            tp3 = row['take_profit_3']
            status = row['status'] or 'pending'
            result = row['result'] if 'result' in row.keys() else None
            close_price = row['close_price'] if 'close_price' in row.keys() else None
            
            # حقول جديدة للقفل والتفعيل
            activated = row['activated'] if 'activated' in row.keys() else 0
            tp1_locked = row['tp1_locked'] if 'tp1_locked' in row.keys() else 0
            tp2_locked = row['tp2_locked'] if 'tp2_locked' in row.keys() else 0
            tp3_locked = row['tp3_locked'] if 'tp3_locked' in row.keys() else 0
            
            # الحصول على السعر الحالي
            current_price = None
            pips = 0
            progress = 0
            tp_levels_hit = 0
            total_range = 0
            
            # استخدام الدالة المحسنة لجلب السعر
            price_details = get_live_price_detailed(symbol)
            current_price = price_details.get('price') if isinstance(price_details, dict) else None
            current_price_updated_at = price_details.get('updated_at') if isinstance(price_details, dict) else None
            
            if current_price:
                # معالجة الصفقات النشطة فقط (نوع الصفقة buy/sell يأتي من التحليل)
                if status == 'active':
                    if signal_type == 'buy':
                        pips = current_price - entry
                        total_range = tp1 - entry
                        
                        # فحص إيقاف الخسارة
                        if current_price <= sl:
                            sl_outcome = 'win' if (tp1_locked or tp2_locked or tp3_locked) else 'loss'
                            status = 'closed'
                            result = sl_outcome
                            close_price = current_price
                        # فحص الأهداف بنظام القفل
                        elif current_price >= tp3:
                            tp_levels_hit = 3
                            if not tp3_locked:
                                tp3_locked = 1
                                tp2_locked = 1
                                tp1_locked = 1
                                status = 'closed'
                                result = 'win'
                                close_price = current_price
                            else:
                                tp_levels_hit = 3
                        elif current_price >= tp2 and not tp2_locked:
                            tp_levels_hit = 2
                            tp2_locked = 1
                            tp1_locked = 1
                            result = 'win'
                            current_sl = float(sl or entry or 0)
                            if current_sl <= 0:
                                current_sl = float(entry or 0)
                            new_sl = max(current_sl, float(tp1 or entry or 0))
                            sl = new_sl
                        elif current_price >= tp1 and not tp1_locked:
                            tp_levels_hit = 1
                            tp1_locked = 1
                            result = 'win'
                            current_sl = float(sl or entry or 0)
                            if current_sl <= 0:
                                current_sl = float(entry or 0)
                            new_sl = max(current_sl, float(entry or 0))
                            sl = new_sl
                        else:
                            # عدد المقفلة من قبل
                            tp_levels_hit = tp1_locked + tp2_locked + tp3_locked
                            if tp1_locked:
                                result = 'win'
                    elif signal_type == 'sell':
                        pips = entry - current_price
                        total_range = entry - tp1

                        # فحص إيقاف الخسارة
                        if current_price >= sl:
                            sl_outcome = 'win' if (tp1_locked or tp2_locked or tp3_locked) else 'loss'
                            status = 'closed'
                            result = sl_outcome
                            close_price = current_price
                        # فحص الأهداف بنظام القفل
                        elif current_price <= tp3:
                            tp_levels_hit = 3
                            if not tp3_locked:
                                tp3_locked = 1
                                tp2_locked = 1
                                tp1_locked = 1
                                status = 'closed'
                                result = 'win'
                                close_price = current_price
                            else:
                                tp_levels_hit = 3
                        elif current_price <= tp2 and not tp2_locked:
                            tp_levels_hit = 2
                            tp2_locked = 1
                            tp1_locked = 1
                            result = 'win'
                            current_sl = float(sl or entry or 0)
                            if current_sl <= 0:
                                current_sl = float(entry or 0)
                            new_sl = min(current_sl, float(tp1 or entry or 0))
                            sl = new_sl
                        elif current_price <= tp1 and not tp1_locked:
                            tp_levels_hit = 1
                            tp1_locked = 1
                            result = 'win'
                            current_sl = float(sl or entry or 0)
                            if current_sl <= 0:
                                current_sl = float(entry or 0)
                            new_sl = min(current_sl, float(entry or 0))
                            sl = new_sl
                        else:
                            # عدد المقفلة من قبل
                            tp_levels_hit = tp1_locked + tp2_locked + tp3_locked
                            if tp1_locked:
                                result = 'win'
                
                # حساب التقدم
                if total_range != 0:
                    progress = int((pips / total_range) * 100)
            
            signal_obj = {
                'signal_id': row['signal_id'],
                'file': str(row['signal_id']),
                'pair': symbol,
                'symbol': symbol,
                'signal': signal_type,
                'signal_type': signal_type,
                'rec': signal_type.upper(),
                'entry': entry,
                'entry_price': entry,
                'sl': sl,
                'stop_loss': sl,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'take_profit_1': tp1,
                'take_profit_2': tp2,
                'take_profit_3': tp3,
                'quality_score': row['quality_score'],
                'timeframe': row['timeframe'] or '5m',
                'timestamp': row['created_at'],
                'created_at': row['created_at'],
                'status': status,
                'result': result,
                'current_price': current_price,
                'current_price_updated_at': current_price_updated_at,
                'close_price': close_price,
                'pips': pips,
                'progress': progress,
                'tp_levels_hit': tp_levels_hit,
                'tp1_locked': tp1_locked,
                'tp2_locked': tp2_locked,
                'tp3_locked': tp3_locked,
                'activated': activated,
                'follow_up_status': (
                    'closed' if status == 'closed' else
                    'tp3_locked' if tp3_locked else
                    'tp2_locked' if tp2_locked else
                    'tp1_locked' if tp1_locked else
                    'active' if activated else
                    'pending'
                )
            }

            if include_closed or signal_obj.get('status') == 'active' or allow_recent_any:
                signals.append(signal_obj)
        
    except Exception as e:
        print(f"❌ خطأ في تحميل الإشارات: {e}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    return _deduplicate_signal_objects(signals)


def load_admin_recent_signals(limit=5):
    """تحميل آخر الإشارات للأدمن بسرعة بدون جلب أسعار حية لتخفيف بطء لوحة التحكم."""
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT signal_id, symbol, signal_type, entry_price, stop_loss,
                   take_profit_1, quality_score, timeframe, created_at
            FROM signals
            WHERE DATE(created_at) >= ?
              AND status = 'active'
            ORDER BY created_at DESC
            LIMIT ?
        ''', (today, int(limit or 5)))
        rows = c.fetchall()
        conn.close()

        signals = []
        for row in rows:
            signal_type = str(row['signal_type'] or '').lower()
            signals.append({
                'signal_id': row['signal_id'],
                'file': str(row['signal_id']),
                'pair': row['symbol'],
                'symbol': row['symbol'],
                'signal': signal_type,
                'signal_type': signal_type,
                'rec': signal_type.upper() if signal_type else 'N/A',
                'entry': float(row['entry_price'] or 0),
                'entry_price': float(row['entry_price'] or 0),
                'sl': float(row['stop_loss'] or 0),
                'stop_loss': float(row['stop_loss'] or 0),
                'tp1': float(row['take_profit_1'] or 0),
                'take_profit_1': float(row['take_profit_1'] or 0),
                'quality_score': int(row['quality_score'] or 0),
                'timeframe': row['timeframe'] or '1h',
                'tf': row['timeframe'] or '1h',
                'timestamp': row['created_at'],
                'created_at': row['created_at']
            })

        return signals
    except Exception:
        return []


def _count_current_active_signals():
    """عدّ الأزواج التي لديها إشارة نشطة حالياً بغض النظر عن التاريخ."""
    try:
        conn = sqlite3.connect('vip_signals.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT symbol) FROM signals WHERE status = 'active'")
        count = int((c.fetchone() or [0])[0] or 0)
        conn.close()
        return count
    except Exception:
        return 0


def _count_recent_active_signals(days=None):
    """عدّ الأزواج ذات الإشارات النشطة ضمن نافذة العرض الحالية."""
    try:
        lookback_days = int(days if days is not None else SIGNALS_LOOKBACK_DAYS)
        lookback_days = max(1, lookback_days)
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        conn = sqlite3.connect('vip_signals.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT symbol) FROM signals WHERE DATE(created_at) >= ? AND status = 'active'", (start_date,))
        count = int((c.fetchone() or [0])[0] or 0)
        conn.close()
        return count
    except Exception:
        return 0


def count_active_signals_today():
    """عدّ الأزواج ذات الإشارات النشطة اليوم بسرعة من قاعدة البيانات بدون تتبع أسعار."""
    try:
        conn = sqlite3.connect('vip_signals.db')
        c = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT COUNT(DISTINCT symbol)
            FROM signals
            WHERE DATE(created_at) >= ?
              AND status = 'active'
        ''', (today,))
        count = int((c.fetchone() or [0])[0] or 0)
        conn.close()
        return count
    except Exception:
        return 0


def load_recommendations():
    """تحميل التوصيات المحفوظة"""
    recommendations = []
    if RECOMMENDATIONS_DIR.exists():
        for rec_file in sorted(RECOMMENDATIONS_DIR.glob("recommendations_*.json"), reverse=True)[:5]:
            try:
                with open(rec_file, 'r', encoding='utf-8') as f:
                    recs = json.load(f)
                    for rec in recs:
                        rec['file'] = rec_file.name
                        recommendations.append(rec)
            except:
                pass
    # ترتيب حسب الجودة والوقت
    recommendations.sort(key=lambda x: (x.get('quality_score', 0), x.get('timestamp', '')), reverse=True)
    return recommendations[:20]  # أفضل 20 توصية


def load_analysis():
    """تحميل التحليلات المحفوظة"""
    analyses = []
    if ANALYSIS_DIR.exists():
        for analysis_file in sorted(ANALYSIS_DIR.glob("analysis_*.json"), reverse=True)[:20]:
            try:
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    analysis = json.load(f)
                    analysis['file'] = analysis_file.name
                    analyses.append(analysis)
            except:
                pass
    return analyses


def get_statistics():
    """الحصول على الإحصائيات المحسّنة"""
    # عدد الإشارات
    signals_count = len(list(SIGNALS_DIR.glob("*.json"))) if SIGNALS_DIR.exists() else 0
    
    # تحليل الإشارات
    signals_data = load_signals()
    buy_signals = sum(1 for s in signals_data if s.get('rec', '').upper() == 'BUY')
    sell_signals = sum(1 for s in signals_data if s.get('rec', '').upper() == 'SELL')
    
    # عدد التوصيات
    recommendations_count = 0
    recommendations_data = load_recommendations()
    recommendations_count = len(recommendations_data)
    
    # تحليل جودة التوصيات
    high_quality_recs = sum(1 for r in recommendations_data if r.get('quality_score', 0) >= 75)
    medium_quality_recs = sum(1 for r in recommendations_data if 50 <= r.get('quality_score', 0) < 75)
    
    # عدد التحليلات
    analysis_count = len(list(ANALYSIS_DIR.glob("analysis_*.json"))) if ANALYSIS_DIR.exists() else 0
    
    # عدد المشتركين
    users = subscription_manager.get_all_active_users()
    subscribers_count = len(users)
    
    # إحصائيات حسب الخطة
    plans = {}
    for user_data in users:
        if isinstance(user_data, dict):
            plan = user_data.get('plan', 'free')
        else:
            plan = user_data[1] if len(user_data) > 1 else 'free'
        plans[plan] = plans.get(plan, 0) + 1
    
    # حساب معدلات النجاح (تقديري بناءً على الجودة)
    total_quality = sum(r.get('quality_score', 0) for r in recommendations_data)
    avg_quality = total_quality / len(recommendations_data) if recommendations_data else 0
    
    # توزيع الأزواج المختارة
    pairs_distribution = _load_selected_pairs_distribution()
    
    # الأكثر الأزواج طلباً
    top_pairs = sorted(pairs_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'signals_count': signals_count,
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'recommendations_count': recommendations_count,
        'high_quality_recommendations': high_quality_recs,
        'medium_quality_recommendations': medium_quality_recs,
        'analysis_count': analysis_count,
        'subscribers_count': subscribers_count,
        'plans': plans,
        'average_quality': round(avg_quality, 2),
        'top_pairs': dict(top_pairs),
        'pairs_selected_count': len(pairs_distribution)
    }


def get_detailed_report():
    """تقرير تفصيلي للأداء"""
    signals = load_signals()
    recommendations = load_recommendations()
    
    # تحليل الإشارات حسب الزوج
    signals_by_pair = {}
    for signal in signals:
        pair = signal.get('symbol', 'Unknown')
        if pair not in signals_by_pair:
            signals_by_pair[pair] = {'buy': 0, 'sell': 0, 'total': 0}
        
        signals_by_pair[pair]['total'] += 1
        if signal.get('rec', '').upper() == 'BUY':
            signals_by_pair[pair]['buy'] += 1
        elif signal.get('rec', '').upper() == 'SELL':
            signals_by_pair[pair]['sell'] += 1
    
    # تحليل التوصيات حسب الجودة والإطار الزمني
    recs_by_timeframe = {}
    quality_distribution = {'high': 0, 'medium': 0, 'low': 0}
    
    for rec in recommendations:
        tf = rec.get('timeframe', '1h')
        quality = rec.get('quality_score', 0)
        
        if tf not in recs_by_timeframe:
            recs_by_timeframe[tf] = 0
        recs_by_timeframe[tf] += 1
        
        if quality >= 75:
            quality_distribution['high'] += 1
        elif quality >= 50:
            quality_distribution['medium'] += 1
        else:
            quality_distribution['low'] += 1
    
    return {
        'signals_by_pair': signals_by_pair,
        'recommendations_by_timeframe': recs_by_timeframe,
        'quality_distribution': quality_distribution,
        'total_signals': len(signals),
        'total_recommendations': len(recommendations)
    }


# ============ مسارات المصادقة ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    try:
        force_first_login_page = request.args.get('first') == '1'

        if request.method == 'GET' and force_first_login_page:
            return render_template('login.html')

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            print(f"[LOGIN] Attempt for user: {username}")
            if not username or not password:
                print("[LOGIN] Missing username or password")
                return render_template('login.html', error='يرجى ملء جميع الحقول')

            if username.lower() == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session.clear()
                session['local_admin_username'] = ADMIN_USERNAME
                session['user_id'] = 0
                print('[LOGIN] Local admin login success')
                return redirect(url_for('home'))

            # محاولة تسجيل الدخول
            result = user_manager.login_user(
                username, 
                password,
                request.remote_addr
            )
            print(f"[LOGIN] Result: {result.get('success')}, Message: {result.get('message')}")
            if result['success']:
                try:
                    profile = user_manager.get_user_info(result['user_id']) or {}
                    _ensure_subscription_user_link(
                        result['user_id'],
                        profile.get('username') or username,
                        profile.get('full_name') or '',
                        profile.get('email') or '',
                        profile.get('phone') or '',
                        profile.get('country') or '',
                        profile.get('nickname') or '',
                        prefer_trial=False
                    )
                except Exception:
                    pass
                session['session_token'] = result['session_token']
                session['user_id'] = result['user_id']
                print(f"[LOGIN] Session set successfully for user_id: {result['user_id']}")
                print(f"[LOGIN] Redirecting to home...")
                return redirect(url_for('home'))
            else:
                print(f"[LOGIN] Login failed: {result['message']}")
                return render_template('login.html', error=result['message'])

        # التحقق من وجود جلسة نشطة
        if _is_local_admin_session():
            return redirect(url_for('home'))

        if session.get('session_token'):
            user_info = user_manager.verify_session(session.get('session_token'))
            if user_info['success']:
                return redirect(url_for('home'))
        return render_template('login.html')
    except Exception as e:
        import traceback
        print("[LOGIN] Exception:", e)
        traceback.print_exc()
        return render_template('login.html', error=f'حدث خطأ داخلي: {e}')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة التسجيل"""
    force_first_register_page = request.args.get('first') == '1'
    form_data = {
        'full_name': '',
        'username': '',
        'email': '',
        'phone': '',
        'marketing_email_opt_in': True,
        'whatsapp_opt_in': False,
    }

    if request.method == 'GET' and force_first_register_page:
        return render_template('register.html', form_data=form_data)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        terms = request.form.get('terms')
        marketing_email_opt_in = request.form.get('marketing_email_opt_in') == '1'
        whatsapp_opt_in = request.form.get('whatsapp_opt_in') == '1'
        form_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone': phone,
            'marketing_email_opt_in': marketing_email_opt_in,
            'whatsapp_opt_in': whatsapp_opt_in,
        }
        
        # التحقق من صحة البيانات
        if not all([full_name, username, email, password]):
            return render_template('register.html', error='يرجى ملء جميع الحقول', form_data=form_data)
        
        if len(username) < 3:
            return render_template('register.html', error='اسم المستخدم يجب أن يكون 3 أحرف على الأقل', form_data=form_data)
        
        if len(password) < 6:
            return render_template('register.html', error='كلمة المرور يجب أن تكون 6 أحرف على الأقل', form_data=form_data)
        
        if password != confirm_password:
            return render_template('register.html', error='كلمات المرور غير متطابقة', form_data=form_data)
        
        if not terms:
            return render_template('register.html', error='يجب قبول الشروط والأحكام', form_data=form_data)
        
        # تسجيل المستخدم الجديد
        result = user_manager.register_user(
            username,
            email,
            password,
            full_name,
            phone=phone,
            marketing_email_opt_in=marketing_email_opt_in,
            whatsapp_opt_in=whatsapp_opt_in
        )
        
        if result['success']:
            if EMAIL_ACTIVATION_REQUIRED and result.get('activation_token'):
                activation_link = _build_public_url(url_for('activate_account', token=result.get('activation_token')))
                email_sent, email_message = email_service.send_account_activation(email, full_name, activation_link)
                flash('تم إنشاء الحساب. افتح رابط التفعيل المرسل إلى بريدك الإلكتروني قبل تسجيل الدخول.', 'success')
                if email_sent:
                    flash('تم إرسال رابط التفعيل إلى بريدك الإلكتروني.', 'info')
                else:
                    flash(f'تم حفظ الحساب لكن تعذر إرسال البريد الآن: {email_message}', 'warning')
                return redirect(url_for('activation_pending', email=email))

            flash('تم إنشاء الحساب بنجاح. يمكنك تسجيل الدخول مباشرة.', 'success')
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=result['message'], form_data=form_data)
    
    # التحقق من وجود جلسة نشطة
    if session.get('session_token'):
        user_info = user_manager.verify_session(session.get('session_token'))
        if user_info['success']:
            return redirect(url_for('home'))
    
    return render_template('register.html', form_data=form_data)


@app.route('/activation-pending')
def activation_pending():
    """صفحة توضح أن الحساب ينتظر تفعيل البريد."""
    return render_template('activation_pending.html', email=request.args.get('email', '').strip())


@app.route('/activate-account/<token>')
def activate_account(token):
    """تفعيل حساب المستخدم من خلال الرابط المرسل إلى البريد."""
    result = user_manager.activate_user(token)
    if result.get('success'):
        profile = user_manager.get_user_info(result.get('user_id')) or {}
        try:
            _ensure_subscription_user_link(
                result.get('user_id'),
                profile.get('username') or '',
                profile.get('full_name') or '',
                profile.get('email') or '',
                profile.get('phone') or '',
                profile.get('country') or '',
                profile.get('nickname') or '',
                prefer_trial=not result.get('already_active', False)
            )
        except Exception:
            pass
        if not result.get('already_active') and str(profile.get('email') or '').strip():
            welcome_sent, welcome_message = email_service.send_welcome_email(
                profile.get('email') or '',
                profile.get('full_name') or profile.get('username') or ''
            )
            if not welcome_sent:
                print(f"[WELCOME-EMAIL] send failed for user_id={result.get('user_id')}: {welcome_message}")
        flash(result.get('message') or 'تم تفعيل الحساب.', 'success')
        return redirect(url_for('login', first=1))

    flash(result.get('message') or 'تعذر تفعيل الحساب.', 'danger')
    return redirect(url_for('resend_activation'))


@app.route('/resend-activation', methods=['GET', 'POST'])
def resend_activation():
    """إعادة إرسال رابط التفعيل للحساب غير المفعل."""
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        if not identifier:
            return render_template('resend_activation.html', error='أدخل البريد الإلكتروني أو اسم المستخدم.')

        result = user_manager.regenerate_activation_token(identifier)
        if not result.get('success'):
            return render_template('resend_activation.html', error=result.get('message'))

        activation_link = _build_public_url(url_for('activate_account', token=result.get('activation_token')))
        email_sent, email_message = email_service.send_account_activation(
            result.get('email') or '',
            result.get('full_name') or result.get('username') or '',
            activation_link
        )
        if email_sent:
            return render_template(
                'resend_activation.html',
                success='تم إرسال رابط تفعيل جديد إلى بريدك الإلكتروني.',
                email=result.get('email') or ''
            )
        return render_template(
            'resend_activation.html',
            error=f'تم إنشاء رابط جديد لكن الإرسال فشل: {email_message}',
            email=result.get('email') or ''
        )

    return render_template('resend_activation.html', email=request.args.get('email', '').strip())


@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session_token = session.get('session_token')
    if session_token:
        user_manager.logout_user(session_token)
    session.clear()
    return redirect(url_for('home'))


@app.route('/profile')
@login_required
def profile():
    """صفحة الملف الشخصي"""
    user_info = get_current_user()
    if user_info['success']:
        user_data = user_manager.get_user_info(user_info['user_id'])
        return render_template('profile.html', user=user_data)
    return redirect(url_for('login'))


@app.route('/tutorials')
@login_required
def tutorials():
    """صفحة الفيديوهات التعليمية للمستخدمين."""
    user_info = get_current_user()
    videos = load_tutorial_videos()
    return render_template(
        'tutorials.html',
        videos=videos,
        user=user_info,
        is_admin=user_info.get('is_admin', False)
    )


@app.route('/tutorials/video/<path:filename>')
@login_required
def tutorial_video_file(filename):
    """تقديم فيديوهات الشروحات من التخزين الدائم للمستخدمين المسجلين فقط."""
    safe_name = secure_filename(filename or '')
    if not safe_name or safe_name != (filename or ''):
        abort(404)
    ensure_tutorial_storage()
    file_path = TUTORIAL_UPLOAD_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    return send_from_directory(TUTORIAL_UPLOAD_DIR, safe_name, conditional=True)


@app.route('/admin/tutorials/upload', methods=['POST'])
@admin_required
def upload_tutorial_video():
    """رفع فيديو تعليمي جديد من الأدمن."""
    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    video_file = request.files.get('video')

    if not video_file or not video_file.filename:
        flash('يرجى اختيار ملف فيديو قبل الرفع', 'warning')
        return redirect(url_for('tutorials'))

    if not is_allowed_tutorial_video(video_file.filename):
        flash('صيغة الفيديو غير مدعومة. الصيغ المتاحة: MP4, WEBM, OGG, MOV, M4V', 'danger')
        return redirect(url_for('tutorials'))

    ensure_tutorial_storage()
    original_name = secure_filename(video_file.filename)
    extension = Path(original_name).suffix.lower()
    unique_name = f"tutorial_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}{extension}"
    save_path = TUTORIAL_UPLOAD_DIR / unique_name

    try:
        video_file.save(save_path)
        videos = load_tutorial_videos()
        uploader = get_current_user().get('username', 'admin')

        videos.insert(0, {
            'id': f"vid_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(3)}",
            'title': title or (Path(original_name).stem or 'فيديو تعليمي'),
            'description': description,
            'filename': unique_name,
            'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'uploaded_by': uploader,
        })
        save_tutorial_videos(videos)
        flash('تم رفع الفيديو التعليمي بنجاح', 'success')
    except Exception as e:
        try:
            if save_path.exists():
                save_path.unlink()
        except Exception:
            pass
        flash(f'تعذر رفع الفيديو: {e}', 'danger')

    return redirect(url_for('tutorials'))


@app.route('/admin/tutorials/delete/<video_id>', methods=['POST'])
@admin_required
def delete_tutorial_video(video_id):
    """حذف فيديو تعليمي من قبل الأدمن."""
    target_id = (video_id or '').strip()
    if not target_id:
        flash('معرّف الفيديو غير صالح', 'warning')
        return redirect(url_for('tutorials'))

    videos = load_tutorial_videos()
    remaining = []
    deleted_video = None

    for video in videos:
        if str(video.get('id', '')).strip() == target_id and deleted_video is None:
            deleted_video = video
            continue
        remaining.append(video)

    if not deleted_video:
        flash('لم يتم العثور على الفيديو المطلوب', 'warning')
        return redirect(url_for('tutorials'))

    try:
        filename = str(deleted_video.get('filename') or '').strip()
        if filename:
            file_path = TUTORIAL_UPLOAD_DIR / filename
            if file_path.exists():
                file_path.unlink()
        save_tutorial_videos(remaining)
        flash('تم حذف الفيديو التعليمي بنجاح', 'success')
    except Exception as e:
        flash(f'تعذر حذف الفيديو: {e}', 'danger')

    return redirect(url_for('tutorials'))


# ============ الصفحات الرئيسية ============

def get_public_ads():
    """إرجاع إعلانات الصفحة العامة قبل تسجيل الدخول"""
    default_ads = [dict(item) for item in DEFAULT_PUBLIC_ADS]

    def normalize_ads(ads_list):
        normalized = []
        for item in ads_list or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get('title') or '').strip()
            text = str(item.get('text') or '').strip()
            if not title or not text:
                continue
            normalized.append({
                'badge': str(item.get('badge') or 'إعلان').strip() or 'إعلان',
                'title': title,
                'text': text,
                'cta_text': str(item.get('cta_text') or 'عرض التفاصيل').strip() or 'عرض التفاصيل',
                'cta_url': str(item.get('cta_url') or '/plans').strip() or '/plans'
            })
        return normalized[:12]

    try:
        if PUBLIC_ADS_FILE.exists():
            with open(PUBLIC_ADS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            normalized_data = normalize_ads(data if isinstance(data, list) else [])
            if normalized_data:
                return normalized_data
    except Exception as e:
        print(f"[WARN] Could not load public_ads.json: {e}")

    return default_ads


def save_public_ads(new_ads):
    """حفظ إعلانات الصفحة الرئيسية بعد التحقق من الحقول."""
    if not isinstance(new_ads, list):
        raise ValueError('تنسيق الإعلانات غير صالح')

    normalized = []
    for item in new_ads:
        if not isinstance(item, dict):
            continue
        title = str(item.get('title') or '').strip()
        text = str(item.get('text') or '').strip()
        if not title or not text:
            continue
        normalized.append({
            'badge': str(item.get('badge') or 'إعلان').strip() or 'إعلان',
            'title': title,
            'text': text,
            'cta_text': str(item.get('cta_text') or 'عرض التفاصيل').strip() or 'عرض التفاصيل',
            'cta_url': str(item.get('cta_url') or '/plans').strip() or '/plans'
        })

    normalized = normalized[:12]
    if not normalized:
        raise ValueError('يجب إضافة إعلان واحد على الأقل مع عنوان ونص')

    with open(PUBLIC_ADS_FILE, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    return normalized


def get_latest_registered_users(limit=5):
    """جلب آخر المنضمين من users.db و vip_subscriptions.db بدون تكرار."""
    safe_limit = max(1, int(limit))
    merged = {}

    try:
        conn = sqlite3.connect(user_manager.db_file)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT id, username, full_name, email, created_at
            FROM users
            WHERE (deleted_at IS NULL OR deleted_at = '')
            ORDER BY created_at DESC
            LIMIT ?
        ''', (max(safe_limit * 5, 20),))
        for item in c.fetchall():
            row = dict(item)
            email_key = str(row.get('email') or '').strip().lower()
            username_key = str(row.get('username') or '').strip().lower()
            key = email_key or username_key or str(row.get('id') or '').strip()
            if not key:
                continue
            merged[key] = {
                'user_id': row.get('id'),
                'username': row.get('username'),
                'full_name': row.get('full_name'),
                'email': row.get('email'),
                'created_at': row.get('created_at'),
                'source': 'users.db'
            }
        conn.close()
    except Exception as e:
        print(f"[WARN] Could not load latest users from users.db: {e}")

    try:
        conn = sqlite3.connect(str(VIP_SUBSCRIPTIONS_DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('PRAGMA table_info(users)')
        cols = {row[1] for row in c.fetchall()}

        preferred_cols = ['user_id', 'username', 'first_name', 'email', 'created_at']
        if all(col in cols for col in preferred_cols):
            select_clause = ', '.join(preferred_cols)
        else:
            select_parts = [
                'user_id' if 'user_id' in cols else 'NULL AS user_id',
                'username' if 'username' in cols else 'NULL AS username',
                'first_name' if 'first_name' in cols else ('full_name AS first_name' if 'full_name' in cols else 'NULL AS first_name'),
                'email' if 'email' in cols else 'NULL AS email',
                'created_at' if 'created_at' in cols else ('subscription_start AS created_at' if 'subscription_start' in cols else 'CURRENT_TIMESTAMP AS created_at'),
            ]
            select_clause = ', '.join(select_parts)

        c.execute(f'''
            SELECT {select_clause}
            FROM users
            ORDER BY datetime(COALESCE(created_at, CURRENT_TIMESTAMP)) DESC
            LIMIT ?
        ''', (max(safe_limit * 5, 20),))

        for item in c.fetchall():
            row = dict(item)
            email_key = str(row.get('email') or '').strip().lower()
            username_key = str(row.get('username') or '').strip().lower()
            user_id_key = str(row.get('user_id') or '').strip()
            key = email_key or username_key or user_id_key
            if not key or key in merged:
                continue
            merged[key] = {
                'user_id': row.get('user_id'),
                'username': row.get('username'),
                'full_name': row.get('first_name') or row.get('username'),
                'email': row.get('email'),
                'created_at': row.get('created_at'),
                'source': 'vip_subscriptions.db'
            }
        conn.close()
    except Exception as e:
        print(f"[WARN] Could not load latest users from vip_subscriptions.db: {e}")

    users = list(merged.values())
    users.sort(
        key=lambda item: _parse_datetime_flexible(item.get('created_at')) or datetime.min,
        reverse=True
    )
    return users[:safe_limit]


def get_recent_closed_trade_news(limit=8):
    """جلب آخر أخبار إغلاقات الصفقات (رابحة/خاسرة)."""
    items = []
    seen_messages = set()
    try:
        archived_rows = _load_archived_trades(limit=max(50, int(limit or 8) * 15))
        for trade in archived_rows:
            if not isinstance(trade, dict):
                continue

            result = str(trade.get('result') or '').strip().lower()
            if result not in ('win', 'loss'):
                continue

            pair = str(trade.get('symbol') or trade.get('pair') or 'N/A').upper()
            pips_val = trade.get('pips')
            profit_percent = trade.get('profit_percent')
            if profit_percent is None:
                profit_percent = _calc_archived_profit_percent(trade)

            perf = ''
            if pips_val not in (None, ''):
                perf = f" ({pips_val} نقطة)"
            elif profit_percent is not None:
                perf = f" ({profit_percent}%)"

            label = 'رابحة' if result == 'win' else 'خاسرة'
            icon = '✅' if result == 'win' else '❌'
            message = f"{icon} إغلاق {pair} صفقة {label}{perf}"
            if message in seen_messages:
                continue

            seen_messages.add(message)
            items.append(message)
            if len(items) >= max(1, int(limit)):
                break
    except Exception as e:
        print(f"[WARN] Could not load recent closed trades for ticker: {e}")
    return items


def load_cached_economic_news(max_age_minutes=45):
    """قراءة كاش الأخبار الاقتصادية إذا كان لا يزال صالحًا."""
    try:
        if not ECONOMIC_NEWS_CACHE_FILE.exists():
            return []
        with open(ECONOMIC_NEWS_CACHE_FILE, 'r', encoding='utf-8') as f:
            payload = json.load(f) or {}

        updated_at = str(payload.get('updated_at') or '').strip()
        items = payload.get('items') if isinstance(payload, dict) else []
        if not isinstance(items, list) or not items:
            return []

        if updated_at:
            try:
                ts = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                age = (datetime.now() - ts).total_seconds() / 60.0
                if age <= max_age_minutes:
                    return [str(item).strip() for item in items if str(item).strip()]
            except Exception:
                pass
    except Exception as e:
        print(f"[WARN] Could not load economic news cache: {e}")
    return []


def save_economic_news_cache(items):
    """حفظ كاش الأخبار الاقتصادية."""
    try:
        payload = {
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': items[:30]
        }
        with open(ECONOMIC_NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Could not save economic news cache: {e}")


def get_economic_news_sources():
    """إرجاع مصادر الأخبار الاقتصادية (مع إمكانية التعديل من لوحة الأدمن)."""
    defaults = [dict(item) for item in ECONOMIC_NEWS_SOURCES]
    try:
        if not ECONOMIC_NEWS_SOURCES_FILE.exists():
            return defaults
        with open(ECONOMIC_NEWS_SOURCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f) or []

        if not isinstance(data, list):
            return defaults

        source_map = {str(item.get('name') or '').strip().lower(): item for item in data if isinstance(item, dict)}
        normalized = []
        for default_source in defaults:
            key = str(default_source.get('name') or '').strip().lower()
            override = source_map.get(key, {}) if key else {}
            normalized.append({
                'name': default_source.get('name'),
                'url': str(override.get('url') or default_source.get('url') or '').strip(),
                'enabled': bool(override.get('enabled', default_source.get('enabled', True))),
                'language': str(override.get('language') or default_source.get('language') or 'en').strip().lower()
            })
        return normalized
    except Exception as e:
        print(f"[WARN] Could not load economic news sources: {e}")
        return defaults


def save_economic_news_sources(sources_payload):
    """حفظ إعدادات مصادر الأخبار الاقتصادية."""
    if not isinstance(sources_payload, list):
        raise ValueError('تنسيق مصادر الأخبار غير صالح')

    defaults = [dict(item) for item in ECONOMIC_NEWS_SOURCES]
    source_map = {str(item.get('name') or '').strip().lower(): item for item in sources_payload if isinstance(item, dict)}

    normalized = []
    for default_source in defaults:
        name = str(default_source.get('name') or '').strip()
        key = name.lower()
        override = source_map.get(key, {}) if key else {}
        url = str(override.get('url') or default_source.get('url') or '').strip()
        enabled = bool(override.get('enabled', default_source.get('enabled', True)))
        language = str(override.get('language') or default_source.get('language') or 'en').strip().lower()
        if language not in ('ar', 'en'):
            language = str(default_source.get('language') or 'en').strip().lower()
        normalized.append({'name': name, 'url': url, 'enabled': enabled, 'language': language})

    with open(ECONOMIC_NEWS_SOURCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    return normalized


def _is_economic_title(title):
    lower_title = str(title or '').lower()
    return any(keyword in lower_title for keyword in ECONOMIC_KEYWORDS)


def _extract_feed_titles(root):
    """استخراج عناوين من RSS (item/title) أو Atom (entry/title)."""
    titles = []

    for item in root.findall('.//item'):
        title_node = item.find('title')
        if title_node is None:
            continue
        title = str(title_node.text or '').strip()
        if title:
            titles.append(title)

    if titles:
        return titles

    for entry in root.findall('.//{*}entry'):
        title_node = entry.find('{*}title')
        if title_node is None:
            continue
        title = str(title_node.text or '').strip()
        if title:
            titles.append(title)

    return titles


def _is_probably_arabic(text):
    """تحقق مبسط إن كان النص عربيًا (احتواء حروف عربية)."""
    text = str(text or '')
    return bool(re.search(r'[\u0600-\u06FF]', text))


def fetch_economic_news(limit=12, language_mode='all'):
    """جلب الأخبار الاقتصادية من مصادر متعددة مع fallback على الكاش."""
    items = []
    seen = set()

    configured_sources = get_economic_news_sources()
    for source in configured_sources:
        if not bool(source.get('enabled', True)):
            continue

        source_language = str(source.get('language') or 'en').strip().lower()
        if language_mode == 'ar' and source_language != 'ar':
            continue

        url = source.get('url')
        source_name = source.get('name', 'News')
        if not url:
            continue
        try:
            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 GOLD-PRO-NewsBot/1.0'},
                timeout=8
            )
            response.raise_for_status()
            root = ET.fromstring(response.content)

            titles = _extract_feed_titles(root)
            for title in titles:
                if not title:
                    continue
                if not _is_economic_title(title):
                    continue

                dedup_key = title.lower()
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                items.append(f"🌍 {source_name}: {title}")
                if len(items) >= max(1, int(limit)):
                    break

            if len(items) >= max(1, int(limit)):
                break
        except Exception as e:
            print(f"[WARN] Economic source failed ({source_name}): {e}")

    if items:
        save_economic_news_cache(items)
        return items[:max(1, int(limit))]

    cached = load_cached_economic_news(max_age_minutes=180)
    if language_mode == 'ar':
        cached = [item for item in cached if _is_probably_arabic(item)]
    if cached:
        return cached[:max(1, int(limit))]

    return [
        '🌍 تحديث اقتصادي: تابع بيانات الفائدة والتضخم والبطالة لحظة بلحظة',
        '📊 تنبيه: راقب مفكرة الأخبار الاقتصادية قبل فتح الصفقات'
    ]


def build_economic_news_items(language_mode='all'):
    """بناء عناصر الأخبار الاقتصادية للشريط المتحرك."""
    news_items = fetch_economic_news(limit=20, language_mode=language_mode)
    if not news_items:
        news_items = ['⚡ لا توجد أخبار اقتصادية عاجلة حالياً']
    return news_items[:30]


def build_site_news_items():
    """بناء عناصر أخبار المنصة (مستقلة عن الأخبار الاقتصادية)."""
    news_items = []
    news_items.extend(get_recent_closed_trade_news(limit=10))

    latest_users = get_latest_registered_users(limit=5)
    for user_row in latest_users:
        display_name = str(user_row.get('full_name') or user_row.get('username') or '').strip()
        if display_name:
            news_items.append(f"🎉 ترحيب: أهلاً بالمستخدم الجديد {display_name}")

    if not news_items:
        news_items = ['⚡ أخبار المنصة: تابع آخر الإشارات والتوصيات مباشرة من GOLD PRO']

    return news_items[:30]


def build_breaking_news_items():
    """للتوافق الخلفي: دمج الاقتصادي + أخبار الموقع إذا استُخدمت دالة قديمة."""
    merged = []
    merged.extend(build_economic_news_items())
    merged.extend(build_site_news_items())
    return merged[:30]


@app.route('/api/news-ticker')
def api_news_ticker():
    """API الأخبار الاقتصادية للشريط المتحرك."""
    lang_param = str(request.args.get('lang') or '').strip().lower()
    language_mode = 'ar' if lang_param in ('ar', 'arabic') else 'all'
    return jsonify({
        'success': True,
        'type': 'economic',
        'language_mode': language_mode,
        'items': build_economic_news_items(language_mode=language_mode),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/site-news-ticker')
def api_site_news_ticker():
    """API أخبار الموقع (منفصل عن الأخبار الاقتصادية)."""
    return jsonify({
        'success': True,
        'type': 'site',
        'items': build_site_news_items(),
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/news-stream-config')
def api_news_stream_config():
    """تهيئة عرض شريط الأخبار للواجهة العامة."""
    settings = get_site_settings()
    mode = str(settings.get('news_ticker_mode') or 'both').strip().lower()
    if mode not in ('both', 'economic', 'arabic'):
        mode = 'both'
    return jsonify({'success': True, 'mode': mode})

@app.route('/')
def home():
    """الصفحة الرئيسية الجديدة"""
    user_info = get_current_user()
    if not user_info['success']:
        return render_template(
            'public_landing.html',
            ads=get_public_ads(),
            is_logged_in=False,
            user=None
        )
    signals = load_signals()
    stats = get_statistics()
    return render_template('home.html', 
                         signals=signals,
                         stats=stats,
                         is_logged_in=True,
                         user=user_info)


def _filter_signals_for_user(signals, user_info):
    """فلترة الإشارات حسب الخطة مع fallback لتجنب الصفحة الفارغة."""
    if not isinstance(signals, list):
        return []

    if isinstance(user_info, dict) and user_info.get('success') and user_info.get('is_admin'):
        return signals

    quality_threshold = {
        'free': 90,
        'bronze': 80,
        'silver': 70,
        'gold': 60,
        'platinum': 50
    }

    username = (user_info or {}).get('username', '') if isinstance(user_info, dict) else ''
    if username == 'jakel2008':
        return signals

    if isinstance(user_info, dict) and user_info.get('success'):
        plan = user_info.get('plan', 'free')
        threshold = quality_threshold.get(plan, 90)
        filtered = [s for s in signals if (s.get('quality_score') or 0) >= threshold]
    else:
        filtered = [s for s in signals if (s.get('quality_score') or 0) >= 90]

    selected_pairs = set()
    if isinstance(user_info, dict) and user_info.get('success'):
        selected_pairs = set(_load_user_selected_pairs(user_info.get('user_id')))

    if selected_pairs:
        selected_filtered = [s for s in filtered if _normalize_symbol_key(s.get('symbol')) in selected_pairs]
        return selected_filtered

    if filtered:
        return filtered

    ranked = sorted(signals, key=lambda s: (s.get('quality_score') or 0), reverse=True)
    return ranked[:10]


@app.route('/signals')
def signals():
    """صفحة الإشارات - تتطلب تسجيل الدخول"""
    user_info = get_current_user()

    if not user_info['success']:
        return redirect(url_for('login'))

    try:
        signals_data = load_signals()
        filtered_signals = _filter_signals_for_user(signals_data, user_info)

        # القالب الأساسي
        return render_template(
            'signals_gold_card.html',
            signals=filtered_signals,
            all_signals_count=len(signals_data),
            visible_signals_count=len(filtered_signals),
            is_logged_in=True,
            is_admin=user_info.get('is_admin', False),
            user=user_info
        )
    except Exception as e:
        # fallback آمن لو القالب مفقود/به خطأ Jinja
        print(f"[ERROR] /signals failed: {e}")
        try:
            return render_template(
                'signals_old.html',
                signals=[],
                all_signals_count=0,
                visible_signals_count=0,
                is_logged_in=True,
                is_admin=user_info.get('is_admin', False),
                user=user_info
            )
        except Exception:
            return "Signals page temporarily unavailable", 500


@app.route('/trades')
def trades():
    """صفحة متابعة الصفقات"""
    user_info = get_current_user()

    if not user_info['success']:
        return redirect(url_for('login'))

    return render_template('trades.html',
                         is_logged_in=True,
                         is_admin=user_info.get('is_admin', False),
                         user=user_info)


@app.route('/api/trades_status')
@login_required
def api_trades_status():
    """API لمتابعة حالة الصفقات (نشطة/رابحة/خاسرة)"""
    try:
        user_info = get_current_user()
        all_signals = load_signals(include_closed=False)
        signals = _filter_signals_for_user(all_signals, user_info)

        def calc_profit_percent(trade):
            try:
                entry = float(trade.get('entry') or trade.get('entry_price') or 0)
                current = float(trade.get('current_price') or trade.get('close_price') or 0)
                signal_type = (trade.get('signal') or trade.get('signal_type') or '').lower()
                if entry <= 0 or current <= 0:
                    return 0.0
                if signal_type == 'sell':
                    return round(((entry - current) / entry) * 100, 2)
                return round(((current - entry) / entry) * 100, 2)
            except Exception:
                return 0.0

        normalized = []
        for trade in signals:
            signal_type = (trade.get('signal') or trade.get('signal_type') or '').lower() or 'buy'
            profit_percent = trade.get('profit_percent')
            if profit_percent is None:
                profit_percent = calc_profit_percent(trade)

            normalized.append({
                'signal_id': trade.get('signal_id'),
                'pair': trade.get('pair') or trade.get('symbol') or 'N/A',
                'signal': signal_type,
                'entry': trade.get('entry') or trade.get('entry_price') or 0,
                'current_price': trade.get('current_price') or trade.get('close_price') or 0,
                'profit_percent': round(float(profit_percent), 2) if isinstance(profit_percent, (int, float, str)) else 0.0,
                'status': (trade.get('status') or 'active').lower(),
                'result': (trade.get('result') or '').lower(),
                'timestamp': trade.get('timestamp') or trade.get('created_at') or ''
            })

        active_trades = [t for t in normalized if t.get('status') == 'active']

        archived_rows = _load_archived_trades(limit=2500)
        winners = []
        losers = []
        total_closed_profit = 0.0

        for row in archived_rows:
            if not isinstance(row, dict):
                continue

            result = str(row.get('result') or '').lower()
            if result not in ('win', 'loss'):
                continue

            profit_percent = _calc_archived_profit_percent(row)
            total_closed_profit += profit_percent

            item = {
                'pair': row.get('symbol') or row.get('pair') or 'N/A',
                'signal': str(row.get('signal_type') or row.get('signal') or '').lower() or 'buy',
                'entry': row.get('entry_price') or row.get('entry') or 0,
                'close_price': row.get('close_price') or row.get('current_price') or 0,
                'profit_percent': profit_percent,
                'result': result,
                'status': 'closed',
                'timestamp': row.get('archived_at') or row.get('created_at') or ''
            }

            if result == 'win':
                winners.append(item)
            else:
                losers.append(item)

        archived_count = len(archived_rows)
        winners.sort(key=lambda item: item.get('timestamp') or '', reverse=True)
        losers.sort(key=lambda item: item.get('timestamp') or '', reverse=True)

        return jsonify({
            'summary': {
                'total_trades': len(normalized),
                'active': len(active_trades),
                'winners': len(winners),
                'losers': len(losers),
                'net_profit_percent': round(total_closed_profit, 2),
                'archived_closed_trades': archived_count,
                'server_total_trades': len(all_signals),
                'visible_trades': len(normalized)
            },
            'active_trades': active_trades[:100],
            'closed_trades': {
                'winners': winners[:100],
                'losers': losers[:100]
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades-report')
@login_required
def api_trades_report():
    """API خفيف لتقرير الصفقات لصفحة التقارير."""
    try:
        active_count = 0
        recent_closed = []

        active_rows = load_signals(include_closed=False)
        if isinstance(active_rows, list):
            active_count = len([row for row in active_rows if (row.get('status') or 'active').lower() == 'active'])

        archived_rows = _load_archived_trades(limit=2500)

        now = datetime.now()
        recent_window = now - timedelta(hours=1)
        normalized_closed = []

        for row in archived_rows[:500]:
            if not isinstance(row, dict):
                continue

            close_time_raw = row.get('archived_at') or row.get('closed_at') or row.get('created_at')
            close_dt = None
            if close_time_raw:
                try:
                    close_dt = datetime.fromisoformat(str(close_time_raw).replace('Z', '+00:00'))
                except Exception:
                    close_dt = None

            normalized_closed.append({
                'symbol': row.get('symbol') or row.get('pair') or 'N/A',
                'result': (row.get('result') or '').lower(),
                'pips': row.get('pips') if row.get('pips') is not None else row.get('profit_percent'),
                'close_time': close_time_raw,
                '_close_dt': close_dt,
            })

        recent_closed = [
            item for item in normalized_closed
            if item['_close_dt'] is not None and item['_close_dt'] >= recent_window
        ]

        wins = len([item for item in normalized_closed if item.get('result') == 'win'])
        losses = len([item for item in normalized_closed if item.get('result') == 'loss'])

        recent_closed.sort(key=lambda item: item['_close_dt'] or datetime.min, reverse=True)

        for item in recent_closed:
            item.pop('_close_dt', None)

        return jsonify({
            'success': True,
            'active_count': active_count,
            'recent_closed_count': len(recent_closed),
            'wins': wins,
            'losses': losses,
            'recent_closed': recent_closed[:25]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'active_count': 0,
            'recent_closed_count': 0,
            'wins': 0,
            'losses': 0,
            'recent_closed': [],
            'message': str(e)
        }), 500


@app.route('/api/archive-stats')
@login_required
def api_archive_stats():
    """إرجاع إحصاءات الأرشيف الخام مقابل الفعلي بعد إزالة التكرار."""
    try:
        return jsonify({'success': True, 'stats': _build_archive_stats()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/archive-normalize', methods=['POST'])
@admin_required
def api_admin_archive_normalize():
    """تنظيف الأرشيف الحالي وإعادة ترحيله إلى قاعدة البيانات وJSON."""
    try:
        stats = _normalize_archived_trades_storage(backup_json=True)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/periodic-report')
@login_required
def api_periodic_report():
    """معاينة تقرير يومي/أسبوعي/شهري موحد لصفحة التقارير."""
    try:
        period = request.args.get('period', 'daily', type=str)
        report = _build_periodic_report(period=period)
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/continuous-analyzer/status')
@admin_required
def api_continuous_analyzer_status():
    """حالة خدمة التحليل المستمر."""
    auto_healed = False
    analyzer_running_flag = bool(CONTINUOUS_ANALYZER_STATE.get('running'))
    analyzer_alive = _is_continuous_analyzer_alive()

    if analyzer_running_flag and not analyzer_alive:
        try:
            start_continuous_analyzer(interval_seconds=CONTINUOUS_ANALYZER_STATE.get('interval_seconds', CONTINUOUS_ANALYZER_INTERVAL_DEFAULT))
            analyzer_alive = _is_continuous_analyzer_alive()
            auto_healed = analyzer_alive
        except Exception:
            analyzer_alive = False

    state = dict(CONTINUOUS_ANALYZER_STATE)
    state['thread_alive'] = analyzer_alive
    state['auto_healed'] = auto_healed
    if not analyzer_running_flag:
        state['runtime_status'] = 'stopped'
    elif analyzer_alive and not state.get('last_run'):
        state['runtime_status'] = 'starting'
    elif analyzer_alive:
        state['runtime_status'] = 'running'
    else:
        state['runtime_status'] = 'thread_not_alive'

    return jsonify({
        'success': True,
        'state': state
    })


@app.route('/api/admin/continuous-analyzer/start', methods=['POST'])
@admin_required
def api_continuous_analyzer_start():
    """تشغيل خدمة التحليل والبث المستمر."""
    data = request.get_json(silent=True) or {}
    interval_seconds = int(data.get('interval_seconds', CONTINUOUS_ANALYZER_INTERVAL_DEFAULT))
    success, message = start_continuous_analyzer(interval_seconds=interval_seconds)
    return jsonify({
        'success': success,
        'message': message,
        'state': CONTINUOUS_ANALYZER_STATE
    })

@app.route('/api/admin/closed-trades-comparison', methods=['GET'])
@admin_required
def api_admin_closed_trades_comparison():
    """تقرير مقارنة أداء الصفقات المنتهية من الأرشيف دون تغيير واجهة العرض."""
    try:
        days = request.args.get('days', 7, type=int)
        report = _build_closed_trades_comparison_report(days=days)
        return jsonify({'success': True, 'report': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/continuous-analyzer/stop', methods=['POST'])
@admin_required
def api_continuous_analyzer_stop():
    """إيقاف خدمة التحليل والبث المستمر."""
    success, message = stop_continuous_analyzer()
    return jsonify({
        'success': success,
        'message': message,
        'state': CONTINUOUS_ANALYZER_STATE
    })


@app.route('/api/admin/cleanup-scheduler/status')
@admin_required
def api_cleanup_scheduler_status():
    """حالة مجدول تنظيف الصفقات."""
    return jsonify({'success': True, 'state': CLEANUP_SCHEDULER_STATE})


@app.route('/api/admin/cleanup-scheduler/start', methods=['POST'])
@admin_required
def api_cleanup_scheduler_start():
    """تشغيل مجدول تنظيف الصفقات."""
    data = request.get_json(silent=True) or {}
    interval_seconds = int(data.get('interval_seconds', CLEANUP_INTERVAL_DEFAULT))
    success, message = start_cleanup_scheduler(interval_seconds=interval_seconds)
    return jsonify({'success': success, 'message': message, 'state': CLEANUP_SCHEDULER_STATE})


@app.route('/api/admin/cleanup-scheduler/stop', methods=['POST'])
@admin_required
def api_cleanup_scheduler_stop():
    """إيقاف مجدول تنظيف الصفقات."""
    success, message = stop_cleanup_scheduler()
    return jsonify({'success': success, 'message': message, 'state': CLEANUP_SCHEDULER_STATE})


@app.route('/api/admin/cleanup-audit', methods=['GET'])
@admin_required
def api_cleanup_audit():
    """إرجاع آخر سجلات بروتوكول تنظيف الصفقات للأدمن."""
    limit = request.args.get('limit', 20, type=int)
    logs = _get_cleanup_audit_logs(limit=limit)
    return jsonify({
        'success': True,
        'count': len(logs),
        'items': logs
    })


SUBSCRIPTION_DURATION_OPTIONS = {
    'monthly': {'label': 'شهر واحد', 'days': 30},
    'quarterly': {'label': '3 أشهر', 'days': 90},
    'semiannual': {'label': '6 أشهر', 'days': 180},
    'annual': {'label': '12 شهر (سنة)', 'days': 365},
}

SUBSCRIPTION_PLAN_CATALOG = {
    'bronze': {
        'name': 'Bronze',
        'signals': 3,
        'prices': {'monthly': 25, 'quarterly': 68, 'semiannual': 128, 'annual': 240},
    },
    'silver': {
        'name': 'Silver',
        'signals': 5,
        'prices': {'monthly': 50, 'quarterly': 135, 'semiannual': 255, 'annual': 480},
    },
    'gold': {
        'name': 'Gold',
        'signals': 7,
        'prices': {'monthly': 100, 'quarterly': 270, 'semiannual': 510, 'annual': 960},
    },
    'platinum': {
        'name': 'Platinum',
        'signals': 10,
        'prices': {'monthly': 250, 'quarterly': 675, 'semiannual': 1275, 'annual': 2400},
    },
}


def _normalize_duration_key(duration_key):
    key = str(duration_key or '').strip().lower()
    if key not in SUBSCRIPTION_DURATION_OPTIONS:
        return 'monthly'
    return key


def _build_plan_data(plan, duration_key='monthly'):
    duration_key = _normalize_duration_key(duration_key)
    plan_info = SUBSCRIPTION_PLAN_CATALOG.get(plan)
    if not plan_info:
        return None

    duration_info = SUBSCRIPTION_DURATION_OPTIONS[duration_key]
    return {
        'name': plan_info['name'],
        'plan': plan,
        'price': plan_info['prices'][duration_key],
        'duration_days': duration_info['days'],
        'duration_key': duration_key,
        'duration_label': duration_info['label'],
        'signals': plan_info['signals'],
        'signals_per_day': plan_info['signals'],
    }


def _build_duration_options(plan):
    plan_info = SUBSCRIPTION_PLAN_CATALOG.get(plan)
    if not plan_info:
        return []

    options = []
    for key in ('monthly', 'quarterly', 'semiannual', 'annual'):
        duration_info = SUBSCRIPTION_DURATION_OPTIONS[key]
        options.append({
            'key': key,
            'label': duration_info['label'],
            'duration_days': duration_info['days'],
            'price': plan_info['prices'][key],
        })
    return options


@app.route('/select_location/<plan>')
@login_required
def select_location(plan):
    """صفحة اختيار الموقع الجغرافي للدفع"""
    user_info = get_current_user()

    duration_key = _normalize_duration_key(request.args.get('duration', 'monthly'))
    plan_data = _build_plan_data(plan, duration_key)
    if not plan_data:
        return redirect(url_for('home'))

    return render_template('select_location.html',
                         plan=plan,
                         plan_data=plan_data,
                         duration_key=duration_key,
                         duration_options=_build_duration_options(plan),
                         user=user_info)


@app.route('/payment/<location>/<plan>')
@login_required
def payment_page(location, plan):
    """صفحة الدفع حسب الموقع"""
    user_info = get_current_user()

    duration_key = _normalize_duration_key(request.args.get('duration', 'monthly'))
    plan_data = _build_plan_data(plan, duration_key)

    if not plan_data or location not in ['jordan', 'international']:
        return redirect(url_for('home'))

    # تحويل السعر حسب الموقع
    if location == 'jordan':
        # تحويل الدولار للدينار الأردني (1 دولار = 0.71 دينار تقريباً)
        plan_data['price_jod'] = round(plan_data['price'] * 0.71, 2)
        template = 'payment_jordan.html'
    else:
        template = 'payment_international.html'
    
    return render_template(template,
                         location=location,
                         plan=plan,
                         duration_key=duration_key,
                         plan_data=plan_data,
                         user=user_info)


@app.route('/payment_jordan')
def payment_jordan_legacy():
    """رابط قديم: تحويله إلى صفحة الخطط"""
    return redirect(url_for('plans'))


@app.route('/payment_international')
def payment_international_legacy():
    """رابط قديم: تحويله إلى صفحة الخطط"""
    return redirect(url_for('plans'))


@app.route('/payment_jordan/<plan>')
@login_required
def payment_jordan_plan(plan):
    """توافق مع الروابط القديمة للدفع داخل الأردن"""
    duration_key = _normalize_duration_key(request.args.get('duration', 'monthly'))
    return redirect(url_for('payment_page', location='jordan', plan=plan, duration=duration_key))


@app.route('/payment_international/<plan>')
@login_required
def payment_international_plan(plan):
    """توافق مع الروابط القديمة للدفع الدولي"""
    duration_key = _normalize_duration_key(request.args.get('duration', 'monthly'))
    return redirect(url_for('payment_page', location='international', plan=plan, duration=duration_key))


@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة التحكم"""
    user_info = get_current_user()
    
    # تحميل تفضيلات الأزواج من قاعدة البيانات
    user_pairs = _load_user_selected_pairs(user_info.get('user_id'))
    
    return render_template('dashboard.html',
                         user=user_info,
                         is_logged_in=True,
                         is_admin=user_info.get('is_admin', False),
                         selected_pairs_count=len(user_pairs))

# ======= صفحة اختيار الأزواج =======
@app.route('/pairs-selection')
@login_required
def pairs_selection():
    """صفحة اختيار الأزواج"""
    user_info = get_current_user()
    return render_template('pairs_selection.html',
                         user=user_info,
                         is_logged_in=True)


@app.route('/plans')
def plans():
    """صفحة الخطط"""
    user_info = get_current_user()
    return render_template('plans.html',
                         is_logged_in=user_info['success'],
                         user=user_info if user_info['success'] else None)


# ============ API مسارات ============

@app.route('/api/signals')
def api_signals():
    """API لجلب الإشارات"""
    try:
        signals = load_signals()
        user_info = get_current_user()
        filtered_signals = _filter_signals_for_user(signals, user_info)
        return jsonify(filtered_signals)
    except Exception as e:
        print(f"❌ خطأ في api_signals: {e}")
        return jsonify([])


@app.route('/api/recommendations')
def api_recommendations():
    """API لجلب التوصيات"""
    recommendations = load_recommendations()
    return jsonify(recommendations)


@app.route('/api/analysis')
def api_analysis():
    """API لجلب التحليلات"""
    analyses = load_analysis()
    user_info = get_current_user()
    if user_info.get('success'):
        selected_pairs = set(_load_user_selected_pairs(user_info.get('user_id')))
        if selected_pairs:
            analyses = [
                a for a in analyses
                if _normalize_symbol_key(
                    a.get('symbol') or a.get('pair') or a.get('instrument') or a.get('ticker')
                ) in selected_pairs
            ]
    return jsonify(analyses)


@app.route('/api/stats')
def api_stats():
    """API لجلب الإحصائيات"""
    return jsonify(get_statistics())


@app.route('/api/available-pairs')
def api_available_pairs():
    """API لجلب جميع الأزواج المتاحة"""
    return jsonify(get_all_available_pairs())

# ===== Helper function for available pairs =====
def get_all_available_pairs():
    """جلب جميع الأزواج المتاحة مصنفة بالشكل المتوقع في واجهة اختيار الأزواج."""
    categorized = {
        'forex_major': {},
        'forex_minor': {},
        'metals': {},
        'energy': {},
        'indices_us': {},
        'indices_europe': {},
        'indices_asia': {},
        'crypto': {},
    }

    forex_major = {'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'}
    forex_minor = {'EURJPY', 'GBPJPY', 'EURGBP', 'CADJPY', 'CHFJPY'}
    metals = {'XAUUSD', 'XAGUSD'}
    energy = {'WTI', 'BRENT', 'USOIL', 'UKOIL', 'NATGAS', 'NGAS'}
    indices_us = {'US30', 'NAS100', 'SPX500'}
    indices_europe = {'GER40', 'UK100', 'FRA40', 'EU50'}
    indices_asia = {'JPN225', 'HK50', 'CHN50'}
    crypto = {'BTCUSD', 'ETHUSD'}

    for symbol in YF_SYMBOLS.keys():
        normalized = (symbol or '').upper().replace('/', '').replace('-', '')

        if normalized in forex_major:
            categorized['forex_major'][symbol] = YF_SYMBOLS[symbol]
        elif normalized in forex_minor:
            categorized['forex_minor'][symbol] = YF_SYMBOLS[symbol]
        elif normalized in metals:
            categorized['metals'][symbol] = YF_SYMBOLS[symbol]
        elif normalized in energy:
            categorized['energy'][symbol] = YF_SYMBOLS[symbol]
        elif normalized in indices_us:
            categorized['indices_us'][symbol] = YF_SYMBOLS[symbol]
        elif normalized in indices_europe:
            categorized['indices_europe'][symbol] = YF_SYMBOLS[symbol]
        elif normalized in indices_asia:
            categorized['indices_asia'][symbol] = YF_SYMBOLS[symbol]
        elif normalized in crypto:
            categorized['crypto'][symbol] = YF_SYMBOLS[symbol]
        else:
            categorized['forex_minor'][symbol] = YF_SYMBOLS[symbol]

    return categorized


@app.route('/api/user-pairs-preferences')
@login_required
def api_get_user_pairs_preferences():
    """API لجلب تفضيلات المستخدم للأزواج"""
    user_info = get_current_user()
    if not user_info['success']:
        return jsonify({'success': False, 'message': 'غير مسجل'}), 401
    
    user_id = user_info['user_id']
    
    try:
        user_pairs = _load_user_selected_pairs(user_id)
        return jsonify({'success': True, 'pairs': user_pairs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/save-pairs-preferences', methods=['POST'])
@login_required
def api_save_pairs_preferences():
    """API لحفظ تفضيلات المستخدم للأزواج"""
    user_info = get_current_user()
    if not user_info['success']:
        return jsonify({'success': False, 'message': 'غير مسجل'}), 401
    
    user_id = user_info['user_id']
    data = request.get_json(silent=True) or {}
    pairs = data.get('pairs', [])
    
    try:
        ok = _save_user_selected_pairs(user_id, pairs)
        if not ok:
            return jsonify({'success': False, 'message': 'تعذر حفظ التفضيلات'}), 500

        saved_pairs = _load_user_selected_pairs(user_id)
        return jsonify({
            'success': True,
            'message': 'تم حفظ التفضيلات بنجاح',
            'pairs_count': len(saved_pairs),
            'pairs': saved_pairs
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/user')
def api_user():
    """API لجلب بيانات المستخدم الحالي"""
    user_info = get_current_user()
    if user_info['success']:
        return jsonify(user_info)
    return jsonify({'success': False}), 401


@app.route('/api/detailed-report')
def api_detailed_report():
    """API للتقرير التفصيلي"""
    return jsonify(get_detailed_report())


@app.route('/reports')
@login_required
def reports():
    """صفحة التقارير والإحصائيات"""
    user_info = get_current_user()
    return render_template('reports.html',
                         user=user_info,
                         is_logged_in=True)

@app.route('/admin')
@admin_required
def admin():
    """توافق مع الروابط القديمة: تحويل إلى لوحة الإدارة الموحدة"""
    return redirect(url_for('admin_panel'))

def _collect_admin_users_merged(limit=2000):
    """دمج المستخدمين من users.db و vip_subscriptions.db لإظهار كامل المستخدمين."""
    merged = {}
    safe_limit = max(1, int(limit or 2000))

    try:
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT id, username, email, full_name, plan, created_at, is_admin, is_active
            FROM users
            ORDER BY created_at DESC
            LIMIT ?
        ''', (safe_limit,))
        for row in c.fetchall():
            item = dict(row)
            key = str(item.get('id') or '').strip() or str(item.get('username') or '').strip().lower()
            if not key:
                continue
            merged[key] = {
                'id': item.get('id'),
                'user_id': item.get('id'),
                'username': item.get('username'),
                'email': item.get('email'),
                'full_name': item.get('full_name'),
                'plan': item.get('plan') or 'free',
                'status': 'active' if int(item.get('is_active') or 0) == 1 else 'inactive',
                'created_at': item.get('created_at'),
                'is_admin': int(item.get('is_admin') or 0),
                'is_active': int(item.get('is_active') or 0),
                'source': 'users.db'
            }
        conn.close()
    except Exception:
        pass

    try:
        conn = sqlite3.connect('vip_subscriptions.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('PRAGMA table_info(users)')
        cols = {r[1] for r in c.fetchall()}
        q_cols = [x for x in ['user_id', 'username', 'email', 'plan', 'status', 'subscription_end', 'chat_id', 'telegram_id', 'created_at'] if x in cols]
        if q_cols and 'user_id' in cols:
            c.execute(f"SELECT {', '.join(q_cols)} FROM users ORDER BY user_id DESC LIMIT ?", (safe_limit,))
            for row in c.fetchall():
                item = dict(row)
                uid = item.get('user_id')
                username = item.get('username')
                key = str(uid or '').strip() or str(username or '').strip().lower()
                if not key:
                    continue
                existing = merged.get(key, {})
                merged[key] = {
                    'id': existing.get('id') if existing else uid,
                    'user_id': uid,
                    'username': username or existing.get('username'),
                    'email': item.get('email') or existing.get('email'),
                    'full_name': existing.get('full_name'),
                    'plan': item.get('plan') or existing.get('plan') or 'free',
                    'status': item.get('status') or existing.get('status') or 'unknown',
                    'created_at': item.get('created_at') or existing.get('created_at') or item.get('subscription_end'),
                    'is_admin': int(existing.get('is_admin') or 0),
                    'is_active': int(existing.get('is_active') or (1 if str(item.get('status') or '').lower() in ('active', 'trial') else 0)),
                    'subscription_end': item.get('subscription_end'),
                    'chat_id': item.get('chat_id'),
                    'telegram_id': item.get('telegram_id'),
                    'source': 'users.db+vip_subscriptions.db' if existing else 'vip_subscriptions.db'
                }
        conn.close()
    except Exception:
        pass

    users = list(merged.values())
    users.sort(key=lambda u: (_parse_datetime_flexible(u.get('created_at')) or datetime.min), reverse=True)
    return users


# ======= Admin APIs =======
@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    users = _collect_admin_users_merged(limit=2000)
    return jsonify({'success': True, 'users': users})

@app.route('/api/admin/set_admin', methods=['POST'])
@admin_required
def api_admin_set_admin():
    data = request.json or {}
    user_id = data.get('user_id')
    is_admin = bool(data.get('is_admin'))
    result = user_manager.set_admin_status(user_id, is_admin)
    return jsonify(result)

@app.route('/api/admin/set_active', methods=['POST'])
@admin_required
def api_admin_set_active():
    data = request.json or {}
    user_id = data.get('user_id')
    is_active = bool(data.get('is_active'))
    result = user_manager.set_active_status(user_id, is_active)
    return jsonify(result)

@app.route('/api/admin/subscriptions')
@admin_required
def api_admin_subscriptions():
    """الحصول على جميع الاشتراكات"""
    sync_summary = _sync_registered_users_to_subscriptions(prefer_trial_for_missing=False)
    subscriptions = _enrich_subscriptions_with_activity(subscription_manager.get_all_subscriptions())
    return jsonify({'success': True, 'subscriptions': subscriptions, 'sync': sync_summary})


@app.route('/api/admin/subscriptions/sync-users', methods=['POST'])
@admin_required
def api_admin_sync_users_to_subscriptions():
    """مزامنة المستخدمين المسجلين مع قاعدة بيانات الاشتراكات."""
    data = request.get_json(silent=True) or {}
    prefer_trial = bool(data.get('prefer_trial', False))
    summary = _sync_registered_users_to_subscriptions(prefer_trial_for_missing=prefer_trial)
    return jsonify({'success': True, 'sync': summary})


@app.route('/api/admin/recover-users', methods=['POST'])
@admin_required
def api_admin_recover_users():
    """تشغيل الاسترجاع اليدوي لبيانات المستخدمين والاشتراكات."""
    payload = request.get_json(silent=True) or {}
    force_sync = bool(payload.get('force_sync', True))
    prefer_trial = bool(payload.get('prefer_trial', False))
    merge_missing = bool(payload.get('merge_missing', True))

    backup_info = _snapshot_core_databases(reason='admin_recover_users', actor='admin') if BACKUP_ON_ADMIN_WRITE else None

    users_result = _recover_users_db_if_empty()
    vip_result = _recover_vip_subscriptions_if_empty()
    users_merge_result = {'merged': 0, 'sources': []}
    vip_merge_result = {'merged': 0, 'sources': []}
    if merge_missing:
        users_merge_result = _merge_users_from_legacy_sources(limit_sources=15)
        vip_merge_result = _merge_vip_users_from_legacy_sources(limit_sources=15)
    sync_result = None
    if force_sync:
        sync_result = _sync_registered_users_to_subscriptions(prefer_trial_for_missing=prefer_trial)

    users_count = _table_row_count(USERS_DB_PATH, 'users')
    vip_users_count = _table_row_count(VIP_SUBSCRIPTIONS_DB_PATH, 'users')

    _log_admin_audit(
        action='admin_recover_users',
        target_user_id=None,
        details={
            'force_sync': force_sync,
            'prefer_trial': prefer_trial,
            'merge_missing': merge_missing,
            'backup': backup_info,
            'users_result': users_result,
            'vip_result': vip_result,
            'users_merge_result': users_merge_result,
            'vip_merge_result': vip_merge_result,
            'sync_result': sync_result,
            'users_count': users_count,
            'vip_users_count': vip_users_count
        }
    )

    return jsonify({
        'success': True,
        'users_db': str(USERS_DB_PATH),
        'vip_subscriptions_db': str(VIP_SUBSCRIPTIONS_DB_PATH),
        'users_result': users_result,
        'vip_result': vip_result,
        'users_merge_result': users_merge_result,
        'vip_merge_result': vip_merge_result,
        'sync_result': sync_result,
        'backup': backup_info,
        'force_sync': force_sync,
        'merge_missing': merge_missing,
        'users_count': users_count,
        'vip_users_count': vip_users_count
    })


@app.route('/admin/recover-users-now', methods=['GET'])
@admin_required
def admin_recover_users_now():
    """تنفيذ استرجاع ومزامنة المشتركين من رابط مباشر للأدمن ثم العودة لإدارة الاشتراكات."""
    users_result = _recover_users_db_if_empty()
    vip_result = _recover_vip_subscriptions_if_empty()
    users_merge_result = _merge_users_from_legacy_sources(limit_sources=15)
    vip_merge_result = _merge_vip_users_from_legacy_sources(limit_sources=15)
    sync_result = _sync_registered_users_to_subscriptions(prefer_trial_for_missing=False)

    users_count = _table_row_count(USERS_DB_PATH, 'users')
    vip_users_count = _table_row_count(VIP_SUBSCRIPTIONS_DB_PATH, 'users')

    flash(
        (
            f"Recovery done: users={users_count}, vip={vip_users_count}, "
            f"users_merged={int(users_merge_result.get('merged', 0) or 0)}, "
            f"vip_merged={int(vip_merge_result.get('merged', 0) or 0)}, "
            f"linked={int(sync_result.get('linked', 0) or 0)}, "
            f"failed={int(sync_result.get('failed', 0) or 0)}"
        ),
        'success'
    )

    if int(users_result.get('restored', 0) or 0) > 0 or int(vip_result.get('restored', 0) or 0) > 0 or int(users_merge_result.get('merged', 0) or 0) > 0 or int(vip_merge_result.get('merged', 0) or 0) > 0:
        print(f"[MANUAL-RECOVERY] users={users_result} vip={vip_result} users_merge={users_merge_result} vip_merge={vip_merge_result} sync={sync_result}")

    return redirect(url_for('subscription_management'))


@app.route('/admin/import-backup', methods=['GET', 'POST'])
@admin_required
def admin_import_backup():
    """رفع ملفات قواعد بيانات محلية ودمجها في قواعد السيرفر الحالية."""
    if request.method == 'GET':
        return '''
        <!doctype html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="utf-8">
            <title>استيراد نسخة احتياطية</title>
            <style>
                body { font-family: Tahoma, Arial, sans-serif; background:#0f172a; color:#e5e7eb; margin:0; padding:32px; }
                .box { max-width:760px; margin:0 auto; background:#111827; padding:24px; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,.25); }
                h1 { margin-top:0; font-size:28px; }
                p { line-height:1.7; color:#cbd5e1; }
                label { display:block; margin:18px 0 8px; font-weight:bold; }
                input[type=file] { display:block; width:100%; padding:12px; background:#1f2937; color:#e5e7eb; border:1px solid #374151; border-radius:10px; }
                button, a.btn { display:inline-block; margin-top:20px; padding:12px 18px; border-radius:10px; border:none; text-decoration:none; cursor:pointer; }
                button { background:#d4a017; color:#111827; font-weight:bold; }
                a.btn { background:#374151; color:#f9fafb; margin-right:12px; }
                .hint { font-size:14px; color:#93c5fd; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>استيراد نسخة احتياطية للمستخدمين والاشتراكات</h1>
                <p>إذا كانت قاعدة Render فارغة، ارفع هنا ملفاتك المحلية مثل <strong>users.db</strong> و <strong>vip_subscriptions.db</strong> وسيتم دمجها داخل قاعدة السيرفر الحالية بدون حذف البيانات الموجودة.</p>
                <form method="post" enctype="multipart/form-data">
                    <label for="users_db">ملف users.db</label>
                    <input id="users_db" name="users_db" type="file" accept=".db,.sqlite,.sqlite3">

                    <label for="vip_db">ملف vip_subscriptions.db</label>
                    <input id="vip_db" name="vip_db" type="file" accept=".db,.sqlite,.sqlite3">

                    <div class="hint">يمكنك رفع ملف واحد أو الملفين معًا. بعد الدمج سيتم تشغيل مزامنة المشتركين تلقائيًا.</div>
                    <button type="submit">بدء الاستيراد والدمج</button>
                    <a class="btn" href="/subscriptions_management">العودة لإدارة الاشتراكات</a>
                </form>
            </div>
        </body>
        </html>
        '''

    users_file = request.files.get('users_db')
    vip_file = request.files.get('vip_db')
    admin_name = session.get('local_admin_username') or (get_current_user() or {}).get('username') or 'admin'

    if (not users_file or not users_file.filename) and (not vip_file or not vip_file.filename):
        flash('لم يتم اختيار أي ملف للاستيراد.', 'error')
        return redirect(url_for('admin_import_backup'))

    import_dir = DATA_DIR / 'imports'
    try:
        import_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    backup_info = _snapshot_core_databases(reason='admin_import_backup', actor=admin_name) if BACKUP_ON_ADMIN_WRITE else None
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    users_result = {'merged': 0, 'source': None, 'reason': 'not_uploaded'}
    vip_result = {'merged': 0, 'source': None, 'reason': 'not_uploaded'}

    if users_file and users_file.filename:
        users_path = import_dir / f'users_upload_{stamp}.db'
        users_file.save(str(users_path))
        users_result = _merge_users_from_source_db(users_path)

    if vip_file and vip_file.filename:
        vip_path = import_dir / f'vip_upload_{stamp}.db'
        vip_file.save(str(vip_path))
        vip_result = _merge_vip_users_from_source_db(vip_path)

    sync_result = _sync_registered_users_to_subscriptions(prefer_trial_for_missing=False)

    _log_admin_audit(
        action='admin_import_backup',
        target_user_id=None,
        details={
            'backup': backup_info,
            'users_result': users_result,
            'vip_result': vip_result,
            'sync_result': sync_result
        }
    )

    flash(
        (
            f"Import done: users_merged={int(users_result.get('merged', 0) or 0)}, "
            f"vip_merged={int(vip_result.get('merged', 0) or 0)}, "
            f"linked={int(sync_result.get('linked', 0) or 0)}, "
            f"failed={int(sync_result.get('failed', 0) or 0)}"
        ),
        'success'
    )
    return redirect(url_for('subscription_management'))

@app.route('/api/admin/update_plan', methods=['POST'])
@admin_required
def api_admin_update_plan():
    """تحديث خطة المستخدم - يتم إلغاء الاشتراكات السابقة وتفعيل الخطة الجديدة فقط"""
    data = request.json or {}
    user_id = data.get('user_id')
    plan = data.get('plan')
    duration_days = data.get('duration_days')
    
    try:
        backup_info = _snapshot_core_databases(reason='admin_update_plan', actor='admin') if BACKUP_ON_ADMIN_WRITE else None
        # إلغاء جميع الاشتراكات النشطة السابقة
        try:
            import sqlite3
            conn_vip = sqlite3.connect('vip_subscriptions.db')
            cursor_vip = conn_vip.cursor()
            
            cursor_vip.execute('''
                UPDATE users 
                SET status = 'cancelled', subscription_end = ?
                WHERE user_id = ? AND status IN ('active', 'trial')
            ''', (datetime.now().isoformat(), user_id))
            
            conn_vip.commit()
            conn_vip.close()
        except Exception as e:
            print(f"تحذير: خطأ في إلغاء الاشتراكات السابقة: {e}")
        
        # تفعيل الخطة الجديدة
        success, message = subscription_manager.update_subscription_plan(
            user_id, plan, duration_days
        )
        
        # تحديث في جدول users أيضاً
        if success:
            user_manager.update_user_plan(user_id, plan)

        _log_admin_audit(
            action='admin_update_plan',
            target_user_id=user_id,
            details={
                'plan': plan,
                'duration_days': duration_days,
                'success': bool(success),
                'message': message,
                'backup': backup_info
            }
        )
        
        return jsonify({
            'success': success, 
            'message': f'{message} - تم إلغاء الاشتراكات السابقة تلقائياً.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/extend_subscription', methods=['POST'])
@admin_required
def api_admin_extend_subscription():
    """تمديد اشتراك المستخدم"""
    data = request.json or {}
    user_id = data.get('user_id')
    days = int(data.get('days', 0))
    
    success, message = subscription_manager.extend_subscription(user_id, days)
    return jsonify({'success': success, 'message': message})

@app.route('/api/admin/cancel_subscription', methods=['POST'])
@admin_required
def api_admin_cancel_subscription():
    """إلغاء اشتراك المستخدم"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    backup_info = _snapshot_core_databases(reason='admin_cancel_subscription', actor='admin') if BACKUP_ON_ADMIN_WRITE else None
    success, message = subscription_manager.cancel_subscription(user_id)
    _log_admin_audit('admin_cancel_subscription', target_user_id=user_id, details={'success': bool(success), 'message': message, 'backup': backup_info})
    return jsonify({'success': success, 'message': message})

@app.route('/api/admin/reactivate_subscription', methods=['POST'])
@admin_required
def api_admin_reactivate_subscription():
    """إعادة تفعيل اشتراك المستخدم"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    backup_info = _snapshot_core_databases(reason='admin_reactivate_subscription', actor='admin') if BACKUP_ON_ADMIN_WRITE else None
    success, message = subscription_manager.reactivate_subscription(user_id)
    _log_admin_audit('admin_reactivate_subscription', target_user_id=user_id, details={'success': bool(success), 'message': message, 'backup': backup_info})
    return jsonify({'success': success, 'message': message})

@app.route('/api/admin/activate_subscription', methods=['POST'])
@admin_required
def api_admin_activate_subscription():
    """تفعيل اشتراك المستخدم"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    try:
        backup_info = _snapshot_core_databases(reason='admin_activate_subscription', actor='admin') if BACKUP_ON_ADMIN_WRITE else None
        import sqlite3
        conn = sqlite3.connect('vip_subscriptions.db')
        cursor = conn.cursor()
        
        # تحديث حالة المستخدم إلى نشط
        cursor.execute('''
            UPDATE users 
            SET status = 'active'
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        _log_admin_audit('admin_activate_subscription', target_user_id=user_id, details={'success': True, 'backup': backup_info})
        return jsonify({'success': True, 'message': 'تم تفعيل الاشتراك بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في تفعيل الاشتراك: {str(e)}'})

@app.route('/api/admin/deactivate_subscription', methods=['POST'])
@admin_required
def api_admin_deactivate_subscription():
    """إيقاف اشتراك المستخدم مؤقتاً"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    try:
        backup_info = _snapshot_core_databases(reason='admin_deactivate_subscription', actor='admin') if BACKUP_ON_ADMIN_WRITE else None
        import sqlite3
        conn = sqlite3.connect('vip_subscriptions.db')
        cursor = conn.cursor()
        
        # تحديث حالة المستخدم إلى غير نشط
        cursor.execute('''
            UPDATE users 
            SET status = 'inactive'
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        _log_admin_audit('admin_deactivate_subscription', target_user_id=user_id, details={'success': True, 'backup': backup_info})
        return jsonify({'success': True, 'message': 'تم إيقاف الاشتراك مؤقتاً'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في إيقاف الاشتراك: {str(e)}'})


@app.route('/api/admin/delete_user', methods=['POST'])
@admin_required
def api_admin_delete_user():
    """حذف إداري منطقي للمستخدم/المشترك مع حفظ كامل البيانات وإمكانية الاستعادة."""
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    reason = str(data.get('reason') or 'admin_request').strip()
    admin_name = session.get('local_admin_username') or (get_current_user() or {}).get('username') or 'admin'

    if not user_id:
        return jsonify({'success': False, 'error': 'missing_user_id'}), 400

    backup_info = _snapshot_core_databases(reason='admin_soft_delete_user', actor=admin_name) if BACKUP_ON_ADMIN_WRITE else None
    user_result = user_manager.soft_delete_user(user_id, admin_username=admin_name, reason=reason)

    vip_result = False
    try:
        if hasattr(subscription_manager, 'soft_delete_user'):
            vip_result = bool(subscription_manager.soft_delete_user(user_id, admin_username=admin_name, reason=reason))
    except Exception:
        vip_result = False

    _log_admin_audit(
        action='admin_soft_delete_user',
        target_user_id=user_id,
        details={'reason': reason, 'user_result': user_result, 'vip_result': vip_result, 'backup': backup_info}
    )

    ok = bool((user_result or {}).get('success')) or bool(vip_result)
    return jsonify({'success': ok, 'user_result': user_result, 'vip_result': vip_result, 'backup': backup_info})


@app.route('/api/admin/restore_user', methods=['POST'])
@admin_required
def api_admin_restore_user():
    """استعادة مستخدم/مشترك محذوف إداريًا."""
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    admin_name = session.get('local_admin_username') or (get_current_user() or {}).get('username') or 'admin'

    if not user_id:
        return jsonify({'success': False, 'error': 'missing_user_id'}), 400

    backup_info = _snapshot_core_databases(reason='admin_restore_user', actor=admin_name) if BACKUP_ON_ADMIN_WRITE else None
    user_result = user_manager.restore_user(user_id, admin_username=admin_name)

    vip_result = False
    try:
        if hasattr(subscription_manager, 'restore_user'):
            vip_result = bool(subscription_manager.restore_user(user_id))
    except Exception:
        vip_result = False

    _log_admin_audit(
        action='admin_restore_user',
        target_user_id=user_id,
        details={'user_result': user_result, 'vip_result': vip_result, 'backup': backup_info}
    )

    ok = bool((user_result or {}).get('success')) or bool(vip_result)
    return jsonify({'success': ok, 'user_result': user_result, 'vip_result': vip_result, 'backup': backup_info})


@app.route('/api/admin/audit-log')
@admin_required
def api_admin_audit_log():
    """آخر سجلات تدقيق إجراءات الأدمن المتعلقة بالمستخدمين والاشتراكات."""
    limit = max(1, min(500, int(request.args.get('limit', 50) or 50)))
    try:
        _ensure_admin_audit_table()
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            '''
            SELECT id, admin_username, action, target_user_id, details, created_at
            FROM admin_audit_log
            ORDER BY id DESC
            LIMIT ?
            ''',
            (limit,)
        )
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify({'success': True, 'rows': rows, 'count': len(rows)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/subscription_requests')
@admin_required
def api_admin_subscription_requests():
    """الحصول على طلبات الاشتراك المعلقة"""
    try:
        import sqlite3
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, username, email, full_name, plan, price, 
                   duration_days, request_date, status, payment_proof, admin_notes
            FROM subscription_requests
            ORDER BY 
                CASE status 
                    WHEN 'pending' THEN 1 
                    WHEN 'processing' THEN 2 
                    ELSE 3 
                END,
                request_date DESC
        ''')
        
        requests_list = []
        for row in cursor.fetchall():
            requests_list.append({
                'id': row[0],
                'user_id': row[1],
                'username': row[2],
                'email': row[3],
                'full_name': row[4],
                'plan': row[5],
                'price': row[6],
                'duration_days': row[7],
                'request_date': row[8],
                'status': row[9],
                'payment_proof': row[10],
                'admin_notes': row[11]
            })
        
        conn.close()
        return jsonify({'success': True, 'requests': requests_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/approve_subscription', methods=['POST'])
@admin_required
def api_admin_approve_subscription():
    """الموافقة على طلب اشتراك وتفعيله - يتم تفعيل الخطة الأعلى فقط"""
    data = request.json or {}
    request_id = data.get('request_id')
    admin_notes = data.get('admin_notes', '')
    
    try:
        import sqlite3
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # جلب بيانات الطلب
        cursor.execute('''
            SELECT user_id, plan, duration_days, email
            FROM subscription_requests
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'success': False, 'error': 'الطلب غير موجود أو تم معالجته مسبقاً'})
        
        user_id, plan, duration_days, user_email = result
        
        # إلغاء جميع الاشتراكات النشطة السابقة للمستخدم في vip_subscriptions
        # حتى يكون لديه اشتراك واحد فقط (الخطة الأعلى/الجديدة)
        try:
            conn_vip = sqlite3.connect('vip_subscriptions.db')
            cursor_vip = conn_vip.cursor()
            
            # إلغاء الاشتراكات النشطة السابقة
            cursor_vip.execute('''
                UPDATE users 
                SET status = 'cancelled', subscription_end = ?
                WHERE user_id = ? AND status IN ('active', 'trial')
            ''', (datetime.now().isoformat(), user_id))
            
            conn_vip.commit()
            conn_vip.close()
        except Exception as e:
            print(f"تحذير: خطأ في إلغاء الاشتراكات السابقة في VIP: {e}")
        
        # تفعيل الاشتراك الجديد في users.db
        user_manager.update_user_plan(user_id, plan)
        
        # تفعيل الاشتراك الجديد في vip_subscriptions.db
        subscription_manager.update_subscription_plan(user_id, plan, duration_days)
        
        # تحديث حالة الطلب
        cursor.execute('''
            UPDATE subscription_requests
            SET status = 'approved', admin_notes = ?
            WHERE id = ?
        ''', (admin_notes, request_id))
        
        conn.commit()
        conn.close()
        
        # إرسال إيميل تأكيد
        end_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')
        email_service.send_activation_confirmation(user_email, plan, end_date)
        
        return jsonify({
            'success': True, 
            'message': f'تم تفعيل خطة {plan.upper()} بنجاح. تم إلغاء الاشتراكات السابقة تلقائياً.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/reject_subscription', methods=['POST'])
@admin_required
def api_admin_reject_subscription():
    """رفض طلب اشتراك"""
    data = request.json or {}
    request_id = data.get('request_id')
    admin_notes = data.get('admin_notes', '')
    
    try:
        import sqlite3
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE subscription_requests
            SET status = 'rejected', admin_notes = ?
            WHERE id = ?
        ''', (admin_notes, request_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'تم رفض الطلب'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """API للاشتراك مع معلومات الموقع وطريقة الدفع"""
    user_info = get_current_user()
    
    if not user_info['success']:
        return jsonify({'success': False, 'error': 'يجب تسجيل الدخول أولاً'}), 401
    
    data = request.json
    plan = data.get('plan', 'bronze')
    duration_key = _normalize_duration_key(data.get('duration_key', 'monthly'))
    location = data.get('location', 'jordan')  # jordan أو international
    payment_method = data.get('payment_method', 'cliq')  # cliq, bank_transfer, visa, crypto
    transaction_id = data.get('transaction_id', '')  # رقم العملية أو المعاملة
    
    try:
        if plan == 'free':
            plan_data = {
                'name': 'Free',
                'price': 0,
                'duration_days': 0,
                'duration_key': 'monthly',
                'duration_label': 'مجاني',
                'signals_per_day': 1,
                'signals': 1,
                'plan': 'free'
            }
        else:
            plan_data = _build_plan_data(plan, duration_key)
            if not plan_data:
                return jsonify({'success': False, 'error': 'خطة غير صحيحة'}), 400
        
        # إضافة معلومات الموقع والدفع
        payment_info = {
            'location': location,
            'payment_method': payment_method,
            'transaction_id': transaction_id,
            'duration_key': plan_data.get('duration_key'),
            'duration_label': plan_data.get('duration_label')
        }
        
        # حفظ طلب الاشتراك وإرسال إيميل
        success, message = email_service.send_subscription_request(user_info, plan_data, payment_info)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'تم استلام طلبك للخطة {plan_data["name"]}. سيتم التواصل معك بعد التحقق من الدفع على البريد: {user_info["email"]}',
                'pending': True
            })
        else:
            return jsonify({
                'success': False,
                'error': 'حدث خطأ في إرسال الطلب'
            }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ============ لوحة تحكم المشرف - Admin Panel ============

@app.route('/admin-panel')
@admin_required
def admin_panel():
    """صفحة لوحة تحكم المشرف"""
    user_info = get_current_user()
    
    # إحصائيات عامة
    all_subscriptions = subscription_manager.get_all_subscriptions()
    active_users = subscription_manager.get_all_active_users()
    
    # إحصائيات الخطط
    plans_stats = {}
    for sub in all_subscriptions:
        # sub is a dictionary
        plan = sub.get('plan', 'free') if isinstance(sub, dict) else (sub[3] if len(sub) > 3 else 'free')
        plans_stats[plan] = plans_stats.get(plan, 0) + 1
    
    # آخر الإشارات والتوصيات (نسخة خفيفة لتسريع فتح لوحة التحكم)
    recent_signals = load_admin_recent_signals(limit=5)
    all_recommendations = load_recommendations()
    recent_recommendations = all_recommendations[:5]
    
    stats = {
        'total_users': len(all_subscriptions),
        'active_users': len(active_users),
        'total_signals': count_active_signals_today(),
        'total_recommendations': len(all_recommendations),
        'plans_stats': plans_stats
    }
    
    return render_template(
        'admin_panel.html',
        user_info=user_info,
        stats=stats,
        recent_signals=recent_signals,
        recent_recommendations=recent_recommendations
    )


@app.route('/admin/customer-communications', methods=['GET', 'POST'])
@admin_required
def admin_customer_communications():
    """إدارة تواصل الأدمن مع العملاء عبر البريد وتصدير جهات واتساب."""
    user_info = get_current_user()
    contacts = user_manager.list_contactable_users(verified_only=False, marketing_only=False)
    recent_campaigns = _get_recent_email_campaigns(limit=100)
    delayed_pending_users = user_manager.list_pending_activation_users(older_than_hours=24)
    contact_query = str(request.args.get('contact_q', '') or '').strip().lower()
    campaign_query = str(request.args.get('campaign_q', '') or '').strip().lower()
    audience_filter = str(request.args.get('audience_filter', 'all') or 'all').strip().lower()
    campaign_type_filter = str(request.args.get('campaign_type_filter', 'all') or 'all').strip().lower()

    if contact_query:
        contacts = [
            row for row in contacts
            if contact_query in str(row.get('username') or '').lower()
            or contact_query in str(row.get('full_name') or '').lower()
            or contact_query in str(row.get('email') or '').lower()
            or contact_query in str(row.get('phone') or '').lower()
        ]

    if campaign_query:
        recent_campaigns = [
            row for row in recent_campaigns
            if campaign_query in str(row.get('subject') or '').lower()
            or campaign_query in str(row.get('actor_username') or '').lower()
            or campaign_query in str(row.get('audience') or '').lower()
            or campaign_query in str(row.get('campaign_type') or '').lower()
        ]

    if audience_filter in ('marketing', 'all_verified'):
        recent_campaigns = [row for row in recent_campaigns if str(row.get('audience') or '').strip().lower() == audience_filter]
    if campaign_type_filter in ('welcome', 'update', 'promotion', 'important'):
        recent_campaigns = [row for row in recent_campaigns if str(row.get('campaign_type') or '').strip().lower() == campaign_type_filter]

    email_contacts = [row for row in contacts if str(row.get('email') or '').strip()]
    verified_email_contacts = [row for row in email_contacts if row.get('email_verified')]
    marketing_email_contacts = [row for row in verified_email_contacts if row.get('marketing_email_opt_in')]
    whatsapp_contacts = [row for row in contacts if str(row.get('phone') or '').strip() and row.get('whatsapp_opt_in')]

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        audience = request.form.get('audience', 'marketing')
        campaign_type = request.form.get('campaign_type', 'update').strip().lower() or 'update'

        if not subject or not body:
            flash('أدخل عنوان الرسالة ومحتواها قبل الإرسال.', 'danger')
            return render_template(
                'admin_customer_communications.html',
                user_info=user_info,
                contacts_preview=contacts[:100],
                communication_stats={
                    'total_contacts': len(contacts),
                    'email_contacts': len(email_contacts),
                    'verified_email_contacts': len(verified_email_contacts),
                    'marketing_email_contacts': len(marketing_email_contacts),
                    'whatsapp_contacts': len(whatsapp_contacts)
                },
                recent_campaigns=recent_campaigns,
                delayed_pending_users=delayed_pending_users,
                filter_state={
                    'contact_q': contact_query,
                    'campaign_q': campaign_query,
                    'audience_filter': audience_filter,
                    'campaign_type_filter': campaign_type_filter
                }
            )

        if audience == 'all_verified':
            recipients = verified_email_contacts
        else:
            recipients = marketing_email_contacts

        result = email_service.send_admin_broadcast(recipients, subject, body)
        _log_email_campaign(
            subject,
            body,
            campaign_type,
            audience,
            (user_info or {}).get('username', 'admin'),
            result
        )
        flash(result.get('message') or 'تمت معالجة الإرسال.', 'success' if result.get('sent', 0) > 0 else 'warning')
        for error in result.get('errors', [])[:5]:
            flash(error, 'warning')
        return redirect(url_for('admin_customer_communications'))

    return render_template(
        'admin_customer_communications.html',
        user_info=user_info,
        contacts_preview=contacts[:100],
        communication_stats={
            'total_contacts': len(contacts),
            'email_contacts': len(email_contacts),
            'verified_email_contacts': len(verified_email_contacts),
            'marketing_email_contacts': len(marketing_email_contacts),
            'whatsapp_contacts': len(whatsapp_contacts)
        },
        recent_campaigns=recent_campaigns,
        delayed_pending_users=delayed_pending_users,
        filter_state={
            'contact_q': contact_query,
            'campaign_q': campaign_query,
            'audience_filter': audience_filter,
            'campaign_type_filter': campaign_type_filter
        }
    )


@app.route('/admin/pending-activations')
@admin_required
def admin_pending_activations():
    """عرض الحسابات غير المفعلة والمتأخرة في التفعيل."""
    query = str(request.args.get('q', '') or '').strip().lower()
    older_than = max(0, int(request.args.get('older_than', '24') or 24))
    users = user_manager.list_pending_activation_users(older_than_hours=older_than)
    if query:
        users = [
            row for row in users
            if query in str(row.get('username') or '').lower()
            or query in str(row.get('full_name') or '').lower()
            or query in str(row.get('email') or '').lower()
            or query in str(row.get('phone') or '').lower()
        ]
    return render_template('admin_pending_activations.html', pending_users=users, filter_state={'q': query, 'older_than': older_than})


@app.route('/admin/pending-activations/<int:user_id>/resend', methods=['POST'])
@admin_required
def admin_resend_activation_for_user(user_id):
    """إعادة إرسال رابط التفعيل من لوحة الأدمن لحساب محدد."""
    profile = user_manager.get_user_info(user_id)
    if not profile:
        flash('المستخدم غير موجود.', 'danger')
        return redirect(url_for('admin_pending_activations'))
    if profile.get('email_verified'):
        flash('الحساب مفعل بالفعل.', 'info')
        return redirect(url_for('admin_pending_activations'))

    identifier = profile.get('email') or profile.get('username') or ''
    result = user_manager.regenerate_activation_token(identifier)
    if not result.get('success'):
        flash(result.get('message') or 'تعذر إنشاء رابط تفعيل جديد.', 'danger')
        return redirect(url_for('admin_pending_activations'))

    activation_link = _build_public_url(url_for('activate_account', token=result.get('activation_token')))
    sent, message = email_service.send_account_activation(
        result.get('email') or '',
        result.get('full_name') or result.get('username') or '',
        activation_link
    )
    flash('تم إرسال رابط التفعيل من لوحة الأدمن.' if sent else f'تعذر إرسال رابط التفعيل: {message}', 'success' if sent else 'warning')
    return redirect(url_for('admin_pending_activations'))


@app.route('/admin/pending-activations/<int:user_id>/activate', methods=['POST'])
@admin_required
def admin_activate_pending_user(user_id):
    """تفعيل حساب غير مفعل مباشرة من لوحة الأدمن عند تعذر وصول البريد."""
    result = user_manager.activate_user_by_id(user_id)
    flash(result.get('message') or 'تمت معالجة الطلب.', 'success' if result.get('success') else 'danger')
    return redirect(url_for('admin_pending_activations'))


@app.route('/admin/customer-communications/whatsapp-export.csv')
@admin_required
def admin_customer_communications_whatsapp_export():
    """تصدير جهات العملاء المصرح لهم عبر واتساب إلى ملف CSV."""
    contacts = user_manager.list_contactable_users(verified_only=False, marketing_only=False)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'username', 'full_name', 'email', 'phone', 'country', 'plan', 'created_at', 'last_login'])

    for row in contacts:
        phone = str(row.get('phone') or '').strip()
        if not phone or not row.get('whatsapp_opt_in'):
            continue
        writer.writerow([
            row.get('id'),
            row.get('username'),
            row.get('full_name'),
            row.get('email'),
            phone,
            row.get('country'),
            row.get('plan'),
            row.get('created_at'),
            row.get('last_login'),
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=goldpro_whatsapp_contacts.csv'}
    )

@app.route('/subscription-management')
@app.route('/subscriptions-management')
@app.route('/subscriptions_management')
@admin_required
def subscription_management():
    """صفحة إدارة الاشتراكات"""
    user_info = get_current_user()
    return render_template('subscriptions_management.html', user_info=user_info)


@app.route('/api/admin/site-settings', methods=['GET'])
@admin_required
def api_get_site_settings():
    """إرجاع إعدادات الدفع والدعم للأدمن."""
    return jsonify({'success': True, 'settings': get_site_settings()})


@app.route('/api/admin/site-settings', methods=['POST'])
@admin_required
def api_update_site_settings():
    """تحديث إعدادات الدفع والدعم من لوحة الأدمن."""
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'تنسيق البيانات غير صالح'}), 400

        is_valid, validation_error = validate_crypto_addresses(data)
        if not is_valid:
            return jsonify({'success': False, 'error': validation_error}), 400

        updated = save_site_settings(data)
        return jsonify({'success': True, 'settings': updated, 'message': 'تم حفظ الإعدادات بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/continuous-analyzer/run-once', methods=['POST'])
@admin_required
def api_continuous_analyzer_run_once():
    """تشغيل دورة تحليل فورية لجميع الأزواج وإرسال الإشارات الناتجة."""
    try:
        data = request.get_json(silent=True) or {}
        interval = str(data.get('interval', '1h')).strip() or '1h'
        max_symbols = data.get('max_symbols')
        force_live_raw = data.get('force_live', False)
        force_live = str(force_live_raw).strip().lower() in ('1', 'true', 'yes', 'on')
        try:
            max_symbols = int(max_symbols) if max_symbols is not None else None
        except Exception:
            max_symbols = None

        result = _run_continuous_analyzer_once(interval=interval, max_symbols=max_symbols, force_live=force_live)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/data-source-health', methods=['GET'])
@admin_required
def api_data_source_health():
    """فحص حالة جلب البيانات لكل الأزواج مع مصدر الجلب الفعلي."""
    try:
        interval = request.args.get('interval', '1h')
        outputsize = request.args.get('outputsize', '120')
        force_live_raw = request.args.get('force_live', '0')
        force_live = str(force_live_raw).strip().lower() in ('1', 'true', 'yes', 'on')
        try:
            outputsize = int(outputsize)
        except Exception:
            outputsize = 120

        result = _probe_data_sources(interval=interval, outputsize=outputsize, force_live=force_live)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/critical-symbols-health', methods=['GET'])
@admin_required
def api_admin_critical_symbols_health():
    """فحص سريع للأزواج الحرجة: الذهب/الطاقة/العملات الرقمية."""
    interval = request.args.get('interval', '1h')
    outputsize = max(30, min(500, int(request.args.get('outputsize', 120) or 120)))
    force_live = request.args.get('force_live', '1').strip().lower() in ('1', 'true', 'yes', 'on')

    critical_symbols = ['XAUUSD', 'XAGUSD', 'USOIL', 'UKOIL', 'NATGAS', 'BTCUSD', 'ETHUSD']
    rows = []

    try:
        from forex_analyzer import fetch_data, get_last_fetch_metadata  # type: ignore
    except Exception as e:
        return jsonify({'success': False, 'error': f'forex_analyzer import failed: {e}'}), 500

    for symbol in critical_symbols:
        item = {'symbol': symbol, 'ok': False, 'rows': 0, 'source': None, 'errors': []}
        try:
            df = fetch_data(symbol, interval, outputsize=outputsize, force_live=force_live)
            meta = get_last_fetch_metadata() or {}
            item['ok'] = True
            item['rows'] = int(len(df) if df is not None else 0)
            item['source'] = meta.get('source')
            item['errors'] = meta.get('errors') or []
        except Exception as e:
            try:
                meta = get_last_fetch_metadata() or {}
                item['source'] = meta.get('source')
                item['errors'] = (meta.get('errors') or []) + [str(e)]
            except Exception:
                item['errors'] = [str(e)]
        rows.append(item)

    ok_count = sum(1 for item in rows if item.get('ok'))
    return jsonify({
        'success': True,
        'interval': interval,
        'force_live': force_live,
        'ok': ok_count,
        'failed': len(rows) - ok_count,
        'rows': rows,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/admin/adaptive-thresholds', methods=['GET'])
@admin_required
def api_admin_adaptive_thresholds():
    """إرجاع إحصاءات الحدود التكيفية للأزواج والفريمات دون أي تغيير واجهة."""
    try:
        limit = request.args.get('limit', 30, type=int)
        overview = _build_adaptive_thresholds_overview(limit_rows=limit)
        return jsonify({'success': True, 'data': overview})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/public-ads', methods=['GET'])
@admin_required
def api_get_public_ads():
    """إرجاع إعلانات الصفحة الرئيسية للأدمن."""
    return jsonify({'success': True, 'ads': get_public_ads()})


@app.route('/api/admin/public-ads', methods=['POST'])
@admin_required
def api_update_public_ads():
    """تحديث إعلانات الصفحة الرئيسية من لوحة الأدمن."""
    try:
        data = request.get_json(silent=True)
        ads_payload = data
        if isinstance(data, dict):
            ads_payload = data.get('ads')

        if not isinstance(ads_payload, list):
            return jsonify({'success': False, 'error': 'يرجى إرسال مصفوفة إعلانات بصيغة JSON'}), 400

        updated_ads = save_public_ads(ads_payload)
        return jsonify({'success': True, 'ads': updated_ads, 'message': 'تم تحديث الإعلانات بنجاح'})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/news-sources', methods=['GET'])
@admin_required
def api_get_news_sources():
    """إرجاع إعدادات مصادر الأخبار الاقتصادية للأدمن."""
    return jsonify({'success': True, 'sources': get_economic_news_sources()})


@app.route('/api/admin/news-sources', methods=['POST'])
@admin_required
def api_update_news_sources():
    """تحديث إعدادات مصادر الأخبار الاقتصادية من لوحة الأدمن."""
    try:
        data = request.get_json(silent=True) or {}
        sources_payload = data.get('sources') if isinstance(data, dict) else data
        updated_sources = save_economic_news_sources(sources_payload)
        return jsonify({'success': True, 'sources': updated_sources, 'message': 'تم حفظ مصادر الأخبار بنجاح'})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/forex-analyzer')
@admin_required
def forex_analyzer():
    """توافق مع المسار القديم: المحلل الذكي والمتقدم نفس الصفحة"""
    return redirect(url_for('advanced_analyzer_page'))


@app.route('/strong-signals')
def strong_signals_page():
    """اختصار يحوّل إلى صفحة الإشارات القوية ضمن مسار forex-app مع نقل كل البارامترات."""
    query_args = request.args.to_dict(flat=True)
    return redirect(url_for('my_forex_strong_signals_page', **query_args))


@app.route('/smart-analyzer')
def smart_analyzer_redirect():
    """توافق فقط مع الروابط السابقة: تحويل إلى صفحة الإشارات القوية المستقلة."""
    query_args = request.args.to_dict(flat=True)
    return redirect(url_for('strong_signals_page', **query_args))


@app.route('/api/strong-signals')
def api_strong_signals():
    module = load_my_forex_module()
    symbol = request.args.get('symbol', 'ALL')
    interval = request.args.get('interval', '1h')
    result = module.get_strong_signals(symbol, interval)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@app.route('/api/smart-signals')
def api_smart_signals():
    """توافق فقط مع الاستدعاءات السابقة لنفس بيانات الإشارات القوية."""
    return api_strong_signals()


@app.route(f'{MY_FOREX_BASE_PATH}/debug-status')
def my_forex_debug_status():
    import traceback as tb
    info = {
        'MY_FOREX_APP_DIR': str(MY_FOREX_APP_DIR),
        'dir_exists': MY_FOREX_APP_DIR.exists(),
        'app_py_exists': (MY_FOREX_APP_DIR / 'app.py').exists(),
        'templates_dir_exists': MY_FOREX_TEMPLATES_DIR.exists(),
    }
    try:
        module = load_my_forex_module()
        info['module_loaded'] = True
        info['has_get_strong_signals'] = hasattr(module, 'get_strong_signals')
        info['has_SUPPORTED_SYMBOLS'] = hasattr(module, 'SUPPORTED_SYMBOLS')
        if hasattr(module, 'SUPPORTED_SYMBOLS'):
            info['symbol_count'] = len(module.SUPPORTED_SYMBOLS)
    except Exception as e:
        info['module_loaded'] = False
        info['module_error'] = f'{type(e).__name__}: {e}'
        info['module_traceback'] = tb.format_exc()
    return jsonify(info)


@app.route('/advanced_analyzer')
@app.route('/advanced-analyzer')
@admin_required
def advanced_analyzer_page():
    """صفحة المحلل المتقدم"""
    user_info = get_current_user()
    return render_template('advanced_analyzer.html', user_info=user_info)


@app.route(f'{MY_FOREX_BASE_PATH}')
def my_forex_home_page():
    query_args = request.args.to_dict(flat=True)
    return redirect(url_for('my_forex_strong_signals_page', **query_args))


@app.route(f'{MY_FOREX_BASE_PATH}/signals')
def my_forex_signals_page():
    module = load_my_forex_module()
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    signals_data = module.get_signals(symbol, interval)
    return render_template('my_forex/signals.html', signals=signals_data, **build_my_forex_context(symbol, interval))


@app.route(f'{MY_FOREX_BASE_PATH}/analyst')
def my_forex_analyst_page():
    module = load_my_forex_module()
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    analyst_data = module.get_analyst_view(symbol, interval)
    return render_template('my_forex/analyst.html', analyst=analyst_data, **build_my_forex_context(symbol, interval))


@app.route(f'{MY_FOREX_BASE_PATH}/strong-signals')
def my_forex_strong_signals_page():
    symbol = request.args.get('symbol', 'ALL')
    interval = request.args.get('interval', '1h')
    try:
        module = load_my_forex_module()
        strong_signals_data = module.get_strong_signals(symbol, interval)
    except Exception as e:
        import traceback
        strong_signals_data = {
            'success': False,
            'error': f'{type(e).__name__}: {e}',
            'traceback': traceback.format_exc(),
            'signals': [],
            'symbol': symbol,
            'interval': interval,
            'symbol_label': symbol,
            'scanned_symbols': 0,
            'matched_signals': 0,
            'scan_errors': [f'{type(e).__name__}: {e}'],
            'categories': [],
        }
    try:
        ctx = build_my_forex_context(symbol, interval, include_all_option=True)
    except Exception:
        ctx = {
            'symbol_options': [], 'grouped_symbol_options': [],
            'interval_options': ['1h'], 'selected_symbol': symbol,
            'selected_interval': interval, 'symbol_count': 0, 'interval_count': 1,
            'main_site_url': '/', 'return_to_param': quote('/', safe=''),
            'forex_base_path': MY_FOREX_BASE_PATH,
        }
    return render_template(
        'my_forex/strong_signals.html',
        strong_signals=strong_signals_data,
        **ctx,
    )


@app.route(f'{MY_FOREX_BASE_PATH}/trade-simulator')
def my_forex_trade_simulator_page():
    module = load_my_forex_module()
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    capital = request.args.get('capital', '1000')
    leverage = request.args.get('leverage', '100')
    risk_percent = request.args.get('risk_percent', '1')
    replay_bars = request.args.get('replay_bars', '24')
    embed_mode = request.args.get('embed', '0') == '1'
    simulation = module.get_trade_simulation(symbol, interval, capital, leverage, risk_percent, replay_bars)
    return render_template(
        'my_forex/trade_simulator.html',
        simulation=simulation,
        embed_mode=embed_mode,
        **build_my_forex_context(symbol, interval),
    )


@app.route(f'{MY_FOREX_BASE_PATH}/api/trade-simulator', methods=['GET', 'OPTIONS'])
def my_forex_trade_simulator_api():
    module = load_my_forex_module()
    if request.method == 'OPTIONS':
        return jsonify({}), 204

    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    capital = request.args.get('capital', '1000')
    leverage = request.args.get('leverage', '100')
    risk_percent = request.args.get('risk_percent', '1')
    replay_bars = request.args.get('replay_bars', '24')
    simulation = module.get_trade_simulation(symbol, interval, capital, leverage, risk_percent, replay_bars)
    status_code = 200 if simulation.get('success') else 400
    return jsonify(simulation), status_code


@app.route(f'{MY_FOREX_BASE_PATH}/advanced-analyzer')
@app.route(f'{MY_FOREX_BASE_PATH}/advanced_analyzer')
def my_forex_advanced_analyzer_page():
    symbol = request.args.get('symbol', 'EURUSD')
    interval = request.args.get('interval', '1h')
    return render_template(
        'my_forex/advanced_analyzer.html',
        strategy_options=['harmonic', 'elliott', 'head_shoulders', 'smc', 'ict', 'ist'],
        **build_my_forex_context(symbol, interval),
    )


@app.route(f'{MY_FOREX_BASE_PATH}/api/advanced-analysis', methods=['POST'])
@app.route(f'{MY_FOREX_BASE_PATH}/api/advanced_analysis', methods=['POST'])
def my_forex_advanced_analysis_api():
    data = request.json or {}
    symbol = data.get('symbol', 'EURUSD')
    interval = data.get('interval', '1h')

    try:
        try:
            from advanced_analyzer_engine import perform_full_analysis # type: ignore
        except ImportError:
            analyzer_path = Path(__file__).parent / 'advanced_analyzer_engine.py'
            spec = importlib.util.spec_from_file_location('advanced_analyzer_engine', str(analyzer_path))
            analyzer_module = importlib.util.module_from_spec(spec)
            sys.modules['advanced_analyzer_engine'] = analyzer_module
            spec.loader.exec_module(analyzer_module)
            perform_full_analysis = analyzer_module.perform_full_analysis

        result = perform_full_analysis(symbol, interval)
        if result.get('success'):
            return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': result.get('error', 'خطأ غير معروف')}), 400
    except Exception as error:
        return jsonify({'success': False, 'error': f'خطأ في التحليل: {error}'}), 500

@app.route('/api/forex-analysis', methods=['POST'])
@app.route('/api/advanced_analysis', methods=['POST'])
@app.route('/api/advanced-analysis', methods=['POST'])
@admin_required
def api_forex_analysis():
    """API لتحليل الفوركس - يستخدم المحلل المتقدم"""
    data = request.json or {}
    symbol = data.get('symbol', 'EUR/USD')
    interval = data.get('interval', '1h')
    
    try:

        # --- Fix ImportError for advanced_analyzer_engine ---
        try:
            from advanced_analyzer_engine import perform_full_analysis # type: ignore
        except ImportError:
            import importlib.util
            import sys
            from pathlib import Path
            analyzer_path = Path(__file__).parent / 'advanced_analyzer_engine.py'
            spec = importlib.util.spec_from_file_location('advanced_analyzer_engine', str(analyzer_path))
            analyzer_module = importlib.util.module_from_spec(spec)
            sys.modules['advanced_analyzer_engine'] = analyzer_module
            spec.loader.exec_module(analyzer_module)
            perform_full_analysis = analyzer_module.perform_full_analysis
        result = perform_full_analysis(symbol, interval)
        
        if result.get('success'):
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'خطأ غير معروف')})
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in forex analysis: {error_detail}")
        return jsonify({'success': False, 'error': f'خطأ في التحليل: {str(e)}'})


@app.route('/api/admin/send-signal', methods=['POST'])
@admin_required
def api_admin_send_signal():
    """إرسال إشارة من لوحة الأدمن"""
    try:
        data = request.json
        signal_id = str(data.get('signal_id') or '').strip()
        
        if not signal_id:
            return jsonify({'success': False, 'error': 'Signal ID is required'}), 400

        signal_data = None

        # 1) دعم الإشارات المولدة في قاعدة البيانات (signal_id رقمي)
        if signal_id.isdigit():
            conn = sqlite3.connect('vip_signals.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM signals WHERE signal_id = ? LIMIT 1', (int(signal_id),))
            row = c.fetchone()
            conn.close()

            if row:
                row_dict = dict(row)
                signal_type = str(row_dict.get('signal_type') or '').lower()
                signal_data = {
                    'signal_id': row_dict.get('signal_id'),
                    'symbol': row_dict.get('symbol'),
                    'signal': signal_type,
                    'rec': signal_type.upper() if signal_type else 'N/A',
                    'timeframe': row_dict.get('timeframe') or '1h',
                    'entry': float(row_dict.get('entry_price') or 0),
                    'sl': float(row_dict.get('stop_loss') or 0),
                    'tp1': float(row_dict.get('take_profit_1') or 0),
                    'tp2': float(row_dict.get('take_profit_2') or 0),
                    'tp3': float(row_dict.get('take_profit_3') or 0),
                    'quality_score': int(row_dict.get('quality_score') or 80),
                    'timestamp': row_dict.get('created_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'risk_reward_tp1': _compute_risk_reward(
                        row_dict.get('entry_price'),
                        row_dict.get('stop_loss'),
                        row_dict.get('take_profit_1')
                    ),
                    'follow_up_status': (
                        'closed' if (row_dict.get('status') == 'closed') else
                        'tp3_locked' if int(row_dict.get('tp3_locked') or 0) else
                        'tp2_locked' if int(row_dict.get('tp2_locked') or 0) else
                        'tp1_locked' if int(row_dict.get('tp1_locked') or 0) else
                        'active'
                    )
                }

        # 2) دعم الإشارات القديمة من ملفات JSON
        if signal_data is None:
            signal_file = SIGNALS_DIR / signal_id
            if signal_file.exists():
                with open(signal_file, 'r', encoding='utf-8') as f:
                    signal_data = json.load(f)

        if signal_data is None:
            return jsonify({'success': False, 'error': 'Signal not found'}), 404

        persisted_signal_id = _ensure_signal_payload_persisted(signal_data)
        if persisted_signal_id:
            signal_data['signal_id'] = persisted_signal_id
        
        # إرسال الإشارة إلى المشتركين
        result = telegram_sender.send_signal_to_subscribers(signal_data, signal_data.get('quality_score', 100))
        
        return jsonify({
            'success': True,
            'sent_count': result.get('sent_count', 0),
            'failed_count': result.get('failed_count', 0),
            'total_subscribers': result.get('total_subscribers', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/send-recommendation', methods=['POST'])
@admin_required
def api_admin_send_recommendation():
    """إرسال توصية من لوحة الأدمن"""
    try:
        data = request.json
        rec_id = data.get('recommendation_id')
        
        if not rec_id:
            return jsonify({'success': False, 'error': 'Recommendation ID is required'}), 400
        
        # البحث عن التوصية
        recommendations = load_recommendations()
        recommendation = None
        
        for rec in recommendations:
            rec_identifier = f"{rec.get('pair')}_{rec.get('timeframe')}_{rec.get('timestamp')}"
            if rec_identifier == rec_id or str(recommendations.index(rec)) == rec_id:
                recommendation = rec
                break
        
        if not recommendation:
            return jsonify({'success': False, 'error': 'Recommendation not found'}), 404

        _ensure_signal_payload_persisted(recommendation)
        
        # إرسال التوصية إلى المشتركين
        result = telegram_sender.send_recommendation_to_subscribers(recommendation)
        
        return jsonify({
            'success': True,
            'sent_count': result.get('sent_count', 0),
            'failed_count': result.get('failed_count', 0),
            'total_subscribers': result.get('total_subscribers', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/broadcast-targets', methods=['GET'])
@admin_required
def api_admin_get_broadcast_targets():
    """جلب أهداف البث الإضافية (تيليجرام/واتساب) من لوحة الأدمن."""
    config = telegram_sender.load_broadcast_targets()
    targets = config.get('targets', []) if isinstance(config, dict) else []
    if not isinstance(targets, list):
        targets = []
    return jsonify({'success': True, 'targets': targets})


@app.route('/api/admin/broadcast-targets', methods=['POST'])
@admin_required
def api_admin_save_broadcast_targets():
    """حفظ أهداف البث الإضافية (إضافة/تعديل/حذف/إيقاف) من لوحة الأدمن."""
    try:
        data = request.get_json(silent=True) or {}
        targets = data.get('targets', [])
        if not isinstance(targets, list):
            return jsonify({'success': False, 'error': 'targets must be a list'}), 400

        normalized_targets = []
        for idx, item in enumerate(targets):
            if not isinstance(item, dict):
                continue

            platform = str(item.get('platform') or item.get('type') or '').strip().lower()
            if platform not in ('telegram', 'telegram_channel', 'telegram_group', 'whatsapp', 'whatsapp_group'):
                continue

            target_id = str(item.get('id') or f'target_{idx+1}').strip()
            if not target_id:
                target_id = f'target_{idx+1}'

            target_obj = {
                'id': target_id,
                'name': str(item.get('name') or f'Target {idx+1}').strip(),
                'platform': platform,
                'enabled': bool(item.get('enabled', True))
            }

            if platform in ('telegram', 'telegram_channel', 'telegram_group'):
                chat_id = str(item.get('chat_id') or item.get('telegram_chat_id') or '').strip()
                if not chat_id:
                    continue
                target_obj['chat_id'] = chat_id
                target_obj['bot_mode'] = str(item.get('bot_mode') or 'all_active').strip().lower()
            else:
                webhook_url = str(item.get('webhook_url') or item.get('url') or '').strip()
                if not webhook_url:
                    continue
                target_obj['webhook_url'] = webhook_url
                target_obj['group_id'] = str(item.get('group_id') or item.get('to') or '').strip()
                target_obj['auth_token'] = str(item.get('auth_token') or '').strip()

            normalized_targets.append(target_obj)

        ok = telegram_sender.save_broadcast_targets({'targets': normalized_targets})
        if not ok:
            return jsonify({'success': False, 'error': 'Failed to save broadcast targets'}), 500

        return jsonify({'success': True, 'targets': normalized_targets, 'count': len(normalized_targets)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/send-report', methods=['POST'])
@admin_required
def api_admin_send_report():
    """إرسال تقرير مخصص من لوحة الأدمن"""
    try:
        data = request.json
        report_text = data.get('report_text', '').strip()
        report_type = data.get('report_type', 'custom')
        
        if not report_text:
            return jsonify({'success': False, 'error': 'Report text is required'}), 400
        
        # إضافة header للتقرير
        if report_type == 'daily':
            header = "📊 <b>التقرير اليومي - Daily Report</b>\n\n"
        elif report_type == 'weekly':
            header = "📈 <b>التقرير الأسبوعي - Weekly Report</b>\n\n"
        elif report_type == 'monthly':
            header = "🗓️ <b>التقرير الشهري - Monthly Report</b>\n\n"
        elif report_type == 'performance':
            header = "⭐ <b>تقرير الأداء - Performance Report</b>\n\n"
        else:
            header = "📋 <b>تقرير خاص - Special Report</b>\n\n"
        
        full_report = header + report_text
        
        # إرسال التقرير إلى المشتركين
        result = telegram_sender.send_report_to_subscribers(full_report)
        
        return jsonify({
            'success': True,
            'sent_count': result.get('sent_count', 0),
            'failed_count': result.get('failed_count', 0),
            'total_subscribers': result.get('total_subscribers', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/send-periodic-report', methods=['POST'])
@admin_required
def api_admin_send_periodic_report():
    """إرسال التقرير الزمني الجاهز مباشرة للمشتركين والأهداف المخصصة."""
    try:
        data = request.json or {}
        period = data.get('period', 'daily')
        report = _build_periodic_report(period=period)
        message_html = str(report.get('message_html') or '').strip()
        if not message_html:
            return jsonify({'success': False, 'error': 'تعذر إنشاء محتوى التقرير'}), 500

        subscribers_result = telegram_sender.send_report_to_subscribers(message_html)
        targets_result = telegram_sender.send_broadcast_to_configured_targets(message_html)

        return jsonify({
            'success': True,
            'period': report.get('period'),
            'period_label': report.get('period_label'),
            'subscribers_sent_count': subscribers_result.get('sent_count', 0),
            'subscribers_failed_count': subscribers_result.get('failed_count', 0),
            'subscribers_total': subscribers_result.get('total_subscribers', 0),
            'targets_sent_count': targets_result.get('sent_count', 0),
            'targets_failed_count': targets_result.get('failed_count', 0),
            'targets_total': targets_result.get('total_targets', 0),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/broadcast-message', methods=['POST'])
@admin_required
def api_admin_broadcast_message():
    """إرسال رسالة عامة لجميع المشتركين"""
    try:
        data = request.json
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # 1) إرسال للمشتركين (عبر البوتات النشطة)
        result = telegram_sender.send_report_to_subscribers(message_text)

        # 2) إرسال إضافي إلى الأهداف الخارجية المفعلة (قناة/جروب تيليجرام + واتساب)
        targets_result = telegram_sender.send_broadcast_to_configured_targets(message_text)
        
        return jsonify({
            'success': True,
            'sent_count': result.get('sent_count', 0),
            'failed_count': result.get('failed_count', 0),
            'total_subscribers': result.get('total_subscribers', 0),
            'targets_sent_count': targets_result.get('sent_count', 0),
            'targets_failed_count': targets_result.get('failed_count', 0),
            'targets_total': targets_result.get('total_targets', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ معالجات الأخطاء ============

@app.errorhandler(404)
def not_found(error):
    """صفحة الخطأ 404"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """صفحة الخطأ 500"""
    return render_template('500.html'), 500


# ============ تشغيل التطبيق ============

# ============== Admin Management Routes ==============

@app.route('/admin-management')
@admin_required
def admin_management():
    """صفحة إدارة صلاحيات الأدمن"""
    return render_template('admin_management.html')

@app.route('/api/admin/users/all', methods=['GET'])
@admin_required
def get_all_users():
    """الحصول على جميع المستخدمين"""
    try:
        users = _collect_admin_users_merged(limit=5000)
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/users/set-admin', methods=['POST'])
@admin_required
def set_admin_status():
    """تعيين أو إزالة صلاحيات الأدمن"""
    try:
        data = request.json
        user_id = data.get('user_id')
        is_admin = data.get('is_admin', False)
        
        if not user_id:
            return jsonify({'success': False, 'message': 'معرف المستخدم مطلوب'})
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # تحديث حالة الأدمن
        cursor.execute('''
            UPDATE users SET is_admin = ? WHERE id = ?
        ''', (1 if is_admin else 0, user_id))
        
        conn.commit()
        conn.close()
        
        message = 'تم منح صلاحيات المشرف بنجاح' if is_admin else 'تم إزالة صلاحيات المشرف بنجاح'
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============== Bot Management Routes ==============

@app.route('/bot-management')
@admin_required
def bot_management():
    """صفحة إدارة البوتات"""
    return render_template('bot_management.html')

@app.route('/api/admin/bots', methods=['GET'])
@admin_required
def get_bots():
    """الحصول على قائمة البوتات"""
    try:
        config = telegram_sender.load_bots_config()
        return jsonify({
            'success': True,
            'bots': config.get('bots', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        })

@app.route('/api/admin/bots/<int:bot_id>', methods=['GET'])
@admin_required
def get_bot(bot_id):
    """الحصول على بيانات بوت محدد"""
    try:
        config = telegram_sender.load_bots_config()
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        if bot:
            return jsonify({'success': True, 'bot': bot})
        else:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/test', methods=['POST'])
@admin_required
def test_bot_token():
    """اختبار توكن بوت"""
    try:
        data = request.json
        token = data.get('token')
        if not token:
            return jsonify({'success': False, 'message': 'التوكن مطلوب'})
        
        # اختبار التوكن
        import requests
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe')
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_name = bot_info['result']['first_name']
                return jsonify({
                    'success': True,
                    'bot_name': bot_name,
                    'message': 'التوكن صالح'
                })
        
        return jsonify({'success': False, 'message': 'التوكن غير صالح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/add', methods=['POST'])
@admin_required
def add_bot():
    """إضافة بوت جديد"""
    try:
        data = request.json
        name = data.get('name')
        token = data.get('token')
        description = data.get('description', '')
        is_default = data.get('is_default', False)
        
        if not name or not token:
            return jsonify({'success': False, 'message': 'الاسم والتوكن مطلوبان'})
        
        # اختبار التوكن أولاً
        import requests
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe')
        if response.status_code != 200 or not response.json().get('ok'):
            return jsonify({'success': False, 'message': 'التوكن غير صالح'})
        
        # تحميل الإعدادات
        config = telegram_sender.load_bots_config()
        
        # إنشاء ID جديد
        max_id = max([b['id'] for b in config.get('bots', [])], default=0)
        new_id = max_id + 1
        
        # إذا كان هذا البوت افتراضي، إلغاء الافتراضي من الآخرين
        if is_default:
            for bot in config.get('bots', []):
                bot['is_default'] = False
        
        # إضافة البوت الجديد
        new_bot = {
            'id': new_id,
            'name': name,
            'token': token,
            'status': 'active',
            'is_default': is_default,
            'created_at': datetime.now().isoformat(),
            'description': description
        }
        
        if 'bots' not in config:
            config['bots'] = []
        config['bots'].append(new_bot)
        
        # حفظ الإعدادات
        telegram_sender.save_bots_config(config)
        
        return jsonify({
            'success': True,
            'message': 'تمت إضافة البوت بنجاح',
            'bot': new_bot
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/<int:bot_id>/edit', methods=['POST'])
@admin_required
def edit_bot(bot_id):
    """ تعديل بوت"""
    try:
        data = request.json
        config = telegram_sender.load_bots_config()
        
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        if not bot:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
        
        # تحديث البيانات
        bot['name'] = data.get('name', bot['name'])
        bot['token'] = data.get('token', bot['token'])
        bot['description'] = data.get('description', bot.get('description', ''))
        
        # تحديث الافتراضي
        if data.get('is_default', False):
            for b in config.get('bots', []):
                b['is_default'] = False
        
        # تعيين هذا البوت كافتراضي
        bot['is_default'] = True
        telegram_sender.save_bots_config(config)
        
        return jsonify({'success': True, 'message': 'تم التعديل بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/<int:bot_id>/pause', methods=['POST'])
@admin_required
def pause_bot(bot_id):
    """إيقاف بوت مؤقتاً"""
    try:
        config = telegram_sender.load_bots_config()
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        
        if not bot:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
        
        bot['status'] = 'paused'
        telegram_sender.save_bots_config(config)
        
        return jsonify({'success': True, 'message': 'تم إيقاف البوت مؤقتاً'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/<int:bot_id>/activate', methods=['POST'])
@admin_required
def activate_bot(bot_id):
    """تنشيط بوت"""
    try:
        config = telegram_sender.load_bots_config()
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        
        if not bot:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
        
        bot['status'] = 'active'
        telegram_sender.save_bots_config(config)
        
        return jsonify({'success': True, 'message': 'تم تنشيط البوت'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/<int:bot_id>/delete', methods=['POST'])
@admin_required
def delete_bot(bot_id):
    """حذف بوت (soft delete)"""
    try:
        config = telegram_sender.load_bots_config()
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        
        if not bot:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
        
        # حماية: لا يمكن حذف البوت الافتراضي
        if bot.get('is_default'):
            return jsonify({'success': False, 'message': 'لا يمكن حذف البوت الافتراضي'})
        
        bot['status'] = 'deleted'
        telegram_sender.save_bots_config(config)
        
        return jsonify({'success': True, 'message': 'تم حذف البوت'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/<int:bot_id>/restore', methods=['POST'])
@admin_required
def restore_bot(bot_id):
    """استعادة بوت محذوف"""
    try:
        config = telegram_sender.load_bots_config()
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        
        if not bot:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
        
        bot['status'] = 'active'
        telegram_sender.save_bots_config(config)
        
        return jsonify({'success': True, 'message': 'تم استعادة البوت'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/<int:bot_id>/set-default', methods=['POST'])
@admin_required
def set_default_bot(bot_id):
    """تعيين بوت افتراضي"""
    try:
        config = telegram_sender.load_bots_config()
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        
        if not bot:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
        
        if bot['status'] != 'active':
            return jsonify({'success': False, 'message': 'يجب أن يكون البوت نشطاً'})
        
        # إلغاء الافتراضي من الكل
        for b in config.get('bots', []):
            b['is_default'] = False
        
        # تعيين هذا البوت كافتراضي
        bot['is_default'] = True
        telegram_sender.save_bots_config(config)
        
        return jsonify({'success': True, 'message': 'تم تعيين البوت كافتراضي'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/admin/bots/<int:bot_id>/test-send', methods=['POST'])
@admin_required
def test_send_bot(bot_id):
    """اختبار إرسال رسالة عبر بوت"""
    try:
        config = telegram_sender.load_bots_config()
        bot = next((b for b in config.get('bots', []) if b['id'] == bot_id), None)
        
        if not bot:
            return jsonify({'success': False, 'message': 'البوت غير موجود'})
        
        # إرسال رسالة اختبار
        test_message = f"""
🧪 <b>رسالة اختبار - Test Message</b>

✅ البوت يعمل بنجاح!
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 Bot: {bot['name']}
"""
        
        # استخدام التوكن الخاص بهذا البوت
        result = telegram_sender.send_telegram_message(
            CHAT_ID,
            test_message,
            bot_token=bot['token']
        )
        
        if result:
            return jsonify({'success': True, 'message': 'تم إرسال رسالة اختبار بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'فشل إرسال الرسالة'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    # ...existing code...
        
        # حفظ في ملف JSON
        recommendations_file = 'recommendations_history.json'
        recommendations = []
        
        if os.path.exists(recommendations_file):
            with open(recommendations_file, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)
        
        recommendations.insert(0, recommendation)
        recommendations = recommendations[:100]  # حفظ آخر 100 توصية
        
        with open(recommendations_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=4, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': 'تم النشر على صفحة التوصيات بنجاح'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/export-trading-signal', methods=['POST'])
@admin_required
def export_trading_signal():
    """تصدير إشارة التداول من المحلل المتقدم"""
    try:
        data = request.json or {}
        symbol = (data.get('symbol') or '').strip()
        interval = data.get('interval', '1h')

        if not symbol:
            return jsonify({'success': False, 'error': 'الزوج مطلوب'}), 400

        export_payload = {
            'symbol': symbol,
            'interval': interval,
            'trade_type': data.get('trade_type', 'NEUTRAL'),
            'entry_price': data.get('entry_price'),
            'take_profit': data.get('take_profit', []),
            'stop_loss': data.get('stop_loss'),
            'confidence': data.get('confidence', ''),
            'recommendation': data.get('recommendation', ''),
            'exported_at': datetime.now().isoformat(),
            'source': 'advanced_analyzer'
        }

        ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"analysis_signal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = ANALYSIS_DIR / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_payload, f, ensure_ascii=False, indent=2)

        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publish-to-recommendations', methods=['POST'])
@admin_required
def publish_to_recommendations():
    """نشر توصية من المحلل المتقدم إلى ملفات التوصيات"""
    try:
        data = request.json or {}
        symbol = (data.get('symbol') or '').strip()

        if not symbol:
            return jsonify({'success': False, 'error': 'الزوج مطلوب'}), 400

        recommendation_text = data.get('recommendation', 'NEUTRAL')
        recommendation = {
            'pair': symbol,
            'symbol': symbol,
            'signal': recommendation_text,
            'rec': recommendation_text,
            'entry': data.get('entry_point'),
            'entry_price': data.get('entry_point'),
            'tp1': data.get('tp1'),
            'tp2': data.get('tp2'),
            'tp3': data.get('tp3'),
            'sl': data.get('stop_loss'),
            'stop_loss': data.get('stop_loss'),
            'timeframe': data.get('interval', '1h'),
            'analysis_text': data.get('analysis_text', ''),
            'confidence': data.get('confidence', ''),
            'quality_score': 90,
            'timestamp': datetime.now().isoformat(),
            'source': 'advanced_analyzer'
        }

        RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)
        rec_file = RECOMMENDATIONS_DIR / f"recommendations_{datetime.now().strftime('%Y%m%d')}.json"

        recommendations = []
        if rec_file.exists():
            try:
                with open(rec_file, 'r', encoding='utf-8') as f:
                    recommendations = json.load(f) or []
            except Exception:
                recommendations = []

        recommendations.insert(0, recommendation)
        recommendations = recommendations[:200]

        with open(rec_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)

        return jsonify({'success': True, 'message': 'تم النشر على صفحة التوصيات بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/send-to-telegram', methods=['POST'])
@admin_required
def send_analysis_to_telegram():
    """إرسال التحليل للبوت"""
    try:
        data = request.json or {}
        symbol = data.get('symbol')
        recommendation = data.get('recommendation')
        entry = data.get('entry_point')
        tp1 = data.get('tp1')
        tp2 = data.get('tp2')
        tp3 = data.get('tp3')
        sl = data.get('stop_loss')
        confidence = data.get('confidence', '')
        interval = data.get('interval', '1h')

        def _fmt_price(value):
            try:
                return f"{float(value):.5f}"
            except Exception:
                return 'N/A'
        
        # تنسيق الرسالة
        message = f"""
🔔 <b>تحليل جديد - MONEY MAKER</b> 🔔

📊 <b>الزوج:</b> {symbol}
⏱ <b>الإطار الزمني:</b> {interval}

{confidence}
✅ <b>التوصية:</b> {recommendation}

💰 <b>السعر الحالي:</b> {_fmt_price(entry)}

🎯 <b>أهداف الربح:</b>
    • TP1: {_fmt_price(tp1)}
    • TP2: {_fmt_price(tp2)}
    • TP3: {_fmt_price(tp3)}

🛑 <b>وقف الخسارة:</b> {_fmt_price(sl)}

⏰ <b>التاريخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

#فوركس #توصيات #تحليل_فني
"""
        
        # إرسال للتليجرام
        result = telegram_sender.send_telegram_message(
            os.environ.get("MM_TELEGRAM_CHAT_ID", ""),
            message
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': 'تم إرسال التحليل للتليجرام بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'فشل إرسال الرسالة'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============== End Advanced Forex Analyzer Routes ==============

# ============== Master Dashboard Routes ==============

@app.route('/master-dashboard')
@login_required
def master_dashboard():
    """عرض لوحة التحكم المركزية"""
    return render_template('master_dashboard.html')

@app.route('/api/system-status')
def api_system_status():
    """الحصول على حالة النظام"""
    try:
        # قراءة حالة النظام من ملف
        status_file = Path(__file__).parent / 'system_status.json'
        
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                system_data = json.load(f)
        else:
            system_data = {
                'status': {
                    'web_app': 'running',
                    'vip_bot': 'unknown',
                    'signal_broadcaster': 'unknown',
                    'scheduler': 'unknown',
                    'continuous_analyzer': 'unknown'
                }
            }

        system_data.setdefault('status', {})
        # تحديث حالة التطبيق والخدمات ديناميكياً (بدلاً من الاعتماد على ملف قديم)
        system_data['status']['web_app'] = 'running'
        analyzer_running_flag = bool(CONTINUOUS_ANALYZER_STATE.get('running'))
        analyzer_alive = _is_continuous_analyzer_alive()
        if analyzer_running_flag and not analyzer_alive:
            # self-heal إذا كان العلم running لكن الثريد مات
            try:
                start_continuous_analyzer(interval_seconds=CONTINUOUS_ANALYZER_STATE.get('interval_seconds', CONTINUOUS_ANALYZER_INTERVAL_DEFAULT))
                analyzer_alive = _is_continuous_analyzer_alive()
            except Exception:
                analyzer_alive = False
        system_data['status']['continuous_analyzer'] = 'running' if analyzer_running_flag and analyzer_alive else 'stopped'
        system_data['status']['delivery_report_scheduler'] = 'running' if DELIVERY_REPORT_SCHEDULER_STATE.get('running') else 'stopped'
        system_data['status']['scheduler'] = system_data['status']['delivery_report_scheduler']

        bots = []
        active_bots = []

        # تحديد حالة vip_bot من إعدادات البوت الفعلية
        try:
            bots_config = telegram_sender.load_bots_config()
            bots = bots_config.get('bots', []) if isinstance(bots_config, dict) else []
            active_bots = [
                bot for bot in bots
                if isinstance(bot, dict) and bot.get('status') == 'active' and str(bot.get('token', '')).strip()
            ]
            if active_bots:
                system_data['status']['vip_bot'] = 'running'
            elif bots:
                system_data['status']['vip_bot'] = 'stopped'
            else:
                system_data['status']['vip_bot'] = 'unknown'
        except Exception:
            system_data['status']['vip_bot'] = 'stopped'

        # تحديد حالة نظام البث بشكل ديناميكي (بدلاً من الاعتماد على system_status.json)
        try:
            targets_config = telegram_sender.load_broadcast_targets()
            targets = targets_config.get('targets', []) if isinstance(targets_config, dict) else []

            enabled_targets = [t for t in targets if isinstance(t, dict) and t.get('enabled', True)]
            valid_telegram_targets = [
                t for t in enabled_targets
                if str(t.get('platform') or t.get('type') or '').strip().lower() in ('telegram', 'telegram_channel', 'telegram_group')
                and str(t.get('chat_id') or t.get('telegram_chat_id') or '').strip()
            ]
            valid_whatsapp_targets = [
                t for t in enabled_targets
                if str(t.get('platform') or t.get('type') or '').strip().lower() in ('whatsapp', 'whatsapp_group')
                and str(t.get('webhook_url') or t.get('url') or '').strip()
            ]

            # وجود قناة إرسال (توكنات متاحة)
            available_tokens = []
            try:
                token_loader = getattr(telegram_sender, '_get_active_bot_tokens', None)
                if callable(token_loader):
                    available_tokens = token_loader() or []
            except Exception:
                available_tokens = []

            # وجود مستقبلين فعليين من المشتركين (chat_id/telegram_id)
            has_subscriber_receivers = False
            try:
                subscribers = subscription_manager.get_all_active_users() or []
                has_subscriber_receivers = any(
                    (str((u.get('chat_id') if isinstance(u, dict) else '') or '').strip())
                    or (u.get('telegram_id') if isinstance(u, dict) else None)
                    for u in subscribers
                )
            except Exception:
                has_subscriber_receivers = False

            # fallback عام للبث الخارجي
            env_fallback_ready = bool(str(os.environ.get('MM_TELEGRAM_CHAT_ID', '') or '').strip())

            broadcaster_ready = bool(available_tokens) and (
                has_subscriber_receivers
                or bool(valid_telegram_targets)
                or bool(valid_whatsapp_targets)
                or env_fallback_ready
            )

            if broadcaster_ready:
                system_data['status']['signal_broadcaster'] = 'running'
            elif targets or bots:
                system_data['status']['signal_broadcaster'] = 'stopped'
            else:
                system_data['status']['signal_broadcaster'] = 'stopped'
        except Exception:
            system_data['status']['signal_broadcaster'] = 'stopped'
        
        # حساب المقاييس
        # إجمالي المستخدمين
        all_users = subscription_manager.get_all_active_users()
        total_users = len(all_users) if all_users else 0
        
        # الصفقات النشطة
        active_trades_file = Path(__file__).parent / 'active_trades.json'
        active_trades = []
        active_trades_count = 0
        
        if active_trades_file.exists():
            try:
                with open(active_trades_file, 'r', encoding='utf-8') as f:
                    active_trades = json.load(f)
                    if isinstance(active_trades, list):
                        active_trades_count = len([t for t in active_trades if t.get('status') == 'active'])
                    else:
                        active_trades = []
            except:
                pass
        
        # الإشارات المرسلة اليوم
        sent_signals_file = Path(__file__).parent / 'sent_signals.json'
        total_signals_today = 0
        
        if sent_signals_file.exists():
            try:
                with open(sent_signals_file, 'r', encoding='utf-8') as f:
                    sent_signals = json.load(f)
                    today = datetime.now().date()
                    total_signals_today = len([
                        s for s in sent_signals 
                        if 'sent_at' in s and datetime.fromisoformat(s['sent_at']).date() == today
                    ])
            except:
                pass
        
        # معدل النجاح من قاعدة البيانات
        try:
            from trade_statistics import TradeStatistics  # type: ignore
            stats_engine = TradeStatistics()
            stats = stats_engine.get_statistics(days=30)
            win_rate = stats.get('win_rate', 0)
        except:
            win_rate = 0
        
        adaptive_overview = _build_adaptive_thresholds_overview(limit_rows=20)
        archive_stats = _build_archive_stats()

        return jsonify({
            'success': True,
            'status': system_data.get('status', {}),
            'metrics': {
                'total_users': total_users,
                'total_signals': total_signals_today,
                'active_trades': active_trades_count,
                'win_rate': win_rate
            },
            'archive_stats': archive_stats,
            'adaptive_overview': adaptive_overview.get('summary', {}),
            'continuous_analyzer': CONTINUOUS_ANALYZER_STATE,
            'continuous_analyzer_thread_alive': analyzer_alive,
            'cleanup_scheduler': CLEANUP_SCHEDULER_STATE,
            'delivery_report_scheduler': DELIVERY_REPORT_SCHEDULER_STATE,
            'active_trades': active_trades[:10],  # آخر 10 صفقات
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/recent-analysis')
def api_recent_analysis():
    """الحصول على آخر التحليلات"""
    try:
        signals_dir = SIGNALS_DIR
        
        if not signals_dir.exists():
            return jsonify({'success': True, 'analysis': []})
        
        all_signals = []
        
        # قراءة جميع ملفات الإشارات
        for signal_file in signals_dir.glob('*.json'):
            try:
                with open(signal_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if isinstance(data, list):
                        all_signals.extend(data)
                    else:
                        all_signals.append(data)
            except:
                continue
        
        # ترتيب حسب الوقت (الأحدث أولاً)
        all_signals.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        user_info = get_current_user()
        if user_info.get('success'):
            selected_pairs = set(_load_user_selected_pairs(user_info.get('user_id')))
            if selected_pairs:
                all_signals = [
                    s for s in all_signals
                    if _normalize_symbol_key(
                        s.get('symbol') or s.get('pair') or s.get('instrument') or s.get('ticker')
                    ) in selected_pairs
                ]

        # أخذ آخر 20 إشارة
        recent_signals = all_signals[:20]
        
        return jsonify({
            'success': True,
            'analysis': recent_signals
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/start-component', methods=['POST'])
@login_required
def api_start_component():
    """تشغيل مكون معين"""
    try:
        data = request.get_json()
        component = data.get('component')
        
        if component in ('continuous_analyzer', 'continuous-analysis', 'analyzer'):
            interval_seconds = int(data.get('interval_seconds', CONTINUOUS_ANALYZER_INTERVAL_DEFAULT))
            success, message = start_continuous_analyzer(interval_seconds=interval_seconds)
            return jsonify({
                'success': success,
                'message': message,
                'state': CONTINUOUS_ANALYZER_STATE
            })

        if component in ('delivery_report_scheduler', 'delivery-reports', 'delivery_csv_scheduler'):
            daily_time = data.get('daily_time', DELIVERY_REPORT_DAILY_TIME)
            check_interval_seconds = int(data.get('check_interval_seconds', DELIVERY_REPORT_CHECK_INTERVAL_SECONDS))
            success, message = start_delivery_report_scheduler(
                daily_time=daily_time,
                check_interval_seconds=check_interval_seconds
            )
            return jsonify({
                'success': success,
                'message': message,
                'state': DELIVERY_REPORT_SCHEDULER_STATE
            })

        if component in ('generate_delivery_csv_now', 'delivery_csv_now'):
            try:
                _generate_delivery_csv_now()
                return jsonify({
                    'success': True,
                    'message': 'تم توليد تقرير CSV اليومي الآن',
                    'state': DELIVERY_REPORT_SCHEDULER_STATE
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        return jsonify({
            'success': True,
            'message': f'تم تشغيل {component} بنجاح'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stop-component', methods=['POST'])
@login_required
def api_stop_component():
    """إيقاف مكون معين"""
    try:
        data = request.get_json()
        component = data.get('component')
        
        if component in ('continuous_analyzer', 'continuous-analysis', 'analyzer'):
            success, message = stop_continuous_analyzer()
            return jsonify({
                'success': success,
                'message': message,
                'state': CONTINUOUS_ANALYZER_STATE
            })

        if component in ('delivery_report_scheduler', 'delivery-reports', 'delivery_csv_scheduler'):
            success, message = stop_delivery_report_scheduler()
            return jsonify({
                'success': success,
                'message': message,
                'state': DELIVERY_REPORT_SCHEDULER_STATE
            })
        
        return jsonify({
            'success': True,
            'message': f'تم إيقاف {component} بنجاح'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ============== End Master Dashboard Routes ==============

# ============== API للتحديث التلقائي ==============

@app.route('/api/update_prices')
def api_update_prices():
    """API لتحديث الأسعار الحالية فقط"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('vip_signals.db', timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('PRAGMA busy_timeout = 30000')
        
        start_date = (datetime.now() - timedelta(days=SIGNALS_LOOKBACK_DAYS)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT signal_id, symbol, signal_type, entry_price, stop_loss, 
                   take_profit_1, take_profit_2, take_profit_3, status
            FROM signals 
            WHERE DATE(created_at) >= ? AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 200
        ''', (start_date,))
        
        rows = c.fetchall()
        signals_data = []
        
        for row in rows:
            symbol = row['symbol']
            signal_type = _normalize_signal_type(row['signal_type'])
            entry = row['entry_price']
            tp1 = row['take_profit_1']
            
            # استخدام الدالة المحسنة مع وقت آخر تحديث
            price_details = get_live_price_detailed(symbol)
            current_price = price_details.get('price') if isinstance(price_details, dict) else None
            current_price_updated_at = price_details.get('updated_at') if isinstance(price_details, dict) else None
            
            if current_price:
                try:
                    # حساب النقاط
                    if signal_type == 'buy':
                        pips = current_price - entry
                        total_range = tp1 - entry
                    else:
                        pips = entry - current_price
                        total_range = entry - tp1
                    
                    # حساب نسبة التقدم
                    progress = int((pips / total_range) * 100) if total_range != 0 else 0
                    
                    signals_data.append({
                        'id': row['signal_id'],
                        'signal_id': row['signal_id'],
                        'current_price': current_price,
                        'current_price_updated_at': current_price_updated_at,
                        'pips': round(pips, 2),
                        'progress': max(0, progress)
                    })
                except Exception as e:
                    print(f"Error fetching price for {symbol}: {e}")
                    continue
        
        conn.close()

        UPDATE_PRICES_LAST_PAYLOAD['signals'] = signals_data
        UPDATE_PRICES_LAST_PAYLOAD['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'success': True,
            'signals': signals_data,
            'cached_fallback': False,
            'updated_at': UPDATE_PRICES_LAST_PAYLOAD.get('updated_at')
        })
        
    except Exception as e:
        error_text = str(e)
        fallback_signals = UPDATE_PRICES_LAST_PAYLOAD.get('signals', []) or []

        if not fallback_signals:
            try:
                for signal in load_signals(include_closed=False):
                    if str(signal.get('status', '')).lower() != 'active':
                        continue
                    fallback_signals.append({
                        'id': signal.get('signal_id'),
                        'signal_id': signal.get('signal_id'),
                        'current_price': signal.get('current_price'),
                        'current_price_updated_at': signal.get('current_price_updated_at'),
                        'pips': signal.get('pips'),
                        'progress': signal.get('progress')
                    })
            except Exception:
                pass

        return jsonify({
            'success': True,
            'signals': fallback_signals,
            'cached_fallback': True,
            'updated_at': UPDATE_PRICES_LAST_PAYLOAD.get('updated_at'),
            'warning': error_text
        })


@app.route('/api/update_status')
def api_update_status():
    """API للتحقق من تغيير الحالات"""
    try:
        refresh_stats = _refresh_active_signal_statuses()

        cleaned_count = archive_and_cleanup_closed_signals()
        
        return jsonify({
            'success': True,
            'needs_refresh': bool(refresh_stats.get('changed')),
            'cleaned_closed_trades': cleaned_count,
            'refreshed_active_signals': refresh_stats.get('processed', 0),
            'updated_active_signals': refresh_stats.get('changed', 0)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ============== نهاية API للتحديث التلقائي ==============


def _auto_start_background_services_for_wsgi():
    """تشغيل خدمات الخلفية تلقائياً عند الاستيراد عبر WSGI (مثل Render/Gunicorn)."""
    if __name__ == '__main__':
        return
    if not BACKGROUND_SERVICES_ENABLED:
        return
    _schedule_background_services_bootstrap()


_auto_start_background_services_for_wsgi()

if __name__ == '__main__':
    debug_mode = os.environ.get('APP_DEBUG', '0').strip().lower() in ('1', 'true', 'yes', 'on')
    banner = "=" * 60
    print(banner)
    print("VIP Signals Web Server - Login System")
    print(banner)
    print("Open your browser:")
    print("  http://localhost:5000")
    print("Register page:")
    print("  http://localhost:5000/register")
    print(banner)

    should_start_background = (os.environ.get('WERKZEUG_RUN_MAIN') == 'true') or (not debug_mode)
    if should_start_background:
        started, msg = start_continuous_analyzer(interval_seconds=CONTINUOUS_ANALYZER_INTERVAL_DEFAULT)
        print(f"[CONTINUOUS_ANALYZER] {msg}")
        cleanup_started, cleanup_msg = start_cleanup_scheduler(interval_seconds=CLEANUP_INTERVAL_DEFAULT)
        print(f"[CLEANUP_SCHEDULER] {cleanup_msg}")
        cmd_started, cmd_msg = start_telegram_command_bot()
        print(f"[TELEGRAM_COMMAND_BOT] {cmd_msg}")

    app.run(debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=debug_mode)







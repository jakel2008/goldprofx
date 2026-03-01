# GOLD PRO Web Application
# تطبيق ويب متكامل لنظام التداول متعدد الخطط

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask import send_from_directory, abort
from functools import wraps
import json
import os
import sqlite3
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from pathlib import Path

if os.name == "nt":
    os.system("chcp 65001 > nul")

# شغّل الهجرات عند الإقلاع (Idempotent)
try:
    from db_migrate import migrate_all
    migrate_all()
except Exception:
    pass

# المصدر الوحيد للخطط
try:
    from vip_subscription_system import PLANS
except Exception:
    PLANS = {}

PAYMENTS_DIR = Path(__file__).parent / "payment_proofs"
ALLOWED_PROOF_EXT = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}

def _hash_password(p: str) -> str:
    return hashlib.sha256((p or "").encode("utf-8")).hexdigest()

def _get_plan_meta(plan_name: str) -> dict:
    return PLANS.get(plan_name, {}) if isinstance(PLANS, dict) else {}

def plan_duration_days(plan_name: str) -> int:
    m = _get_plan_meta(plan_name)
    return int(m.get("duration_days", m.get("duration", 0)) or 0)

def plan_signal_limit(plan_name: str) -> int:
    m = _get_plan_meta(plan_name)
    return int(m.get("signals_per_day", m.get("signal_limit", 0)) or 0)

def save_payment_proof(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    suffix = Path(file_storage.filename).suffix.lower()
    if suffix not in ALLOWED_PROOF_EXT:
        return None
    PAYMENTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"proof_{secrets.token_hex(8)}{suffix}"
    file_storage.save(str(PAYMENTS_DIR / filename))
    return filename  # نخزن الاسم فقط

# إعداد التطبيق
DB_PATH = os.getenv('DB_PATH', 'goldpro_system.db')
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'gold-pro-vip-signals-2026-secure-key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

SIGNALS_DIR = Path(__file__).parent / "signals"
RECOMMENDATIONS_DIR = Path(__file__).parent / "recommendations"
ACTIVE_TRADES_FILE = Path(__file__).parent / "active_trades.json"
CLOSED_TRADES_FILE = Path(__file__).parent / "closed_trades.json"

# دوال مساعدة للتعامل مع قاعدة البياناتاعدة للتعامل مع قاعدة البيانات
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['GET', 'POST'])

def init_db():
    """إنشاء جداول قاعدة البيانات الأساسية وإضافة الخطط الافتراضية."""
    conn = get_db()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        price REAL DEFAULT 0,
        features TEXT,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        plan_id INTEGER,
        is_active INTEGER DEFAULT 0,
        activation_code TEXT,
        join_date TEXT,
        last_login TEXT,
        is_admin INTEGER DEFAULT 0,
        FOREIGN KEY(plan_id) REFERENCES plans(id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        symbol TEXT NOT NULL,
        entry REAL,
        sl REAL,
        tp1 REAL,
        tp2 REAL,
        tp3 REAL,
        quality_score INTEGER,
        status TEXT DEFAULT 'pending',
        plan_id INTEGER,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(plan_id) REFERENCES plans(id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS trade_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER,
        user_id INTEGER,
        status TEXT,
        profit_loss REAL,
        updated_at TEXT,
        FOREIGN KEY(trade_id) REFERENCES trades(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS upgrades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        from_plan_id INTEGER,
        to_plan_id INTEGER,
        request_date TEXT,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(from_plan_id) REFERENCES plans(id),
        FOREIGN KEY(to_plan_id) REFERENCES plans(id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS support (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        message TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        created_at TEXT,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS plan_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER,
        feature TEXT,
        is_enabled INTEGER DEFAULT 1,
        FOREIGN KEY(plan_id) REFERENCES plans(id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        source TEXT,
        price REAL,
        fetched_at TEXT
    )''')

    c.execute('SELECT COUNT(*) AS total FROM plans')
    row = c.fetchone()
    total_plans = row['total'] if row else 0

    if not total_plans:
        default_plans = [
            ('free', 'الخطة المجانية', 0, 'إشارات محدودة يومياً'),
            ('bronze', 'خطة برونزية', 29, 'إشارات إضافية + دعم أساسي'),
            ('silver', 'خطة فضية', 69, 'إشارات أكثر + توصيات متقدمة'),
            ('gold', 'خطة ذهبية', 199, 'إشارات قوية + تقارير احترافية'),
            ('platinum', 'خطة بلاتينية', 499, 'كل الميزات + دعم VIP')
        ]
        c.executemany(
            'INSERT INTO plans (name, description, price, features, is_active) VALUES (?, ?, ?, ?, 1)',
            default_plans
        )

    c.execute('''
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token TEXT UNIQUE NOT NULL,
        expires_at TEXT,
        used INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()


def ensure_user_schema():
    """تأكد من وجود عمود صلاحيات الأدمن في قاعدة البيانات."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
        conn.commit()
    except Exception:
        pass
    conn.close()


# تهيئة قاعدة البيانات عند الاستيراد (لبيئات الإنتاج مثل Render) - آمن مع معالجة الأخطاءلأخطاء
try:
    init_db()
except Exception as e:
    print(f"Warning: Database initialization failed (will retry on first request): {e}")

def get_user_by_email(email):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_plan_by_id(plan_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM plans WHERE id = ?', (plan_id,))
    plan = c.fetchone()
    conn.close()
    return plan

def get_all_plans():
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM plans WHERE is_active = 1')
    except sqlite3.OperationalError as e:
        if 'no such column: is_active' in str(e).lower():
            c.execute('SELECT * FROM plans')
        else:
            conn.close()
            raise
    plans = c.fetchall()
    conn.close()
    return plans

def create_user(full_name, email, password_hash, activation_code, is_active=0):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO users (full_name, email, password_hash, plan_id, is_active, activation_code, join_date)
           VALUES (?, ?, ?, 1, ?, ?, ?)''',
        (full_name, email, password_hash, is_active, activation_code, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def check_password(user, password_hash):
    return user and user['password_hash'] == password_hash

# Decorators for access control
def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return render_template('403.html'), 403
        return f(*args, **kwargs)
    return decorated

def require_plan(*plans):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('plan') not in plans and session.get('role') != 'admin':
                return render_template('403.html'), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _calc_rr(entry, sl, tp1):
    try:
        risk = abs(entry - sl)
        reward = abs(tp1 - entry)
        if risk <= 0 or reward <= 0:
            return 0.00
        return reward / risk
    except Exception:
        return 0.0


def _parse_timestamp(ts):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def load_signals_from_files():
    """تحميل الإشارات من ملفات JSON في مجلد signals وتوحيد الحقول."""
    signals = []
    if not SIGNALS_DIR.exists():
        return signals

    for signal_file in sorted(SIGNALS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(signal_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue

        if isinstance(data, dict):
            data = [data]

        for raw in data:
            if not isinstance(raw, dict):
                continue

            symbol = raw.get('symbol') or raw.get('pair') or 'UNKNOWN'
            signal_type = (raw.get('signal_type') or raw.get('trade_type') or raw.get('signal') or 'buy').lower()
            if signal_type not in ('buy', 'sell'):
                signal_type = 'buy'

            entry_price = _safe_float(raw.get('entry_price', raw.get('entry', 0)))
            stop_loss = _safe_float(raw.get('stop_loss', raw.get('sl', 0)))
            take_profit_1 = _safe_float(raw.get('take_profit_1', raw.get('tp1', 0)))
            take_profit_2 = _safe_float(raw.get('take_profit_2', raw.get('tp2', 0)))
            take_profit_3 = _safe_float(raw.get('take_profit_3', raw.get('tp3', 0)))

            timestamp = raw.get('timestamp') or raw.get('created_at') or datetime.now().isoformat()
            quality_score = int(raw.get('quality_score') or raw.get('quality') or 0)
            status = raw.get('status') or 'pending'

            signal_id = raw.get('signal_id') or f"{symbol}_{entry_price}_{timestamp}"

            signals.append({
                'signal_id': signal_id,
                'symbol': symbol,
                'signal_type': signal_type,
                'status': status,
                'result': raw.get('result'),
                'timestamp': timestamp,
                'quality_score': quality_score,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit_1': take_profit_1 or None,
                'take_profit_2': take_profit_2 or None,
                'take_profit_3': take_profit_3 or None,
                'tp1_locked': bool(raw.get('tp1_locked')),
                'tp2_locked': bool(raw.get('tp2_locked')),
                'tp3_locked': bool(raw.get('tp3_locked')),
                'current_price': _safe_float(raw.get('current_price', 0)),
                'pips': _safe_float(raw.get('pips', 0)),
                'progress': int(raw.get('progress', 0)),
                'close_price': _safe_float(raw.get('close_price', 0)) if raw.get('close_price') else None,
                'rr': _calc_rr(entry_price, stop_loss, take_profit_1)
            })

    return signals


def load_best_signals():
    """فلترة أفضل الإشارات (جودة عالية + عائد/مخاطرة مناسب + حديثة)."""
    min_quality = 70
    min_rr = 1.2
    max_age_hours = 72
    limit = 30

    signals = load_signals_from_files()
    now = datetime.now()

    filtered = []
    for s in signals:
        quality = s.get('quality_score') or 0
        rr = s.get('rr') or 0
        ts = _parse_timestamp(s.get('timestamp', ''))
        if ts is None:
            continue
        age_hours = (now - ts).total_seconds() / 3600.0
        if quality < min_quality or rr < min_rr or age_hours > max_age_hours:
            continue
        filtered.append(s)

    filtered.sort(key=lambda x: (x.get('quality_score', 0), x.get('rr', 0), x.get('timestamp', '')), reverse=True)
    return filtered[:limit]


def load_recommendations_from_files():
    """تحميل التوصيات من ملفات JSON في مجلد recommendations."""
    recommendations = []
    if not RECOMMENDATIONS_DIR.exists():
        return recommendations

    for rec_file in sorted(RECOMMENDATIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(rec_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue

        if isinstance(data, dict):
            data = [data]

        for raw in data:
            if not isinstance(raw, dict):
                continue
            recommendations.append(raw)

    return recommendations


def save_json(path: Path, payload):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# المسارات الرئيسية
@app.route('/')
def index():
    """الصفحة الرئيسية"""
    plans = get_all_plans()
    return render_template('landing.html', plans=plans)

@app.route('/activate/<token>')
def activate(token):
    """تفعيل الحساب عبر البريد"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, is_active FROM users WHERE activation_code = ?', (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        return render_template('login.html', error='رمز التفعيل غير صالح أو منتهي.')
    user_id, is_active = row['id'], row['is_active']
    if is_active:
        conn.close()
        return render_template('login.html', error='الحساب مفعل بالفعل. يمكنك تسجيل الدخول.')
    c.execute('UPDATE users SET is_active = 1, activation_code = NULL WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return render_template('login.html', error='تم تفعيل الحساب بنجاح! يمكنك الآن تسجيل الدخول.')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        print(f"[LOGIN] Email: {email}, Password length: {len(password)}")

        if not email or not password:
            return render_template('login.html', error='يرجى إدخال البريد والكلمة المرور')

        user = get_user_by_email(email)
        print(f"[LOGIN] User found: {user is not None}")

        if user:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            print(f"[LOGIN] Password check: {check_password(user, password_hash)}")

            if check_password(user, password_hash):
                admin_emails = {
                    e.strip().lower()
                    for e in os.environ.get('ADMIN_EMAILS', '').split(',')
                    if e.strip()
                }
                if email.lower() in admin_emails:
                    try:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute('UPDATE users SET is_admin = 1, is_active = 1 WHERE email = ?', (email,))
                        conn.commit()
                        conn.close()
                        user = get_user_by_email(email)
                    except Exception:
                        pass
                if not user['is_active']:
                    return render_template('login.html', error='يجب تفعيل الحساب عبر البريد الإلكتروني أولاً.')
                # جلب خطة المستخدم
                plan_id = user['plan_id']
                plan_row = get_plan_by_id(plan_id)
                plan = plan_row['name'] if plan_row else 'free'
                # تحديد الدور
                is_admin = False
                try:
                    is_admin = bool(user['is_admin'])
                except Exception:
                    is_admin = False
                role = 'admin' if user['id'] == 1 or is_admin else 'user'
                session['user_id'] = user['id']
                session['full_name'] = user['full_name']
                session['plan'] = plan
                session['role'] = role
                session.permanent = True
                print(f"[LOGIN] Login successful! Redirecting to dashboard")
                return redirect(url_for('dashboard'))

        print(f"[LOGIN] Login failed")
        return render_template('login.html', error='بيانات الدخول غير صحيحة أو المستخدم غير موجود')
    return render_template('login.html')

 
@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة التسجيل"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        if get_user_by_email(email):
            return render_template('register.html', error='البريد الإلكتروني مستخدم بالفعل.')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        smtp_ready = all([smtp_server, smtp_user, smtp_pass]) and smtp_server != 'smtp.example.com'
        auto_activate = os.environ.get('AUTO_ACTIVATE', '1') == '1'

        if auto_activate or not smtp_ready:
            create_user(full_name, email, password_hash, activation_code=None, is_active=1)
            return render_template('register.html', success='تم إنشاء الحساب ويمكنك تسجيل الدخول الآن.')

        activation_code = secrets.token_urlsafe(32)
        create_user(full_name, email, password_hash, activation_code, is_active=0)
        # إرسال بريد التفعيل
        try:
            activation_link = url_for('activate', token=activation_code, _external=True)
            msg = MIMEText(f"مرحباً {full_name},\n\nيرجى تفعيل حسابك عبر الرابط التالي:\n{activation_link}\n\nشكراً!", 'plain', 'utf-8')
            msg['Subject'] = 'تفعيل حسابك في GOLD PRO'
            msg['From'] = 'noreply@goldpro.com'
            msg['To'] = email
            # محاولة إرسال البريد (قد تفشل إذا لم تكن الإعدادات صحيحة)
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(msg['From'], [msg['To']], msg.as_string())
            except Exception:
                pass  # تجاهل أخطاء SMTP
            return render_template('register.html', success='تم إنشاء الحساب. تحقق من بريدك الإلكتروني لتفعيل الحساب.')
        except Exception:
            return render_template('register.html', error='حدث خطأ أثناء التسجيل.')
    return render_template('register.html')

@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/plans')
def plans():
    """صفحة الخطط"""
    plans = get_all_plans()
    return render_template('plans.html', plans=plans)

@app.route('/dashboard')
@require_login

def dashboard():
    """
    لوحة التحكم
    """
    # حساب عدد الأزواج المختارة للمستخدم الحالي
    selected_pairs_count = 0
    try:
        user_id = session.get('user_id')
        if user_id:
            # مثال: إذا كان لديك جدول أو قائمة للأزواج المختارة
            # selected_pairs_count = get_selected_pairs_count(user_id)
            pass
    except Exception:
        selected_pairs_count = 0
    return render_template('dashboard.html', selected_pairs_count=selected_pairs_count)

@app.route('/index_new')
def index_new():
    """واجهة الصفحة الجديدة"""
    return render_template('index_new.html')

@app.route('/admin')
@require_login
@require_admin
def admin_panel():
    """لوحة الإدارة"""
    user = {
        'username': session.get('full_name') or session.get('email') or 'Admin'
    }
    return render_template('admin.html', user=user)


@app.route('/api/admin/users')
@require_login
@require_admin
def api_admin_users():
    """عرض الحسابات الفعّالة فقط في لوحة الإدارة."""
    ensure_user_schema()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, email, full_name, plan_id, is_active, last_login, is_admin FROM users')
    rows = c.fetchall()
    conn.close()

    users = []
    for row in rows:
        plan_row = get_plan_by_id(row['plan_id'])
        plan_name = plan_row['name'] if plan_row else 'free'
        email = row['email'] or ''
        username = email.split('@')[0] if '@' in email else (row['full_name'] or f"user{row['id']}")
        is_admin = False
        try:
            is_admin = bool(row['is_admin'])
        except Exception:
            is_admin = False
        users.append({
            'id': row['id'],
            'username': username,
            'email': email,
            'full_name': row['full_name'],
            'plan': plan_name,
            'is_active': bool(row['is_active']),
            'is_admin': True if row['id'] == 1 else is_admin,
            'last_login': row['last_login']
        })

    return jsonify({'success': True, 'users': users})


@app.route('/api/admin/set_active', methods=['POST'])
@require_login
@require_admin
def api_admin_set_active():
    data = request.json or {}
    user_id = data.get('user_id')
    is_active = 1 if data.get('is_active') else 0
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id مطلوب'})

    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET is_active = ? WHERE id = ?', (is_active, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/set_admin', methods=['POST'])
@require_login
@require_admin
def api_admin_set_admin():
    """تحكم بسيط بصلاحيات الأدمن (الحساب 1 فقط)."""
    ensure_user_schema()
    data = request.json or {}
    user_id = data.get('user_id')
    is_admin = 1 if data.get('is_admin') else 0
    if not user_id:
        return jsonify({'success': False, 'message': 'user_id مطلوب'})

    if int(user_id) == 1:
        return jsonify({'success': True})

    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin = ? WHERE id = ?', (is_admin, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/admin/update_plan', methods=['POST'])
@require_login
@require_admin
def api_admin_update_plan():
    data = request.json or {}
    user_id = data.get('user_id')
    plan_name = data.get('plan')
    if not user_id or not plan_name:
        return jsonify({'success': False, 'message': 'user_id و plan مطلوبان'})

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM plans WHERE name = ?', (plan_name,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'خطة غير صالحة'})
    plan_id = row['id']
    c.execute('UPDATE users SET plan_id = ? WHERE id = ?', (plan_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/signals')
@require_login
def signals_page():
    """صفحة الإشارات"""
    signals = load_signals_from_files()
    is_admin = session.get('role') == 'admin'
    return render_template('signals_gold_card.html', signals=signals, is_admin=is_admin)


@app.route('/api/update_prices')
def api_update_prices():
    """تحديث الأسعار من السوق وحساب النقاط والتقدم."""""

    signals = load_best_signals()
    updated = []
    for s in signals:
        symbol = s.get('symbol')
        current_price = s.get('current_price')
        if symbol:
            live_price = get_current_price(symbol)
            if live_price:
                current_price = live_price

        entry = s.get('entry_price') or 0
        tp1 = s.get('take_profit_1')
        pips = s.get('pips', 0)
        progress = s.get('progress', 0)

        if current_price and entry:
            if s.get('signal_type') == 'sell':
                pips = entry - current_price
                if tp1 and entry != tp1:
                    progress = int(((entry - current_price) / (entry - tp1)) * 100)
            else:
                pips = current_price - entry
                if tp1 and entry != tp1:
                    progress = int(((current_price - entry) / (tp1 - entry)) * 100)

        updated.append({
            'signal_id': s['signal_id'],
            'current_price': current_price,
            'pips': pips,
            'progress': max(0, min(100, progress))
        })

    return jsonify({'success': True, 'signals': updated})

def get_current_price(symbol):
    """Dummy price fetcher. Replace with real API if needed."""
    # TODO: Integrate with real price provider
    return None



@app.route('/api/update_status')
def api_update_status():
    """واجهة بسيطة لتحديث الحالة."""
    return jsonify({'success': True, 'needs_refresh': False})


@app.route('/api/trades_status')
def api_trades_status():
    """حالة الصفقات للواجهة الأمامية."""
    signals = load_best_signals()
    trades = []

    for s in signals:
        pair = s.get('symbol')
        signal = s.get('signal_type')
        entry = s.get('entry_price')
        sl = s.get('stop_loss')
        tp1 = s.get('take_profit_1') or s.get('take_profit_2') or s.get('take_profit_3')

        if not (pair and signal and entry and sl and tp1):
            continue

        current_price = get_current_price(pair) or s.get('current_price')
        if not current_price:
            continue

        if signal == 'sell':
            profit_percent = round((entry - current_price) / entry * 100, 2)
        else:
            profit_percent = round((current_price - entry) / entry * 100, 2)

        status = 'active'
        if signal == 'buy':
            if current_price <= sl:
                status = 'loss'
            elif current_price >= tp1:
                status = 'win'
        else:
            if current_price >= sl:
                status = 'loss'
            elif current_price <= tp1:
                status = 'win'

    trades.append({
        'pair': pair,
        'signal': signal,
        'entry': entry,
        'current_price': current_price,
        'profit_percent': profit_percent,
        'status': status
    })
    active = [t for t in trades if t['status'] == 'active']
    winners = [t for t in trades if t['status'] == 'win']
    losers = [t for t in trades if t['status'] == 'loss']

    # تنظيف الصفقات المنتهية وتحديث ملفات المتابعة
    active_ids = [s['signal_id'] for s in signals if any(t['pair'] == s.get('symbol') and t['signal'] == s.get('signal_type') for t in active)]
    save_json(ACTIVE_TRADES_FILE, active_ids)
    save_json(CLOSED_TRADES_FILE, {
        'timestamp': datetime.now().isoformat(),
        'winners': winners,
        'losers': losers
    })

    summary = {
        'total_trades': len(trades),
        'active': len(active),
        'winners': len(winners),
        'losers': len(losers),
        'net_profit_percent': round(sum(t['profit_percent'] for t in winners) + sum(t['profit_percent'] for t in losers), 2)
    }

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'summary': summary,
        'active_trades': active,
        'closed_trades': {
            'winners': winners,
            'losers': losers
        }
    })


@app.route('/api/signals')
def api_signals():
    """قائمة إشارات مختصرة للواجهات."""
    signals = load_best_signals()
    return jsonify([
        {
            'symbol': s.get('symbol'),
            'pair': s.get('symbol'),
            'signal': s.get('signal_type', '').upper(),
            'entry': s.get('entry_price'),
            'quality_score': s.get('quality_score'),
            'rr': s.get('rr'),
            'timestamp': s.get('timestamp')
        } for s in signals
    ])


@app.route('/api/recommendations')
def api_recommendations():
    """قائمة التوصيات للواجهة الرئيسية."""
    return jsonify(load_recommendations_from_files())


@app.route('/api/stats')
def api_stats():
    """إحصائيات مختصرة للواجهة الرئيسية."""
    signals = load_signals_from_files()
    recommendations = load_recommendations_from_files()
    return jsonify({
        'signals_count': len(signals),
        'recommendations_count': len(recommendations),
        'analysis_count': 0,
        'subscribers_count': 0
    })

@app.route('/trades')
@require_login
def trades():
    """صفحة الصفقات"""
    return render_template('trades.html')

# معالجات الأخطاء الشاملة
@app.before_request
def before_request():
    """تهيئة قاعدة البيانات عند أول طلب إذا لم تتم التهيئة"""
    try:
        init_db()
    except Exception:
        pass

@app.errorhandler(404)
def not_found(e):
    """صفحة 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """صفحة 500"""
    app.logger.error(f'Internal Server Error: {e}', exc_info=True)
    return render_template('500.html'), 500

if __name__ == '__main__':
    # التأكد من وجود مجلدات الإشارات
    SIGNALS_DIR.mkdir(exist_ok=True)
    RECOMMENDATIONS_DIR.mkdir(exist_ok=True)
    
    # إصلاح مشكلة الترميز على Windows
    if os.sys.platform == 'win32':
        os.system('chcp 65001 > nul')
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║           ⭐ GOLD PRO - نظام التداول المتقدم ⭐            ║
    ║                                                            ║
    ║  ✅ السيرفر يعمل على:                                       ║
    ║     📍 http://localhost:5000                               ║
    ║     📍 http://127.0.0.1:5000                               ║
    ║                                                            ║
    ║  🔑 بيانات اختبار:                                          ║
    ║     📧 البريد: test@goldpro.com                            ║
    ║     🔐 كلمة المرور: Test123                               ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

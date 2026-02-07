# ============ صفحة استرجاع كلمة المرور ============

import secrets
import smtplib
from email.mime.text import MIMEText
import hashlib

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import os
# ============== Bot Management Routes ==============

# Define CHAT_ID for bot test send (replace with your actual chat id)
CHAT_ID = os.environ.get('MM_TELEGRAM_CHAT_ID', '')
from functools import wraps
import json
from datetime import datetime, timedelta
from pathlib import Path
from vip_subscription_system import SubscriptionManager
from user_manager import user_manager
from email_service import email_service
import telegram_sender

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-to-random-string'

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
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
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
subscription_manager = SubscriptionManager()
SIGNALS_DIR = Path(__file__).parent / "signals"
SENT_SIGNALS_FILE = Path(__file__).parent / "sent_signals.json"
RECOMMENDATIONS_DIR = Path(__file__).parent / "recommendations"
ANALYSIS_DIR = Path(__file__).parent / "analysis"
USER_PREFERENCES_FILE = Path(__file__).parent / "user_pairs_preferences.json"

# خريطة رموز Yahoo Finance
YF_SYMBOLS = {
    'XAUUSD': 'GC=F', 'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X', 'AUDUSD': 'AUDUSD=X', 'USDCAD': 'USDCAD=X',
    'NZDUSD': 'NZDUSD=X', 'USDCHF': 'USDCHF=X', 'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD', 'US30': '^DJI', 'NAS100': '^IXIC', 'SPX500': '^GSPC'
}


def get_live_price(symbol):
    """
    الحصول على السعر الحالي للزوج بطرق متعددة
    Get current price with multiple fallback methods
    """
    if symbol not in YF_SYMBOLS:
        return None

    try:
        import yfinance as yf  # heavy; lazy import to keep server startup fast
    except Exception:
        return None
    
    yf_symbol = YF_SYMBOLS[symbol]
    
    # الطريقة 1: من ticker.info
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        price_fields = ['regularMarketPrice', 'currentPrice', 'bid', 'ask', 'previousClose']
        for field in price_fields:
            if field in info and info[field]:
                price = float(info[field])
                if price > 0:
                    return price
    except:
        pass
    
    # الطريقة 2: من البيانات التاريخية
    try:
        ticker = yf.Ticker(yf_symbol)
        periods_intervals = [('1d', '1m'), ('5d', '5m'), ('1mo', '1h')]
        
        for period, interval in periods_intervals:
            try:
                hist = ticker.history(period=period, interval=interval)
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    if price > 0:
                        return price
            except:
                continue
    except:
        pass
    
    # الطريقة 3: download
    try:
        data = yf.download(yf_symbol, period='1d', interval='1m', progress=False)
        if not data.empty:
            close_val = data['Close'].iloc[-1]
            price = float(close_val.iloc[0] if hasattr(close_val, 'iloc') else close_val)
            if price > 0:
                return price
    except:
        pass
    
    return None


def login_required(f):
    """Decorator للتحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token')
        if not session_token:
            return redirect(url_for('login'))
        
        user_info = user_manager.verify_session(session_token)
        if not user_info['success']:
            session.clear()
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """الحصول على بيانات المستخدم الحالي"""
    session_token = session.get('session_token')
    if session_token:
        return user_manager.verify_session(session_token)
    return {'success': False}


# Context processor لتوفير المعلومات للقوالب
@app.context_processor
def inject_user():
    """إضافة معلومات المستخدم لجميع القوالب"""
    user_info = get_current_user()
    return {
        'is_logged_in': user_info['success'],
        'user': user_info if user_info['success'] else None
    }

# Decorator لصلاحيات الأدمن
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('session_token')
        if not session_token:
            return redirect(url_for('login'))
        user_info = user_manager.verify_session(session_token)
        if not user_info['success'] or not user_info.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def load_signals():
    """تحميل الإشارات من قاعدة البيانات مع الأسعار الحالية والنتائج"""
    import sqlite3
    signals = []
    
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # جلب جميع الإشارات من اليوم
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT * FROM signals 
            WHERE DATE(created_at) = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        ''', (today,))
        
        rows = c.fetchall()
        for row in rows:
            symbol = row['symbol']
            signal_type = row['signal_type']
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
            
            # استخدام الدالة المحسنة لجلب السعر
            current_price = get_live_price(symbol)
            
            if current_price:
                # معالجة الصفقات النشطة فقط (نوع الصفقة buy/sell يأتي من التحليل)
                if status == 'active':
                    if signal_type == 'buy':
                        pips = current_price - entry
                        total_range = tp1 - entry
                        
                        # فحص إيقاف الخسارة
                        if current_price <= sl:
                            status = 'closed'
                            result = 'loss'
                            close_price = current_price
                            try:
                                conn2 = sqlite3.connect('vip_signals.db')
                                c2 = conn2.cursor()
                                c2.execute('''
                                    UPDATE signals 
                                    SET status='closed', result='loss', close_price=? 
                                    WHERE signal_id=?
                                ''', (current_price, row['signal_id']))
                                conn2.commit()
                                conn2.close()
                            except:
                                pass
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
                                try:
                                    conn2 = sqlite3.connect('vip_signals.db')
                                    c2 = conn2.cursor()
                                    c2.execute('''
                                        UPDATE signals 
                                        SET status='closed', result='win', close_price=?,
                                            tp1_locked=1, tp2_locked=1, tp3_locked=1
                                        WHERE signal_id=?
                                    ''', (current_price, row['signal_id']))
                                    conn2.commit()
                                    conn2.close()
                                except:
                                    pass
                            else:
                                tp_levels_hit = 3
                        elif current_price >= tp2 and not tp2_locked:
                            tp_levels_hit = 2
                            tp2_locked = 1
                            tp1_locked = 1
                            result = 'win'
                            try:
                                conn2 = sqlite3.connect('vip_signals.db')
                                c2 = conn2.cursor()
                                c2.execute('''
                                    UPDATE signals 
                                    SET result='win', tp1_locked=1, tp2_locked=1
                                    WHERE signal_id=?
                                ''', (row['signal_id'],))
                                conn2.commit()
                                conn2.close()
                            except:
                                pass
                        elif current_price >= tp1 and not tp1_locked:
                            tp_levels_hit = 1
                            tp1_locked = 1
                            result = 'win'
                            try:
                                conn2 = sqlite3.connect('vip_signals.db')
                                c2 = conn2.cursor()
                                c2.execute('''
                                    UPDATE signals 
                                    SET result='win', tp1_locked=1
                                    WHERE signal_id=?
                                ''', (row['signal_id'],))
                                conn2.commit()
                                conn2.close()
                            except:
                                pass
                        else:
                            # عدد المقفلة من قبل
                            tp_levels_hit = tp1_locked + tp2_locked + tp3_locked
                            if tp1_locked:
                                result = 'win'
                                
                    else:  # sell
                        pips = entry - current_price
                        total_range = entry - tp1
                        
                        # فحص إيقاف الخسارة
                        if current_price >= sl:
                            status = 'closed'
                            result = 'loss'
                            close_price = current_price
                            try:
                                conn2 = sqlite3.connect('vip_signals.db')
                                c2 = conn2.cursor()
                                c2.execute('''
                                    UPDATE signals 
                                    SET status='closed', result='loss', close_price=? 
                                    WHERE signal_id=?
                                ''', (current_price, row['signal_id']))
                                conn2.commit()
                                conn2.close()
                            except:
                                pass
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
                                try:
                                    conn2 = sqlite3.connect('vip_signals.db')
                                    c2 = conn2.cursor()
                                    c2.execute('''
                                        UPDATE signals 
                                        SET status='closed', result='win', close_price=?,
                                            tp1_locked=1, tp2_locked=1, tp3_locked=1
                                        WHERE signal_id=?
                                    ''', (current_price, row['signal_id']))
                                    conn2.commit()
                                    conn2.close()
                                except:
                                    pass
                            else:
                                tp_levels_hit = 3
                        elif current_price <= tp2 and not tp2_locked:
                            tp_levels_hit = 2
                            tp2_locked = 1
                            tp1_locked = 1
                            result = 'win'
                            try:
                                conn2 = sqlite3.connect('vip_signals.db')
                                c2 = conn2.cursor()
                                c2.execute('''
                                    UPDATE signals 
                                    SET result='win', tp1_locked=1, tp2_locked=1
                                    WHERE signal_id=?
                                ''', (row['signal_id'],))
                                conn2.commit()
                                conn2.close()
                            except:
                                pass
                        elif current_price <= tp1 and not tp1_locked:
                            tp_levels_hit = 1
                            tp1_locked = 1
                            result = 'win'
                            try:
                                conn2 = sqlite3.connect('vip_signals.db')
                                c2 = conn2.cursor()
                                c2.execute('''
                                    UPDATE signals 
                                    SET result='win', tp1_locked=1
                                    WHERE signal_id=?
                                ''', (row['signal_id'],))
                                conn2.commit()
                                conn2.close()
                            except:
                                pass
                        else:
                            # عدد المقفلة من قبل
                            tp_levels_hit = tp1_locked + tp2_locked + tp3_locked
                            if tp1_locked:
                                result = 'win'
                
                # حساب التقدم
                if total_range != 0:
                    progress = int((pips / total_range) * 100)
                
                # تحديث السعر في قاعدة البيانات
                try:
                    conn2 = sqlite3.connect('vip_signals.db')
                    c2 = conn2.cursor()
                    c2.execute('UPDATE signals SET current_price=? WHERE signal_id=?', (current_price, row['signal_id']))
                    conn2.commit()
                    conn2.close()
                except:
                    pass
            
            signals.append({
                'signal_id': row['signal_id'],
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
                'close_price': close_price,
                'pips': pips,
                'progress': progress,
                'tp_levels_hit': tp_levels_hit,
                'tp1_locked': tp1_locked,
                'tp2_locked': tp2_locked,
                'tp3_locked': tp3_locked,
                'activated': activated
            })
        
        conn.close()
    except Exception as e:
        print(f"❌ خطأ في تحميل الإشارات: {e}")
    
    return signals


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
    pairs_distribution = {}
    if USER_PREFERENCES_FILE.exists():
        try:
            with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                all_prefs = json.load(f)
                for user_id, prefs in all_prefs.items():
                    for pair in prefs.get('pairs', []):
                        pairs_distribution[pair] = pairs_distribution.get(pair, 0) + 1
        except:
            pass
    
    # أكثر الأزواج طلباً
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
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"[LOGIN] Attempt for user: {username}")
        
        if not username or not password:
            print("[LOGIN] Missing username or password")
            return render_template('login.html', error='يرجى ملء جميع الحقول')
        
        # محاولة تسجيل الدخول
        result = user_manager.login_user(
            username, 
            password,
            request.remote_addr
        )
        
        print(f"[LOGIN] Result: {result.get('success')}, Message: {result.get('message')}")
        
        if result['success']:
            session['session_token'] = result['session_token']
            session['user_id'] = result['user_id']
            print(f"[LOGIN] Session set successfully for user_id: {result['user_id']}")
            print(f"[LOGIN] Redirecting to index...")
            return redirect(url_for('index'))
        else:
            print(f"[LOGIN] Login failed: {result['message']}")
            return render_template('login.html', error=result['message'])
    
    # التحقق من وجود جلسة نشطة
    if session.get('session_token'):
        user_info = user_manager.verify_session(session.get('session_token'))
        if user_info['success']:
            return redirect(url_for('index'))
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة التسجيل"""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        terms = request.form.get('terms')
        
        # التحقق من صحة البيانات
        if not all([full_name, username, email, password]):
            return render_template('register.html', error='يرجى ملء جميع الحقول')
        
        if len(username) < 3:
            return render_template('register.html', error='اسم المستخدم يجب أن يكون 3 أحرف على الأقل')
        
        if len(password) < 6:
            return render_template('register.html', error='كلمة المرور يجب أن تكون 6 أحرف على الأقل')
        
        if password != confirm_password:
            return render_template('register.html', error='كلمات المرور غير متطابقة')
        
        if not terms:
            return render_template('register.html', error='يجب قبول الشروط والأحكام')
        
        # تسجيل المستخدم الجديد
        result = user_manager.register_user(username, email, password, full_name)
        
        if result['success']:
            # تسجيل الدخول التلقائي بعد التسجيل
            login_result = user_manager.login_user(username, password, request.remote_addr)
            if login_result['success']:
                session['session_token'] = login_result['session_token']
                session['user_id'] = login_result['user_id']
                return redirect(url_for('index'))
        else:
            return render_template('register.html', error=result['message'])
    
    # التحقق من وجود جلسة نشطة
    if session.get('session_token'):
        user_info = user_manager.verify_session(session.get('session_token'))
        if user_info['success']:
            return redirect(url_for('index'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session_token = session.get('session_token')
    if session_token:
        user_manager.logout_user(session_token)
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    """صفحة الملف الشخصي"""
    user_info = get_current_user()
    if user_info['success']:
        user_data = user_manager.get_user_info(user_info['user_id'])
        return render_template('profile.html', user=user_data)
    return redirect(url_for('login'))


# ============ الصفحات الرئيسية ============

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    user_info = get_current_user()
    
    # إذا لم يكن هناك جلسة، تحويل لصفحة الدخول
    if not user_info['success']:
        return redirect(url_for('login'))
    
    signals = load_signals()
    stats = get_statistics()
    return render_template('index.html', 
                         signals=signals,
                         stats=stats,
                         is_logged_in=True,
                         user=user_info)


@app.route('/signals')
def signals():
    """صفحة الإشارات - تتطلب تسجيل الدخول"""
    user_info = get_current_user()
    
    # تحويل غير المسجلين إلى صفحة الدخول
    if not user_info['success']:
        return redirect(url_for('login'))
    
    signals = load_signals()
    
    # فلترة الإشارات حسب الخطة (إلا إذا كان الأدمن jakel2008)
    username = user_info.get('username', '')
    
    # الأدمن jakel2008 يرى كل الإشارات
    if username == 'jakel2008':
        filtered_signals = signals
    else:
        # فلترة حسب خطة المستخدم
        plan = user_info.get('plan', 'free')
        quality_threshold = {
            'free': 90,
            'bronze': 80,
            'silver': 70,
            'gold': 60,
            'platinum': 50
        }
        threshold = quality_threshold.get(plan, 90)
        filtered_signals = [s for s in signals if s.get('quality_score', 0) >= threshold]
    
    return render_template('signals.html', 
                         signals=filtered_signals,
                         all_signals_count=len(signals),
                         is_logged_in=True,
                         is_admin=user_info.get('is_admin', False),
                         user=user_info)


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


@app.route('/select_location/<plan>')
@login_required
def select_location(plan):
    """صفحة اختيار الموقع الجغرافي للدفع"""
    user_info = get_current_user()
    
    # خطط الاشتراك
    plans = {
        'bronze': {'name': 'Bronze', 'price': 29, 'duration_days': 30, 'signals': 3},
        'silver': {'name': 'Silver', 'price': 69, 'duration_days': 90, 'signals': 5},
        'gold': {'name': 'Gold', 'price': 199, 'duration_days': 365, 'signals': 7},
        'platinum': {'name': 'Platinum', 'price': 499, 'duration_days': 365, 'signals': 10}
    }
    
    if plan not in plans:
        return redirect(url_for('index'))
    
    return render_template('select_location.html', 
                         plan=plan,
                         plan_data=plans[plan],
                         user=user_info)


@app.route('/payment/<location>/<plan>')
@login_required
def payment_page(location, plan):
    """صفحة الدفع حسب الموقع"""
    user_info = get_current_user()
    
    plans = {
        'bronze': {'name': 'Bronze', 'price': 29, 'duration_days': 30, 'signals': 3},
        'silver': {'name': 'Silver', 'price': 69, 'duration_days': 90, 'signals': 5},
        'gold': {'name': 'Gold', 'price': 199, 'duration_days': 365, 'signals': 7},
        'platinum': {'name': 'Platinum', 'price': 499, 'duration_days': 365, 'signals': 10}
    }
    
    if plan not in plans or location not in ['jordan', 'international']:
        return redirect(url_for('index'))
    
    plan_data = plans[plan]
    
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
                         plan_data=plan_data,
                         user=user_info)


@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة التحكم"""
    user_info = get_current_user()
    
    # تحميل تفضيلات الأزواج
    user_pairs = []
    if USER_PREFERENCES_FILE.exists():
        try:
            with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                all_prefs = json.load(f)
                user_prefs = all_prefs.get(str(user_info.get('user_id')), {})
                user_pairs = user_prefs.get('pairs', [])
        except:
            pass
    
    return render_template('dashboard.html',
                         user=user_info,
                         is_logged_in=True,
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
    signals = load_signals()
    user_info = get_current_user()
    
    # فلترة الإشارات حسب الخطة (إلا إذا كان الأدمن jakel2008)
    username = user_info.get('username', '') if user_info['success'] else ''
    
    # الأدمن jakel2008 يرى كل الإشارات
    if username == 'jakel2008':
        filtered_signals = signals
    elif user_info['success']:
        # فلترة حسب خطة المستخدم
        plan = user_info.get('plan', 'free')
        quality_threshold = {
            'free': 90,
            'bronze': 80,
            'silver': 70,
            'gold': 60,
            'platinum': 50
        }
        threshold = quality_threshold.get(plan, 90)
        filtered_signals = [s for s in signals if s.get('quality_score', 0) >= threshold]
    else:
        # المستخدمين غير المسجلين يرون فقط الإشارات عالية الجودة
        filtered_signals = [s for s in signals if s.get('quality_score', 0) >= 90]
    
    return jsonify(filtered_signals)


@app.route('/api/recommendations')
def api_recommendations():
    """API لجلب التوصيات"""
    recommendations = load_recommendations()
    return jsonify(recommendations)


@app.route('/api/analysis')
def api_analysis():
    """API لجلب التحليلات"""
    analyses = load_analysis()
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
    """جلب جميع الأزواج المتاحة من YF_SYMBOLS"""
    return list(YF_SYMBOLS.keys())


@app.route('/api/user-pairs-preferences')
@login_required
def api_get_user_pairs_preferences():
    """API لجلب تفضيلات المستخدم للأزواج"""
    user_info = get_current_user()
    if not user_info['success']:
        return jsonify({'success': False, 'message': 'غير مسجل'}), 401
    
    user_id = user_info['user_id']
    
    try:
        # تحميل تفضيلات المستخدم من ملف JSON
        if USER_PREFERENCES_FILE.exists():
            with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                all_preferences = json.load(f)
                user_prefs = all_preferences.get(str(user_id), {})
                return jsonify({
                    'success': True,
                    'pairs': user_prefs.get('pairs', [])
                })
        else:
            return jsonify({'success': True, 'pairs': []})
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
    data = request.get_json()
    pairs = data.get('pairs', [])
    
    try:
        # تحميل التفضيلات الحالية
        all_preferences = {}
        if USER_PREFERENCES_FILE.exists():
            with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                all_preferences = json.load(f)
        
        # تحديث تفضيلات المستخدم
        all_preferences[str(user_id)] = {
            'pairs': pairs,
            'updated_at': datetime.now().isoformat()
        }
        
        # حفظ التفضيلات
        with open(USER_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_preferences, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': 'تم حفظ التفضيلات بنجاح',
            'pairs_count': len(pairs)
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
    """صفحة لوحة تحكم الأدمن"""
    user_info = get_current_user()
    return render_template('admin.html',
                         user=user_info,
                         is_logged_in=True,
                         is_admin=True)

# ======= Admin APIs =======
@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    users = user_manager.list_users()
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
    subscriptions = subscription_manager.get_all_subscriptions()
    return jsonify({'success': True, 'subscriptions': subscriptions})

@app.route('/api/admin/update_plan', methods=['POST'])
@admin_required
def api_admin_update_plan():
    """تحديث خطة المستخدم - يتم إلغاء الاشتراكات السابقة وتفعيل الخطة الجديدة فقط"""
    data = request.json or {}
    user_id = data.get('user_id')
    plan = data.get('plan')
    duration_days = data.get('duration_days')
    
    try:
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
    
    success, message = subscription_manager.cancel_subscription(user_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/admin/reactivate_subscription', methods=['POST'])
@admin_required
def api_admin_reactivate_subscription():
    """إعادة تفعيل اشتراك المستخدم"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    success, message = subscription_manager.reactivate_subscription(user_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/admin/activate_subscription', methods=['POST'])
@admin_required
def api_admin_activate_subscription():
    """تفعيل اشتراك المستخدم"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    try:
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
        
        return jsonify({'success': True, 'message': 'تم إيقاف الاشتراك مؤقتاً'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في إيقاف الاشتراك: {str(e)}'})

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
    location = data.get('location', 'jordan')  # jordan أو international
    payment_method = data.get('payment_method', 'cliq')  # cliq, bank_transfer, visa, crypto
    transaction_id = data.get('transaction_id', '')  # رقم العملية أو المعاملة
    
    try:
        # تفاصيل الخطة
        plans_info = {
            'free': {'name': 'Free', 'price': 0, 'duration_days': 0, 'signals_per_day': 1, 'plan': 'free'},
            'bronze': {'name': 'Bronze', 'price': 29, 'duration_days': 30, 'signals_per_day': 3, 'plan': 'bronze'},
            'silver': {'name': 'Silver', 'price': 69, 'duration_days': 90, 'signals_per_day': 5, 'plan': 'silver'},
            'gold': {'name': 'Gold', 'price': 199, 'duration_days': 365, 'signals_per_day': 7, 'plan': 'gold'},
            'platinum': {'name': 'Platinum', 'price': 499, 'duration_days': 365, 'signals_per_day': 10, 'plan': 'platinum'}
        }
        
        if plan not in plans_info:
            return jsonify({'success': False, 'error': 'خطة غير صحيحة'}), 400
        
        plan_data = plans_info[plan]
        
        # إضافة معلومات الموقع والدفع
        payment_info = {
            'location': location,
            'payment_method': payment_method,
            'transaction_id': transaction_id
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
    
    # آخر الإشارات والتوصيات
    recent_signals = load_signals()[:5]
    recent_recommendations = load_recommendations()[:5]
    
    stats = {
        'total_users': len(all_subscriptions),
        'active_users': len(active_users),
        'total_signals': len(load_signals()),
        'total_recommendations': len(load_recommendations()),
        'plans_stats': plans_stats
    }
    
    return render_template(
        'admin_panel.html',
        user_info=user_info,
        stats=stats,
        recent_signals=recent_signals,
        recent_recommendations=recent_recommendations
    )

@app.route('/subscription-management')
@admin_required
def subscription_management():
    """صفحة إدارة الاشتراكات"""
    user_info = get_current_user()
    return render_template('subscriptions_management.html', user_info=user_info)

@app.route('/forex-analyzer')
@admin_required
def forex_analyzer():
    """صفحة محلل الفوركس"""
    user_info = get_current_user()
    return render_template('forex_analyzer.html', user_info=user_info)

@app.route('/api/forex-analysis', methods=['POST'])
@admin_required
def api_forex_analysis():
    """API لتحليل الفوركس - يستخدم المحلل المتقدم"""
    data = request.json or {}
    symbol = data.get('symbol', 'EUR/USD')
    interval = data.get('interval', '1h')
    
    try:
        from advanced_analyzer_engine import perform_full_analysis
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
        signal_id = data.get('signal_id')
        
        if not signal_id:
            return jsonify({'success': False, 'error': 'Signal ID is required'}), 400
        
        # البحث عن الإشارة
        signal_file = SIGNALS_DIR / signal_id
        if not signal_file.exists():
            return jsonify({'success': False, 'error': 'Signal not found'}), 404
        
        with open(signal_file, 'r', encoding='utf-8') as f:
            signal_data = json.load(f)
        
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


@app.route('/api/admin/broadcast-message', methods=['POST'])
@admin_required
def api_admin_broadcast_message():
    """إرسال رسالة عامة لجميع المشتركين"""
    try:
        data = request.json
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # إرسال الرسالة لجميع المشتركين
        result = telegram_sender.send_report_to_subscribers(message_text)
        
        return jsonify({
            'success': True,
            'sent_count': result.get('sent_count', 0),
            'failed_count': result.get('failed_count', 0),
            'total_subscribers': result.get('total_subscribers', 0)
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
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, full_name, plan, created_at, is_admin, is_active
            FROM users
            ORDER BY created_at DESC
        ''')
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'plan': row[4],
                'created_at': row[5],
                'is_admin': row[6],
                'is_active': row[7]
            })
        conn.close()
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
    """تعديل بوت"""
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

@app.route('/api/send-to-telegram', methods=['POST'])
@admin_required
def send_analysis_to_telegram():
    """إرسال التحليل للبوت"""
    try:
        data = request.json
        symbol = data.get('symbol')
        recommendation = data.get('recommendation')
        entry = data.get('entry_point')
        tp1 = data.get('tp1')
        tp2 = data.get('tp2')
        tp3 = data.get('tp3')
        sl = data.get('stop_loss')
        confidence = data.get('confidence', '')
        interval = data.get('interval', '1h')
        
        # تنسيق الرسالة
        message = f"""
🔔 <b>تحليل جديد - MONEY MAKER</b> 🔔

📊 <b>الزوج:</b> {symbol}
⏱ <b>الإطار الزمني:</b> {interval}

{confidence}
✅ <b>التوصية:</b> {recommendation}

💰 <b>السعر الحالي:</b> {entry:.5f}

🎯 <b>أهداف الربح:</b>
  • TP1: {tp1:.5f}
  • TP2: {tp2:.5f}
  • TP3: {tp3:.5f}

🛑 <b>وقف الخسارة:</b> {sl:.5f}

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
                    'scheduler': 'unknown'
                }
            }
        
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
            from trade_statistics import TradeStatistics
            stats_engine = TradeStatistics()
            stats = stats_engine.get_statistics(days=30)
            win_rate = stats.get('win_rate', 0)
        except:
            win_rate = 0
        
        return jsonify({
            'success': True,
            'status': system_data.get('status', {}),
            'metrics': {
                'total_users': total_users,
                'total_signals': total_signals_today,
                'active_trades': active_trades_count,
                'win_rate': win_rate
            },
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
        signals_dir = Path(__file__).parent / 'signals'
        
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
        
        # هنا يمكن إضافة منطق تشغيل المكونات
        # مثلاً استخدام subprocess لتشغيل السكريبتات
        
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
        
        # هنا يمكن إضافة منطق إيقاف المكونات
        
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
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT signal_id, symbol, signal_type, entry_price, stop_loss, 
                   take_profit_1, take_profit_2, take_profit_3, status
            FROM signals 
            WHERE DATE(created_at) = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (today,))
        
        rows = c.fetchall()
        signals_data = []
        
        for row in rows:
            symbol = row['symbol']
            signal_type = row['signal_type']
            entry = row['entry_price']
            tp1 = row['take_profit_1']
            
            # استخدام الدالة المحسنة
            current_price = get_live_price(symbol)
            
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
                        'current_price': current_price,
                        'pips': round(pips, 2),
                        'progress': max(0, progress)
                    })
                except Exception as e:
                    print(f"Error fetching price for {symbol}: {e}")
                    continue
        
        conn.close()
        
        return jsonify({
            'success': True,
            'signals': signals_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/update_status')
def api_update_status():
    """API للتحقق من تغيير الحالات"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT signal_id, symbol, signal_type, entry_price, stop_loss, 
                   take_profit_1, take_profit_2, take_profit_3, status,
                   tp1_locked, tp2_locked, tp3_locked
            FROM signals 
            WHERE DATE(created_at) = ? AND status = 'active'
        ''', (today,))
        
        rows = c.fetchall()
        needs_refresh = False
        
        for row in rows:
            try:
                symbol = row['symbol']
                signal_type = row['signal_type']
                entry = row['entry_price']
                sl = row['stop_loss']
                tp1 = row['take_profit_1']
                tp2 = row['take_profit_2']
                tp3 = row['take_profit_3']
                tp1_locked = row['tp1_locked'] if 'tp1_locked' in row.keys() else 0
                tp2_locked = row['tp2_locked'] if 'tp2_locked' in row.keys() else 0
                tp3_locked = row['tp3_locked'] if 'tp3_locked' in row.keys() else 0
                
                # استخدام الدالة المحسنة
                current_price = get_live_price(symbol)
                
                if current_price:
                    # فحص التغييرات في الحالة
                    if signal_type == 'buy':
                        # فحص SL
                        if current_price <= sl:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET status='closed', result='loss', close_price=? 
                                WHERE signal_id=?
                            ''', (current_price, row['signal_id']))
                        # فحص TP3
                        elif current_price >= tp3 and not tp3_locked:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET status='closed', result='win', close_price=?,
                                    tp1_locked=1, tp2_locked=1, tp3_locked=1
                                WHERE signal_id=?
                            ''', (current_price, row['signal_id']))
                        # فحص TP2
                        elif current_price >= tp2 and not tp2_locked:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET result='win', tp1_locked=1, tp2_locked=1
                                WHERE signal_id=?
                            ''', (row['signal_id'],))
                        # فحص TP1
                        elif current_price >= tp1 and not tp1_locked:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET result='win', tp1_locked=1
                                WHERE signal_id=?
                            ''', (row['signal_id'],))
                    else:  # sell
                        # فحص SL
                        if current_price >= sl:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET status='closed', result='loss', close_price=? 
                                WHERE signal_id=?
                            ''', (current_price, row['signal_id']))
                        # فحص TP3
                        elif current_price <= tp3 and not tp3_locked:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET status='closed', result='win', close_price=?,
                                    tp1_locked=1, tp2_locked=1, tp3_locked=1
                                WHERE signal_id=?
                            ''', (current_price, row['signal_id']))
                        # فحص TP2
                        elif current_price <= tp2 and not tp2_locked:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET result='win', tp1_locked=1, tp2_locked=1
                                WHERE signal_id=?
                            ''', (row['signal_id'],))
                        # فحص TP1
                        elif current_price <= tp1 and not tp1_locked:
                            needs_refresh = True
                            c.execute('''
                                UPDATE signals 
                                SET result='win', tp1_locked=1
                                WHERE signal_id=?
                            ''', (row['signal_id'],))
            except Exception as e:
                print(f"Error checking status for {symbol}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'needs_refresh': needs_refresh
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ============== نهاية API للتحديث التلقائي ==============

if __name__ == '__main__':
    banner = "=" * 60
    print(banner)
    print("VIP Signals Web Server - Login System")
    print(banner)
    print("Open your browser:")
    print("  http://localhost:5000")
    print("Register page:")
    print("  http://localhost:5000/register")
    print(banner)

    app.run(debug=True, host='0.0.0.0', port=5000)

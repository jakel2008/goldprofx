"""
تطبيق ويب بسيط لنظام الإشارات VIP
Simple VIP Signals Web Application
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from track_trades import generate_report
from user_manager import UserManager
from vip_subscription_system import SubscriptionManager
from auto_pairs_analyzer import build_trade_report
from email_service import email_service
import requests

app = Flask(__name__)
app.secret_key = 'gold-pro-vip-2026'

user_manager = UserManager()
subscription_manager = SubscriptionManager()

SIGNALS_DIR = Path(__file__).parent / "signals"


def get_current_user():
    """جلب المستخدم الحالي من الجلسة"""
    token = session.get('session_token')
    if not token:
        return {'success': False}
    return user_manager.verify_session(token)


def login_required(view_func):
    def wrapper(*args, **kwargs):
        user_info = get_current_user()
        if not user_info.get('success'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'unauthorized'}), 401
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def admin_required(view_func):
    def wrapper(*args, **kwargs):
        user_info = get_current_user()
        if not user_info.get('success'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'unauthorized'}), 401
            return redirect(url_for('login'))
        if user_info.get('role') not in ('admin', 'developer'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'forbidden'}), 403
            return redirect(url_for('index'))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def developer_required(view_func):
    def wrapper(*args, **kwargs):
        user_info = get_current_user()
        if not user_info.get('success'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'unauthorized'}), 401
            return redirect(url_for('login'))
        if user_info.get('role') != 'developer':
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'forbidden'}), 403
            return redirect(url_for('index'))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def render_page(template_name):
    """عرض صفحة مع بيانات المستخدم"""
    user_info = get_current_user()
    if not user_info.get('success'):
        return redirect(url_for('login'))
    return render_template(
        template_name,
        user=user_info,
        is_logged_in=True
    )

def load_signals():
    """تحميل الإشارات من مجلد signals (مع استبعاد الصفقات المنتهية)"""
    signals = []
    if SIGNALS_DIR.exists():
        for file in SIGNALS_DIR.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    signal = json.load(f)
                    if isinstance(signal, dict):
                        signal['symbol'] = signal.get('symbol') or signal.get('pair')
                        signal['pair'] = signal.get('pair') or signal.get('symbol')
                        if signal.get('entry_price') is None:
                            signal['entry_price'] = signal.get('entry')
                        if signal.get('entry') is None:
                            signal['entry'] = signal.get('entry_price')
                        if signal.get('stop_loss') is None:
                            signal['stop_loss'] = signal.get('sl')
                        if signal.get('sl') is None:
                            signal['sl'] = signal.get('stop_loss')
                        if signal.get('take_profit_1') is None:
                            signal['take_profit_1'] = signal.get('tp1')
                        if signal.get('tp1') is None:
                            signal['tp1'] = signal.get('take_profit_1')
                        if signal.get('take_profit_2') is None:
                            signal['take_profit_2'] = signal.get('tp2')
                        if signal.get('tp2') is None:
                            signal['tp2'] = signal.get('take_profit_2')
                        if signal.get('take_profit_3') is None:
                            signal['take_profit_3'] = signal.get('tp3')
                        if signal.get('tp3') is None:
                            signal['tp3'] = signal.get('take_profit_3')
                        try:
                            signal['quality_score'] = float(signal.get('quality_score', 0) or 0)
                        except Exception:
                            signal['quality_score'] = 0
                    signals.append(signal)
            except:
                pass

    try:
        report = generate_report(save_file=True)
        active_pairs = {
            t.get('pair') for t in report.get('active_trades', []) if t.get('pair')
        }
        if active_pairs:
            signals = [s for s in signals if (s.get('pair') or s.get('symbol')) in active_pairs]
    except:
        pass

    return sorted(signals, key=lambda x: x.get('timestamp', ''), reverse=True)


def filter_signals_by_plan(signals, user_info):
    """فلترة الإشارات حسب خطة المستخدم"""
    if not user_info.get('success'):
        return []
    if user_info.get('role') in ('admin', 'developer') or user_info.get('is_admin'):
        return signals

    plan = user_info.get('plan', 'free')
    quality_threshold = {
        'free': 90,
        'bronze': 80,
        'silver': 70,
        'gold': 60,
        'platinum': 50
    }
    threshold = quality_threshold.get(plan, 90)
    filtered = []
    for s in signals:
        try:
            score = float(s.get('quality_score', 0) or 0)
        except Exception:
            score = 0
        if score >= threshold:
            filtered.append(s)
    return filtered


def load_recent_signals(limit=10):
    """تحميل أحدث الإشارات للوحة الأدمن"""
    signals = []
    if SIGNALS_DIR.exists():
        for file in sorted(SIGNALS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    data['file'] = file.name
                    data['symbol'] = data.get('symbol') or data.get('pair')
                    signals.append(data)
                if len(signals) >= limit:
                    break
            except:
                continue
    return signals


def load_recent_recommendations(limit=10):
    """تحميل أحدث التوصيات للوحة الأدمن"""
    file_path = Path(__file__).parent / 'recommendations_history.json'
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data[:limit] if isinstance(data, list) else []
    except:
        return []


def load_all_recommendations():
    """تحميل جميع التوصيات التاريخية"""
    file_path = Path(__file__).parent / 'recommendations_history.json'
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except:
        return []


def build_admin_stats():
    """إحصائيات بسيطة للوحة الأدمن"""
    users = user_manager.list_users()
    active_users = sum(1 for u in users if u.get('is_active'))
    total_signals = len(list(SIGNALS_DIR.glob("*.json"))) if SIGNALS_DIR.exists() else 0
    total_recommendations = len(load_recent_recommendations(100))
    return {
        'total_users': len(users),
        'active_users': active_users,
        'total_signals': total_signals,
        'total_recommendations': total_recommendations
    }

@app.route('/')
def root():
    """توجيه البداية لصفحة الدخول"""
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def index():
    """الصفحة الرئيسية"""
    signals = load_signals()
    user_info = get_current_user()
    filtered_signals = filter_signals_by_plan(signals, user_info)
    return render_template('simple_index.html', signals=filtered_signals, user=user_info, is_logged_in=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة الدخول"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        result = user_manager.login_user(username, password, request.remote_addr or '')
        if result.get('success'):
            session['session_token'] = result.get('session_token')
            return redirect(url_for('index'))
        return render_template('login_simple.html', error=result.get('message'))
    return render_template('login_simple.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة التسجيل"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        full_name = request.form.get('full_name', '').strip()

        if password != confirm_password:
            return render_template('register.html', error='كلمتا المرور غير متطابقتين')

        result = user_manager.register_user(username, email, password, full_name)
        if result.get('success'):
            return redirect(url_for('login'))
        return render_template('register.html', error=result.get('message'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """الملف الشخصي"""
    return render_page('profile.html')

@app.route('/api/signals')
@login_required
def api_signals():
    """API للحصول على الإشارات"""
    signals = load_signals()
    user_info = get_current_user()
    filtered_signals = filter_signals_by_plan(signals, user_info)
    return jsonify(filtered_signals)

@app.route('/signals')
@login_required
def signals():
    """صفحة الإشارات"""
    signals = load_signals()
    user_info = get_current_user()
    filtered_signals = filter_signals_by_plan(signals, user_info)
    return render_template('signals.html', signals=filtered_signals)

@app.route('/trades')
@login_required
def trades():
    """صفحة متابعة الصفقات"""
    return render_template('trades.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة التحكم"""
    return render_page('dashboard.html')

@app.route('/reports')
@login_required
def reports():
    """صفحة التقارير"""
    return render_page('reports.html')

@app.route('/pairs-selection')
@login_required
def pairs_selection():
    """صفحة اختيار الأزواج"""
    return render_page('pairs_selection.html')

@app.route('/plans')
@login_required
def plans():
    """خطط الاشتراك"""
    return render_page('plans.html')

@app.route('/admin')
@admin_required
def admin():
    """لوحة الأدمن"""
    return render_page('admin.html')

@app.route('/admin-panel')
@admin_required
def admin_panel():
    """لوحة الأدمن المتقدمة"""
    user_info = get_current_user()
    stats = build_admin_stats()
    recent_signals = load_recent_signals()
    recent_recommendations = load_recent_recommendations()
    return render_template(
        'admin_panel.html',
        user=user_info,
        is_logged_in=True,
        stats=stats,
        recent_signals=recent_signals,
        recent_recommendations=recent_recommendations
    )

@app.route('/admin-management')
@admin_required
def admin_management():
    """إدارة المستخدمين"""
    return render_page('admin_management.html')

@app.route('/subscriptions-management')
@admin_required
def subscriptions_management():
    """إدارة الاشتراكات"""
    return render_page('admin_management.html')

@app.route('/bot-management')
@admin_required
def bot_management():
    """إدارة البوت"""
    return render_page('bot_management.html')

@app.route('/master-dashboard')
@admin_required
def master_dashboard():
    """اللوحة الرئيسية"""
    return render_page('master_dashboard.html')

@app.route('/advanced-analyzer')
@login_required
def advanced_analyzer():
    """المحلل العميق"""
    return render_page('advanced_analyzer.html')

@app.route('/forex-analyzer')
@login_required
def forex_analyzer():
    """محلل الفوركس"""
    return render_page('forex_analyzer.html')

@app.route('/api/trades_status')
@login_required
def api_trades_status():
    """API لحالة الصفقات"""
    try:
        data = generate_report(save_file=True)
        return jsonify(data)
    except:
        return jsonify({'error': 'No tracking data'})


@app.route('/api/advanced-analysis', methods=['POST'])
@login_required
def advanced_analysis():
    """API للتحليل المتقدم الكامل"""
    try:
        from advanced_analyzer_engine import perform_full_analysis

        data = request.json or {}
        symbol = data.get('symbol', 'EUR/USD')
        interval = data.get('interval', '1h')

        result = perform_full_analysis(symbol, interval)

        if result.get('success'):
            return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': result.get('error')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export-trading-signal', methods=['POST'])
@login_required
def export_trading_signal():
    """تصدير إشارة تداول"""
    try:
        data = request.json or {}
        symbol = data.get('symbol', '').replace('/', '')

        signal = {
            'symbol': symbol,
            'trade_type': data.get('trade_type', 'BUY'),
            'entry_price': data.get('entry_price'),
            'take_profit': data.get('take_profit', []),
            'stop_loss': data.get('stop_loss'),
            'confidence': data.get('confidence', 'MEDIUM'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timeframe': data.get('interval'),
            'recommendation_text': data.get('recommendation')
        }

        filename = f"MoneyMakers_{signal['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join('signals', filename)
        os.makedirs('signals', exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(signal, f, indent=4, ensure_ascii=False)

        return jsonify({'success': True, 'message': 'تم تصدير الإشارة بنجاح', 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/publish-to-recommendations', methods=['POST'])
@login_required
def publish_to_recommendations():
    """نشر التحليل على صفحة التوصيات"""
    try:
        data = request.json or {}
        recommendation = {
            'pair': data.get('symbol'),
            'action': data.get('recommendation'),
            'entry': data.get('entry_point'),
            'tp1': data.get('tp1'),
            'tp2': data.get('tp2'),
            'tp3': data.get('tp3'),
            'sl': data.get('stop_loss'),
            'analysis': data.get('analysis_text', ''),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'confidence': data.get('confidence', ''),
            'timeframe': data.get('interval', '1h')
        }

        recommendations_file = 'recommendations_history.json'
        recommendations = []
        if os.path.exists(recommendations_file):
            with open(recommendations_file, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)

        recommendations.insert(0, recommendation)
        recommendations = recommendations[:100]

        with open(recommendations_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=4, ensure_ascii=False)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/send-to-telegram', methods=['POST'])
@login_required
def send_to_telegram():
    """إرسال التحليل إلى تلجرام"""
    try:
        data = request.json or {}
        bot_token = os.environ.get("MM_TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("MM_TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            return jsonify({'success': False, 'error': 'Telegram not configured'})

        message = (
            f"📊 تحليل {data.get('symbol')}\n"
            f"التوصية: {data.get('recommendation')}\n"
            f"الدخول: {data.get('entry_point')}\n"
            f"SL: {data.get('stop_loss')}\n"
            f"TP1: {data.get('tp1')}\n"
            f"TP2: {data.get('tp2')}\n"
            f"TP3: {data.get('tp3')}\n"
            f"الفريم: {data.get('interval')}"
        )

        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={'chat_id': chat_id, 'text': message},
            timeout=10
        )

        if response.status_code == 200:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': response.text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/stats')
@login_required
def api_stats():
    """إحصائيات عامة لصفحة التقارير"""
    signals = load_signals()
    recommendations = load_all_recommendations()
    users = user_manager.list_users()

    buy_signals = 0
    sell_signals = 0
    top_pairs = {}
    quality_scores = []

    for s in signals:
        signal_type = (s.get('signal') or s.get('rec') or s.get('signal_type') or s.get('trade_type') or '').lower()
        if 'buy' in signal_type or 'شراء' in signal_type:
            buy_signals += 1
        elif 'sell' in signal_type or 'بيع' in signal_type:
            sell_signals += 1

        pair = s.get('pair') or s.get('symbol') or 'UNKNOWN'
        top_pairs[pair] = top_pairs.get(pair, 0) + 1

        try:
            quality_scores.append(float(s.get('quality_score', 0) or 0))
        except Exception:
            pass

    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0
    high_quality = sum(1 for q in quality_scores if q >= 75)
    medium_quality = sum(1 for q in quality_scores if 50 <= q < 75)

    plans = {}
    for u in users:
        plan = u.get('plan', 'free')
        plans[plan] = plans.get(plan, 0) + 1

    return jsonify({
        'signals_count': len(signals),
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'recommendations_count': len(recommendations),
        'average_quality': avg_quality,
        'high_quality_recommendations': high_quality,
        'medium_quality_recommendations': medium_quality,
        'subscribers_count': len(users),
        'plans': plans,
        'top_pairs': dict(sorted(top_pairs.items(), key=lambda x: x[1], reverse=True)[:10])
    })


@app.route('/api/detailed-report')
@login_required
def api_detailed_report():
    """تقرير تفصيلي للتوصيات"""
    recommendations = load_all_recommendations()
    timeframes = {}
    for r in recommendations:
        tf = r.get('timeframe') or r.get('tf') or r.get('interval') or 'غير محدد'
        timeframes[tf] = timeframes.get(tf, 0) + 1

    return jsonify({
        'total_signals': len(load_signals()),
        'total_recommendations': len(recommendations),
        'recommendations_by_timeframe': timeframes
    })


@app.route('/api/trades-report')
@login_required
def api_trades_report():
    """تقرير الصفقات المنتهية والنشطة"""
    data = build_trade_report(hours=1)
    return jsonify(data)


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
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        user_id = None
    try:
        is_admin = int(data.get('is_admin', 0)) == 1
    except Exception:
        is_admin = False

    current_user = get_current_user()
    if user_id is None:
        return jsonify({'success': False, 'message': 'معرّف المستخدم غير صالح'}), 400

    target = next((u for u in user_manager.list_users() if u.get('id') == user_id), None)
    target_role = (target or {}).get('role', 'user')

    if not target:
        return jsonify({'success': False, 'message': 'المستخدم غير موجود'}), 404

    if target_role == 'developer' and current_user.get('role') != 'developer':
        return jsonify({'success': False, 'message': 'لا يمكن تعديل صلاحيات المطور'}), 403

    if is_admin:
        result = user_manager.set_user_role(user_id, 'admin')
    else:
        result = user_manager.set_user_role(user_id, 'user')

    return jsonify(result)


@app.route('/api/admin/set_active', methods=['POST'])
@admin_required
def api_admin_set_active():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        user_id = None
    try:
        is_active = int(data.get('is_active', 0)) == 1
    except Exception:
        is_active = False
    if user_id is None:
        return jsonify({'success': False, 'message': 'معرّف المستخدم غير صالح'}), 400
    result = user_manager.set_active_status(user_id, is_active)
    return jsonify(result)


@app.route('/api/admin/subscriptions')
@admin_required
def api_admin_subscriptions():
    subscriptions = subscription_manager.get_all_subscriptions()
    return jsonify({'success': True, 'subscriptions': subscriptions})


@app.route('/api/admin/update_plan', methods=['POST'])
@admin_required
def api_admin_update_plan():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        user_id = None
    plan = data.get('plan')
    duration_days = data.get('duration_days')

    if user_id is None:
        return jsonify({'success': False, 'message': 'معرّف المستخدم غير صالح'}), 400

    try:
        try:
            conn_vip = sqlite3.connect('vip_subscriptions.db')
            cursor_vip = conn_vip.cursor()
            cursor_vip.execute('''
                UPDATE users 
                SET status = 'cancelled', subscription_end = ?
                WHERE user_id = ? AND status IN ('active', 'trial')
            ''', (datetime.now().isoformat(), user_id))
            conn_vip.commit()
            conn_vip.close()
        except Exception:
            pass

        success, message = subscription_manager.update_subscription_plan(
            user_id, plan, duration_days
        )

        user_manager.update_user_plan(user_id, plan)

        if not success and 'المستخدم غير موجود' in str(message):
            return jsonify({'success': True, 'message': 'تم تحديث الخطة في الموقع'}), 200

        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/extend_subscription', methods=['POST'])
@admin_required
def api_admin_extend_subscription():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        user_id = None
    days = int(data.get('days', 0))

    if user_id is None:
        return jsonify({'success': False, 'message': 'معرّف المستخدم غير صالح'}), 400
    success, message = subscription_manager.extend_subscription(user_id, days)
    return jsonify({'success': success, 'message': message})


@app.route('/api/admin/cancel_subscription', methods=['POST'])
@admin_required
def api_admin_cancel_subscription():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        user_id = None

    if user_id is None:
        return jsonify({'success': False, 'message': 'معرّف المستخدم غير صالح'}), 400
    success, message = subscription_manager.cancel_subscription(user_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/admin/reactivate_subscription', methods=['POST'])
@admin_required
def api_admin_reactivate_subscription():
    data = request.json or {}
    try:
        user_id = int(data.get('user_id'))
    except Exception:
        user_id = None

    if user_id is None:
        return jsonify({'success': False, 'message': 'معرّف المستخدم غير صالح'}), 400
    success, message = subscription_manager.reactivate_subscription(user_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/admin/subscription_requests')
@admin_required
def api_admin_subscription_requests():
    try:
        db_path = Path(__file__).parent / 'users.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, user_id, username, email, full_name, plan, price, 
                   duration_days, request_date, status, payment_proof, admin_notes,
                   location, payment_method, transaction_id
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
                'admin_notes': row[11],
                'location': row[12],
                'payment_method': row[13],
                'transaction_id': row[14]
            })

        conn.close()
        return jsonify({'success': True, 'requests': requests_list})
    except Exception as e:
        if 'no such table' in str(e).lower():
            return jsonify({'success': True, 'requests': []})
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/approve_subscription', methods=['POST'])
@admin_required
def api_admin_approve_subscription():
    data = request.json or {}
    request_id = data.get('request_id')
    admin_notes = data.get('admin_notes', '')

    try:
        db_path = Path(__file__).parent / 'users.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

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

        try:
            conn_vip = sqlite3.connect('vip_subscriptions.db')
            cursor_vip = conn_vip.cursor()
            cursor_vip.execute('''
                UPDATE users 
                SET status = 'cancelled', subscription_end = ?
                WHERE user_id = ? AND status IN ('active', 'trial')
            ''', (datetime.now().isoformat(), user_id))
            conn_vip.commit()
            conn_vip.close()
        except Exception:
            pass

        user_manager.update_user_plan(user_id, plan)
        subscription_manager.update_subscription_plan(user_id, plan, duration_days)

        cursor.execute('''
            UPDATE subscription_requests
            SET status = 'approved', admin_notes = ?
            WHERE id = ?
        ''', (admin_notes, request_id))

        conn.commit()
        conn.close()

        end_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')
        email_service.send_activation_confirmation(user_email, plan, end_date)

        return jsonify({'success': True, 'message': f'تم تفعيل خطة {plan.upper()} بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/reject_subscription', methods=['POST'])
@admin_required
def api_admin_reject_subscription():
    data = request.json or {}
    request_id = data.get('request_id')
    admin_notes = data.get('admin_notes', '')

    try:
        db_path = Path(__file__).parent / 'users.db'
        conn = sqlite3.connect(db_path)
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

if __name__ == '__main__':
    banner = "=" * 60
    print(banner)
    print("GOLD PRO - VIP Signals System")
    print(banner)
    print("Server is running on:")
    print("   http://localhost:5000")
    print("   http://127.0.0.1:5000")
    print(banner)
    print("Press CTRL+C to stop")
    print(banner)
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

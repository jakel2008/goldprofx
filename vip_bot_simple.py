"""
Unified VIP Bot - Simple Version
"""
import os
import sys
import requests
import json
import time
from datetime import datetime

# Encoding fix for Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from vip_subscription_system import SubscriptionManager
from quality_scorer import get_quality_threshold_for_plan

# استخدام المحلل المتقدم
try:
    from simple_analyzer_wrapper import full_analysis
    USE_ADVANCED_ANALYZER = True
except:
    try:
        from forex_analyzer import perform_analysis
        USE_ADVANCED_ANALYZER = False
    except:
        USE_ADVANCED_ANALYZER = False
        def perform_analysis(*args, **kwargs):
            return {'success': False, 'error': 'المحلل غير متاح'}

# Settings
BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Database
subscription_manager = SubscriptionManager()

# Update tracking
LAST_UPDATE_FILE = "last_update.json"
ADMIN_FILE = "admin_users.json"

# Load admin users
def load_admin_users():
    """Load admin user IDs"""
    try:
        if os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return [7657829546]  # Default admin

ADMIN_USERS = load_admin_users()

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_USERS

def log_msg(msg):
    """Simple logging"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def load_last_update():
    """Load last update ID"""
    try:
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_update_id', 0)
    except:
        pass
    return 0


def save_last_update(update_id):
    """Save last update ID"""
    try:
        with open(LAST_UPDATE_FILE, 'w') as f:
            json.dump({'last_update_id': update_id}, f)
    except Exception as e:
        log_msg(f"[ERROR] Save update: {e}")


def send_message(chat_id, text):
    """Send message to user"""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    for attempt in range(1, 4):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200 and response.json().get('ok'):
                return True
            log_msg(f"[WARN] Send status: {response.status_code}")
        except Exception as e:
            log_msg(f"[ERROR] Send attempt {attempt}: {e}")
        time.sleep(min(2 * attempt, 6))
    return False


def send_broadcast_signal(signal_data, quality_score):
    """Send signal to eligible subscribers"""
    try:
        subscribers = subscription_manager.get_all_active_users()
        sent_count = 0
        
        log_msg(f"Broadcasting signal: {signal_data['symbol']} (Quality: {quality_score})")
        log_msg(f"Total subscribers: {len(subscribers)}")
        
        for user_data in subscribers:
            try:
                # Handle both dict and tuple formats
                if isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                    plan = user_data.get('plan', 'free')
                    target_chat_id = user_data.get('chat_id') or user_data.get('telegram_id') or user_id
                else:
                    user_id = user_data[0]
                    plan = user_data[1] if len(user_data) > 1 else 'free'
                    target_chat_id = user_id
                
                if not user_id:
                    continue
                
                # Get subscription info
                sub_info = subscription_manager.check_subscription(user_id)
                
                if not sub_info.get('is_active'):
                    log_msg(f"  -> User {user_id}: not active")
                    continue
                
                # Check if eligible
                threshold = get_quality_threshold_for_plan(plan)
                threshold_map = {'high': 75, 'medium': 50, 'low': 0}
                min_quality = threshold_map.get(threshold, 75)
                
                if quality_score >= min_quality:
                    message = format_signal(signal_data, quality_score, plan)
                    
                    if send_message(target_chat_id, message):
                        sent_count += 1
                        log_msg(f"  -> Sent to user {user_id} ({plan})")
                        time.sleep(0.5)
                    else:
                        log_msg(f"  -> Failed to send to {user_id}")
                else:
                    log_msg(f"  -> User {user_id}: quality too low ({min_quality} required)")
                    
            except Exception as e:
                log_msg(f"  -> Error with user: {e}")
                continue
        
        log_msg(f"Total sent: {sent_count}")
        return sent_count
        
    except Exception as e:
        log_msg(f"[ERROR] Broadcasting: {e}")
        return 0


def format_signal(signal, quality, plan):
    """Format signal message"""
    symbol = signal.get('symbol', 'N/A')
    rec = signal.get('rec', 'N/A')
    entry = signal.get('entry', 0)
    sl = signal.get('sl', 0)
    tp1 = signal.get('tp1', 0)
    tp2 = signal.get('tp2', 0)
    tp3 = signal.get('tp3', 0)
    tf = signal.get('tf', '1H')
    rr = signal.get('rr', 0)
    
    # Quality level
    if quality >= 75:
        q_text = "HIGH"
    elif quality >= 50:
        q_text = "MEDIUM"
    else:
        q_text = "LOW"
    
    msg = f"""
<b>{symbol}</b> | {tf}
Quality: {q_text} ({quality}/100)
Plan: {plan.upper()}

Recommendation: {rec}

Entry: {entry:.5f}
SL: {sl:.5f}
TP1: {tp1:.5f}
TP2: {tp2:.5f}
TP3: {tp3:.5f}

Risk/Reward: {rr:.2f}:1

Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    return msg


def get_start_message():
    """Start message"""
    return """
<b>Welcome to VIP Signals Bot</b>

Commands:
/start - Start
/plans - View plans
/subscribe - Subscribe (FREE trial)
/status - Your status
/analyze - Forex Analysis 📊
/referral - Referral link
/myid - Your Telegram ID
/help - Help

Send /subscribe to start!
"""


def handle_admin_command(chat_id, user_id, text):
    """Handle admin commands"""
    
    if text == '/admin':
        msg = """
<b>👨‍💼 لوحة تحكم الأدمن</b>

<b>📊 إحصائيات:</b>
/admin_stats - إحصائيات النظام

<b>👥 إدارة المستخدمين:</b>
/admin_users - قائمة المستخدمين
/admin_user USER_ID - تفاصيل مستخدم

<b>💎 إدارة الاشتراكات:</b>
/admin_upgrade USER_ID PLAN - ترقية مستخدم
/admin_extend USER_ID DAYS - تمديد اشتراك
/admin_cancel USER_ID - إلغاء اشتراك
/admin_reactivate USER_ID - إعادة تفعيل

<b>📤 البث:</b>
/admin_broadcast MESSAGE - بث رسالة
/admin_test USER_ID MESSAGE - اختبار رسالة

<b>الباقات المتاحة:</b>
free, bronze, silver, gold, platinum
"""
        send_message(chat_id, msg)
    
    elif text == '/admin_stats':
        try:
            all_subs = subscription_manager.get_all_subscriptions()
            active_count = len([s for s in all_subs if s['status'] in ['active', 'trial']])
            
            # Count by plan
            plan_counts = {}
            for sub in all_subs:
                plan = sub['plan']
                plan_counts[plan] = plan_counts.get(plan, 0) + 1
            
            msg = f"""
<b>📊 إحصائيات النظام</b>

<b>المستخدمون:</b>
• الإجمالي: {len(all_subs)}
• النشطون: {active_count}
• غير النشطين: {len(all_subs) - active_count}

<b>توزيع الباقات:</b>
"""
            for plan, count in plan_counts.items():
                msg += f"• {plan.upper()}: {count}\n"
            
            send_message(chat_id, msg)
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")
    
    elif text == '/admin_users':
        try:
            all_subs = subscription_manager.get_all_subscriptions()[:10]  # First 10
            
            msg = "<b>👥 المستخدمون (أول 10)</b>\n\n"
            for sub in all_subs:
                uid = sub['user_id']
                plan = sub['plan']
                status = sub['status']
                emoji = '✅' if status in ['active', 'trial'] else '❌'
                msg += f"{emoji} <code>{uid}</code> - {plan.upper()} ({status})\n"
            
            msg += f"\nالإجمالي: {len(all_subs)}"
            send_message(chat_id, msg)
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")
    
    elif text.startswith('/admin_user '):
        try:
            target_id = int(text.split()[1])
            user = subscription_manager.get_user(target_id)
            
            if user:
                sub_info = subscription_manager.check_subscription(target_id)
                stats = subscription_manager.get_user_stats(target_id)
                
                msg = f"""
<b>👤 معلومات المستخدم</b>

<b>ID:</b> <code>{user['user_id']}</code>
<b>Username:</b> {user.get('username', 'N/A')}
<b>الباقة:</b> {user['plan'].upper()}
<b>الحالة:</b> {user['status']}

<b>الاشتراك:</b>
• البداية: {user.get('subscription_start', 'N/A')[:10]}
• النهاية: {user.get('subscription_end', 'N/A')[:10]}
• الأيام المتبقية: {sub_info.get('days_left', 0)}

<b>الإحصائيات:</b>
• المدفوع: ${stats.get('total_paid', 0)}
• التوصيات: {stats.get('total_signals_received', 0)}
• الإحالات: {stats.get('referrals_count', 0)}

<b>كود الإحالة:</b> <code>{user.get('referral_code', 'N/A')}</code>
"""
                send_message(chat_id, msg)
            else:
                send_message(chat_id, "❌ المستخدم غير موجود")
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")
    
    elif text.startswith('/admin_upgrade'):
        try:
            parts = text.split()
            if len(parts) < 3:
                send_message(chat_id, "❌ صيغة خاطئة!\n\n📝 الصيغة الصحيحة:\n<code>/admin_upgrade USER_ID PLAN</code>\n\n💡 مثال:\n<code>/admin_upgrade 111111111 gold</code>\n\n📦 الباقات المتاحة:\nfree, bronze, silver, gold, platinum")
                return
            
            target_id = int(parts[1])
            plan = parts[2].lower()
            
            success, message = subscription_manager.update_subscription_plan(target_id, plan)
            
            if success:
                send_message(chat_id, f"✅ تم ترقية المستخدم {target_id} إلى {plan.upper()}")
                send_message(target_id, f"🎉 تم ترقية حسابك إلى {plan.upper()}!\n\nاستمتع بمزايا الباقة الجديدة")
            else:
                send_message(chat_id, f"❌ فشل: {message}")
        except ValueError:
            send_message(chat_id, "❌ خطأ: USER_ID يجب أن يكون رقم\n\n📝 الصيغة:\n<code>/admin_upgrade USER_ID PLAN</code>")
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")
    
    elif text.startswith('/admin_extend'):
        try:
            parts = text.split()
            if len(parts) < 3:
                send_message(chat_id, "❌ صيغة خاطئة!\n\n📝 الصيغة الصحيحة:\n<code>/admin_extend USER_ID DAYS</code>\n\n💡 مثال:\n<code>/admin_extend 111111111 30</code>")
                return
            
            target_id = int(parts[1])
            days = int(parts[2])
            
            success, message = subscription_manager.extend_subscription(target_id, days)
            
            if success:
                send_message(chat_id, f"✅ تم تمديد اشتراك {target_id} لـ {days} يوم")
                send_message(target_id, f"🎁 تم تمديد اشتراكك لـ {days} يوم!")
            else:
                send_message(chat_id, f"❌ فشل: {message}")
        except ValueError:
            send_message(chat_id, "❌ خطأ: USER_ID و DAYS يجب أن تكون أرقام\n\n📝 الصيغة:\n<code>/admin_extend USER_ID DAYS</code>")
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")
    
    elif text.startswith('/admin_cancel '):
        try:
            target_id = int(text.split()[1])
            success, message = subscription_manager.cancel_subscription(target_id)
            
            if success:
                send_message(chat_id, f"✅ تم إلغاء اشتراك {target_id}")
                send_message(target_id, "⚠️ تم إلغاء اشتراكك\nللمساعدة: /help")
            else:
                send_message(chat_id, f"❌ فشل: {message}")
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}\nالصيغة: /admin_cancel USER_ID")
    
    elif text.startswith('/admin_reactivate'):
        try:
            parts = text.split()
            if len(parts) < 2:
                send_message(chat_id, "❌ صيغة خاطئة!\n\n📝 الصيغة الصحيحة:\n<code>/admin_reactivate USER_ID</code>\n\n💡 مثال:\n<code>/admin_reactivate 111111111</code>")
                return
            
            target_id = int(parts[1])
            success, message = subscription_manager.reactivate_subscription(target_id)
            
            if success:
                send_message(chat_id, f"✅ تم إعادة تفعيل اشتراك {target_id}")
                send_message(target_id, "🎉 تم إعادة تفعيل اشتراكك!\nمرحباً بك مجدداً")
            else:
                send_message(chat_id, f"❌ فشل: {message}")
        except ValueError:
            send_message(chat_id, "❌ خطأ: USER_ID يجب أن يكون رقم\n\n📝 الصيغة:\n<code>/admin_reactivate USER_ID</code>")
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")
    
    elif text.startswith('/admin_broadcast'):
        try:
            parts = text.split(None, 1)  # Split into command and message
            if len(parts) < 2:
                send_message(chat_id, "❌ صيغة خاطئة!\n\n📝 الصيغة الصحيحة:\n<code>/admin_broadcast رسالتك هنا</code>\n\n💡 مثال:\n<code>/admin_broadcast مرحباً بالجميع!</code>")
                return
            
            broadcast_msg = parts[1]
            
            if len(broadcast_msg) < 5:
                send_message(chat_id, "❌ الرسالة قصيرة جداً (الحد الأدنى 5 أحرف)")
                return
            
            send_message(chat_id, "📤 جاري البث...")
            
            all_subs = subscription_manager.get_all_active_users()
            sent = 0
            failed = 0
            
            for user_data in all_subs:
                try:
                    if isinstance(user_data, dict):
                        target_id = user_data.get('user_id')
                    else:
                        target_id = user_data[0]
                    
                    if send_message(target_id, f"📢 <b>رسالة من الإدارة</b>\n\n{broadcast_msg}"):
                        sent += 1
                    else:
                        failed += 1
                    
                    time.sleep(0.05)  # Rate limiting
                except:
                    failed += 1
            
            send_message(chat_id, f"✅ تم البث!\n\nأُرسلت: {sent}\nفشلت: {failed}")
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")
    
    elif text.startswith('/admin_test'):
        try:
            parts = text.split(None, 2)
            if len(parts) < 3:
                send_message(chat_id, "❌ صيغة خاطئة!\n\n📝 الصيغة الصحيحة:\n<code>/admin_test USER_ID رسالتك</code>\n\n💡 مثال:\n<code>/admin_test 111111111 اختبار البوت</code>")
                return
            
            target_id = int(parts[1])
            test_msg = parts[2]
            
            if send_message(target_id, f"🧪 <b>رسالة اختبار</b>\n\n{test_msg}"):
                send_message(chat_id, f"✅ تم إرسال الرسالة إلى {target_id}")
            else:
                send_message(chat_id, f"❌ فشل الإرسال إلى {target_id}")
        except ValueError:
            send_message(chat_id, "❌ خطأ: USER_ID يجب أن يكون رقم\n\n📝 الصيغة:\n<code>/admin_test USER_ID رسالتك</code>")
        except Exception as e:
            send_message(chat_id, f"❌ خطأ: {e}")



def handle_message(chat_id, text):
    """Handle user message"""
    user_id = chat_id
    
    # ====== أوامر الأدمن - أولاً ======
    if is_admin(user_id) and text.startswith('/admin'):
        handle_admin_command(chat_id, user_id, text)
        return
    
    # ====== الأوامر العادية ======
    if text == '/start':
        msg = get_start_message()
        send_message(chat_id, msg)
        
    elif text == '/subscribe':
        sub_info = subscription_manager.check_subscription(user_id)
        
        if sub_info.get('exists'):
            response = "Already subscribed!\n/status for details"
        else:
            success = subscription_manager.add_user(user_id, f"user_{user_id}")
            if success:
                response = "Success! Account created.\nYou are now subscribed.\n\nWait for signals..."
            else:
                response = "Error subscribing"
        
        send_message(chat_id, response)
        
    elif text == '/status':
        sub_info = subscription_manager.check_subscription(user_id)
        
        if not sub_info.get('exists'):
            response = "Not subscribed\n/subscribe to start"
        else:
            plan = sub_info.get('plan', 'unknown')
            days_left = sub_info.get('days_left', 0)
            response = f"Plan: {plan.upper()}\nDays left: {days_left}"
        
        send_message(chat_id, response)
        
    elif text == '/help':
        msg = """
<b>📞 معلومات الدعم</b>

<b>📧 البريد الإلكتروني:</b>
MAHMOODALQAISE750@GMAIL.COM

<b>💬 التيليجرام:</b>
@abo_hashim1983

<b>الأوامر المتاحة:</b>
/start - رسالة الترحيب
/subscribe - اشترك مجاني
/status - حالة حسابك
/plans - الباقات المتاحة
/analyze - تحليل العملات 📊
/referral - كود الإحالة
/myid - معرفة الآيدي الخاص بك

<b>Need help?</b>
Contact support via:
📧 Email: MAHMOODALQAISE750@GMAIL.COM
💬 Telegram: @abo_hashim1983
"""
        send_message(chat_id, msg)

    elif text in ['/myid', '/id']:
        send_message(chat_id, f"✅ الآيدي الخاص بك هو:\n<code>{chat_id}</code>")
    
    elif text == '/support':
        msg = """
<b>🆘 الدعم الفني</b>

<b>معلومات التواصل:</b>

📧 <b>البريد الإلكتروني:</b>
<code>MAHMOODALQAISE750@GMAIL.COM</code>

💬 <b>تيليجرام:</b>
<code>@abo_hashim1983</code>

📞 <b>ساعات الدعم:</b>
24/7 - متاح طوال الوقت

<b>يمكنك التواصل معنا لـ:</b>
✅ المشاكل الفنية
✅ الاستفسارات
✅ الشكاوى والاقتراحات
✅ طلب المساعدة

نحن هنا لمساعدتك! 🙌
"""
        send_message(chat_id, msg)
    
    elif text == '/analyze':
        # Show analysis menu
        msg = """
<b>📊 Forex Analyzer</b>

Select pair to analyze:
/analyze_eurusd - EUR/USD
/analyze_gbpusd - GBP/USD
/analyze_usdjpy - USD/JPY
/analyze_xauusd - Gold (XAU/USD)
/analyze_btcusd - Bitcoin

Or use: /analyze SYMBOL
Example: /analyze EUR/USD
"""
        send_message(chat_id, msg)
    
    elif text.startswith('/analyze_') or (text.startswith('/analyze ') and len(text) > 9):
        # Extract symbol
        if text.startswith('/analyze_'):
            symbol_map = {
                'eurusd': 'EURUSD',
                'gbpusd': 'GBPUSD',
                'usdjpy': 'USDJPY',
                'xauusd': 'XAUUSD',
                'btcusd': 'BTCUSD'
            }
            cmd = text[9:].lower()
            symbol = symbol_map.get(cmd, 'EURUSD')
        else:
            symbol = text[9:].strip().upper().replace('/', '')
        
        # Send processing message
        send_message(chat_id, f"🔄 جاري تحليل {symbol}...\nالرجاء الانتظار...")
        
        try:
            if USE_ADVANCED_ANALYZER:
                # استخدام المحلل المتقدم
                result = full_analysis(symbol, '1d')
                
                if result and result.get('success'):
                    consensus = result.get('consensus', 'HOLD')
                    consensus_strength = result.get('consensus_strength', 0)
                    current_price = result.get('current_price', 0)
                    strategies = result.get('strategies', {})
                    
                    # رموز تعبيرية للإجماع
                    emoji_map = {
                        'BUY': '🟢',
                        'STRONG_BUY': '🟩',
                        'SELL': '🔴',
                        'STRONG_SELL': '🟥',
                        'HOLD': '⚪'
                    }
                    consensus_emoji = emoji_map.get(consensus, '⚪')
                    
                    # Format message
                    msg = f"""
<b>📊 تحليل {symbol}</b>
<b>الإطار الزمني:</b> يومي (1D)

━━━━━━━━━━━━━━━━━━━━
<b>🎯 الإجماع: {consensus_emoji} {consensus}</b>
<b>القوة:</b> {consensus_strength}%
<b>💰 السعر الحالي:</b> {current_price:.5f}

<b>📊 نتائج الاستراتيجيات:</b>
"""
                    # إضافة نتائج الاستراتيجيات
                    for strategy_name, strategy_result in strategies.items():
                        signal = strategy_result.get('signal', 'hold').upper()
                        confidence = strategy_result.get('confidence', 0)
                        
                        if signal == 'BUY':
                            emoji = '🟢'
                        elif signal == 'SELL':
                            emoji = '🔴'
                        else:
                            emoji = '⚪'
                        
                        msg += f"{emoji} {strategy_name}: {signal} ({confidence}%)\n"
                    
                    msg += f"""
━━━━━━━━━━━━━━━━━━━━
<b>المزيد من التحليلات:</b>
/analyze - اختر زوج
/status - اشتراكك

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
                    send_message(chat_id, msg)
                else:
                    send_message(chat_id, f"❌ خطأ في التحليل")
            else:
                # استخدام المحلل القديم
                result = perform_analysis(symbol, '1h', 'Harmonic')
                
                if result.get('success'):
                    # Format message (old format)
                    msg = f"""
<b>📊 {symbol} Analysis</b>
<b>Strategy:</b> Harmonic Patterns
<b>Timeframe:</b> 1 Hour

━━━━━━━━━━━━━━━━━━━━
<b>🎯 Signals:</b>
{result.get('signal', 'N/A')}

<b>💰 Trade Setup:</b>
Entry: {result.get('entry_point', 0):.5f}
TP1: {result.get('take_profit1', 0):.5f}
TP2: {result.get('take_profit2', 0):.5f}
TP3: {result.get('take_profit3', 0):.5f}
Stop Loss: {result.get('stop_loss', 0):.5f}

<b>📈 Key Levels:</b>
Support: {result.get('support', 0):.5f}
Pivot: {result.get('pivot', 0):.5f}
Resistance: {result.get('resistance', 0):.5f}

━━━━━━━━━━━━━━━━━━━━
/analyze - Choose pair
/status - Your plan

Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
                    send_message(chat_id, msg)
                else:
                    send_message(chat_id, f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            log_msg(f"[ERROR] Analysis exception: {e}")
            import traceback
            traceback.print_exc()
            send_message(chat_id, f"❌ فشل التحليل: {str(e)}")
    
    elif text == '/plans':
        msg = """
<b>💎 الباقات المتاحة</b>

🆓 <b>FREE</b> - 0$
• 1 توصية يومية
• جودة عالية فقط

🥉 <b>BRONZE</b> - 29$/شهر
• 3 توصيات يومية
• جودة عالية ومتوسطة
• دعم فني

🥈 <b>SILVER</b> - 69$/3 أشهر
• 5 توصيات يومية
• جميع الجودات
• دعم فني أولوية
• تحليلات مجانية

🥇 <b>GOLD</b> - 199$/سنة
• 7 توصيات يومية
• جميع الجودات
• دعم VIP 24/7
• تحليلات غير محدودة
• إشارات حصرية

💎 <b>PLATINUM</b> - 499$/سنة
• 10 توصيات يومية
• جميع الجودات
• دعم VIP 24/7
• تحليلات غير محدودة
• إشارات حصرية + استشارات

للترقية: /upgrade
"""
        send_message(chat_id, msg)
    
    elif text == '/referral':
        sub_info = subscription_manager.check_subscription(user_id)
        
        if not sub_info.get('exists'):
            send_message(chat_id, "اشترك أولاً\n/subscribe")
        else:
            ref_code = sub_info.get('referral_code', 'N/A')
            msg = f"""
<b>🎁 برنامج الإحالة</b>

كود الإحالة الخاص بك:
<code>{ref_code}</code>

🎯 <b>كيف يعمل؟</b>
• شارك كودك مع أصدقائك
• عندما يشتركون: تحصل على 30 يوم مجاني!
• لا حدود للإحالات

رابط الدعوة:
https://t.me/{BOT_TOKEN.split(':')[0]}?start={ref_code}
"""
            send_message(chat_id, msg)
    
    elif text == '/upgrade':
        msg = """
<b>💳 الترقية للباقة المدفوعة</b>

للترقية، تواصل مع الدعم:
📧 support@goldpro.com
📱 Telegram: @ADMIN

طرق الدفع:
• بطاقة ائتمان
• PayPal
• تحويل بنكي
• عملات رقمية
"""
        send_message(chat_id, msg)
    
    elif text == '/status':
        sub_info = subscription_manager.check_subscription(user_id)
        
        if not sub_info.get('exists'):
            response = "Not subscribed\n/subscribe to start"
        else:
            plan = sub_info.get('plan', 'unknown')
            days_left = sub_info.get('days_left', 0)
            response = f"Plan: {plan.upper()}\nDays left: {days_left}"
        
        send_message(chat_id, response)


def process_update(update):
    try:
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            if text:
                log_msg(f"Message from {chat_id}: {text}")
                handle_message(chat_id, text)
                
    except Exception as e:
        log_msg(f"[ERROR] Process: {e}")


def run_bot():
    """Run the bot"""
    log_msg("=== VIP Bot Started ===")
    log_msg(f"Token: {BOT_TOKEN[:20]}...")
    
    last_update_id = load_last_update()
    backoff = 5
    max_backoff = 60
    
    while True:
        try:
            url = f"{BASE_URL}/getUpdates"
            params = {'offset': last_update_id + 1, 'timeout': 30}
            
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
                        log_msg(f"Processed {len(updates)} updates")
                backoff = 5
            else:
                log_msg(f"[ERROR] Status: {response.status_code}")
                time.sleep(5)
                
        except requests.exceptions.Timeout:
            log_msg("Timeout - retrying...")
            continue
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            log_msg(f"Connection error - retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
            continue
            
        except Exception as e:
            log_msg(f"[ERROR] {e}")
            time.sleep(5)


if __name__ == "__main__":
    log_msg("VIP Bot - Simple Version")
    try:
        run_bot()
    except KeyboardInterrupt:
        log_msg("Bot stopped by user")

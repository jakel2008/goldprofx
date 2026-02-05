"""
نظام التحليل التلقائي الشامل لجميع الأزواج
يقوم بتحليل جميع الأزواج مرة واحدة في اليوم وإرسال التقارير إلى البوت
مع دعم نظام VIP
"""

import requests
import pandas as pd
import ta
from datetime import datetime, date
import os
import yfinance as yf
import json
from vip_subscription_system import SubscriptionManager
from quality_scorer import add_quality_score, filter_signals_by_quality, get_quality_threshold_for_plan

# استيراد المزامنة الموحدة
try:
    from unified_signal_manager import UnifiedSignalManager
    UNIFIED_SYSTEM_AVAILABLE = True
except:
    UNIFIED_SYSTEM_AVAILABLE = False
    print("⚠️  تحذير: نظام المزامنة الموحد غير متوفر")

# إعدادات البوت
TELEGRAM_BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
TELEGRAM_CHAT_ID = os.environ.get("MM_TELEGRAM_CHAT_ID", "7657829546")

# مدير الاشتراكات للبث للجميع
subscription_manager = SubscriptionManager()

# ملف تخزين الصفقات النشطة
ACTIVE_TRADES_FILE = "active_trades.json"
# ملف أرشفة الصفقات المنتهية
CLOSED_TRADES_FILE = "closed_trades.json"

# مجلد حفظ الإشارات للبث
SIGNALS_DIR = "signals"
if not os.path.exists(SIGNALS_DIR):
    os.makedirs(SIGNALS_DIR)

# قائمة الأزواج المراد تحليلها - تحليل عميق كل 5 دقائق
# أولوية التركيز: الذهب/الفضة/النفط/المؤشرات الأمريكية دون إغفال باقي الأزواج
PRIORITY_PAIRS = [
    ('XAUUSD', '5m'),  # الذهب
    ('XAGUSD', '5m'),  # الفضة
    ('CRUDE', '5m'),   # النفط الخام
    ('BRENT', '5m'),   # نفط برنت
    ('NATGAS', '5m'),  # الغاز الطبيعي
    ('SPX', '5m'),     # S&P 500
    ('DJI', '5m'),     # Dow Jones
    ('NDX', '5m'),     # NASDAQ 100
    ('RUT', '5m'),     # Russell 2000
]

OTHER_PAIRS = [
    # العملات الرئيسية
    ('EURUSD', '5m'),
    ('GBPUSD', '5m'),
    ('USDJPY', '5m'),
    ('AUDUSD', '5m'),
    ('USDCAD', '5m'),
    ('NZDUSD', '5m'),
    ('USDCHF', '5m'),

    # العملات الرقمية
    ('BTCUSD', '5m'),
    ('ETHUSD', '5m'),  # Ethereum
    ('XRPUSD', '5m'),  # Ripple
    ('ADAUSD', '5m'),  # Cardano
    ('SOLUSD', '5m'),  # Solana
    ('DOGEUSD', '5m'), # Dogecoin
]

# دمج القوائم مع إزالة التكرارات مع الحفاظ على أولوية الترتيب
_seen_pairs = set()
PAIRS_TO_ANALYZE = []
for _pair in PRIORITY_PAIRS + OTHER_PAIRS:
    if _pair[0] in _seen_pairs:
        continue
    _seen_pairs.add(_pair[0])
    PAIRS_TO_ANALYZE.append(_pair)

# خرائط رموز Yahoo Finance للأزواج
YF_TICKERS = {
    # العملات الرئيسية
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'NZDUSD': 'NZDUSD=X',
    'USDCHF': 'USDCHF=X',
    
    # المعادن الثمينة
    'XAUUSD': 'GC=F',   # Gold Futures
    'XAGUSD': 'SLV',    # iShares Silver Trust ETF
    
    # الطاقة
    'CRUDE': 'USO',     # United States Oil Fund ETF
    'BRENT': 'BNO',     # United States Brent Oil Fund ETF
    'NATGAS': 'UNG',    # United States Natural Gas Fund ETF
    
    # المؤشرات الأمريكية
    'SPX': '^GSPC',     # S&P 500
    'DJI': '^DJI',      # Dow Jones Industrial Average
    'NDX': '^NDX',      # NASDAQ 100
    'RUT': '^RUT',      # Russell 2000
    
    # العملات الرقمية
    'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD',  # Ethereum
    'XRPUSD': 'XRP-USD',  # Ripple
    'ADAUSD': 'ADA-USD',  # Cardano
    'SOLUSD': 'SOL-USD',  # Solana
    'DOGEUSD': 'DOGE-USD', # Dogecoin
}

# متغيرات الجدولة
last_auto_analysis_date = None
auto_analysis_results = {}


def send_telegram_message(text, parse_mode='Markdown'):
    """إرسال رسالة إلى البوت بتنسيق محسّن"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"❌ خطأ: لم يتم ضبط التوكن")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200 and response.json().get("ok"):
            print(f"✅ تم إرسال الرسالة بنجاح")
            return True
        print(f"❌ فشل الإرسال: {response.text}")
        return False
    except Exception as e:
        print(f"❌ خطأ في الإرسال: {str(e)}")
        return False


def send_broadcast_message(text, parse_mode='HTML'):
    """إرسال رسالة لكل المشتركين النشطين"""
    if not TELEGRAM_BOT_TOKEN:
        return 0

    try:
        users = subscription_manager.get_all_active_users()
    except Exception:
        users = []

    sent = 0
    for user in users:
        chat_id = None
        if isinstance(user, dict):
            chat_id = user.get('chat_id') or user.get('telegram_id') or user.get('user_id')
        else:
            chat_id = user[0] if len(user) > 0 else None

        try:
            chat_id = int(str(chat_id).strip())
        except Exception:
            continue

        if chat_id <= 0:
            continue

        try:
            payload = {"chat_id": chat_id, "text": text}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json=payload,
                timeout=10
            )
            if response.status_code == 200 and response.json().get("ok"):
                sent += 1
        except Exception:
            continue

    return sent


def fetch_pair_data(symbol, interval='1h', limit=100):
    """جلب بيانات الزوج من API"""
    try:
        # استخدام Binance API كمثال
        if 'BTC' in symbol or 'ETH' in symbol:
            api_url = f"https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol.replace('/', ''),
                'interval': interval,
                'limit': limit
            }
        else:
            # للفوركس استخدم API آخر
            return None
        
        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'ctime', 'qav', 'num_trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'])
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['open'] = pd.to_numeric(df['open'])
            df['volume'] = pd.to_numeric(df['volume'])
            return df
        return None
    except:
        return None


def fetch_pair_data_5m(symbol, period='1d'):
    """جلب بيانات 5 دقائق عبر Yahoo Finance مع بدائل"""
    try:
        ticker = YF_TICKERS.get(symbol)
        if not ticker:
            return None

        attempts = [
            ('5m', period),
            ('5m', '5d'),
            ('15m', '5d'),
            ('30m', '5d'),
            ('60m', '1mo')
        ]

        df = None
        for interval, per in attempts:
            df = yf.download(ticker, interval=interval, period=per, progress=False, auto_adjust=False)
            if df is not None and not df.empty:
                break

        if df is None or df.empty:
            # fallback عبر history
            try:
                ticker_obj = yf.Ticker(ticker)
                df = ticker_obj.history(period='7d', interval='15m', auto_adjust=False)
            except Exception:
                df = None
            send_broadcast_message(notification)
        if df is None or df.empty:
            return None
        
        # تحويل MultiIndex إلى columns عادية إن وجد
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        
        # تسمية الأعمدة بشكل صحيح
        column_mapping = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        df = df.rename(columns=column_mapping)
        
        # التأكد من أن الأعمدة Series وليست DataFrame
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].squeeze(), errors='coerce')
        
        df = df.dropna()
        df = df.reset_index()
        return df
    except Exception as e:
        print(f"خطأ في جلب {symbol}: {e}")
        return None


def analyze_pair(symbol, interval):
    """تحليل زوج واحد"""
    df = fetch_pair_data(symbol, interval)
    if df is None or len(df) < 14:
        return None
    
    # حساب المؤشرات
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD'] = ta.trend.macd_diff(df['close'])
    
    # حساب البولنجر باند (محذوف في هذا الإصدار)
    
    # تحديد التوصية
    close_price = float(df['close'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    macd = float(df['MACD'].iloc[-1])
    
    signals = []
    
    if rsi > 70:
        signals.append("بيع - RSI مرتفع جداً")
        if macd < 0:
            recommendation = "بيع قوي"
        else:
            recommendation = "بيع"
    elif rsi < 30:
        signals.append("شراء - RSI منخفض جداً")
        if macd > 0:
            recommendation = "شراء قوي"
        else:
            recommendation = "شراء"
    elif macd > 0:
        recommendation = "شراء"
    elif macd < 0:
        recommendation = "بيع"
    else:
        recommendation = "حياد"
    
    return {
        'symbol': symbol,
        'interval': interval,
        'close_price': close_price,
        'rsi': rsi,
        'macd': macd,
        'recommendation': recommendation,
        'signals': signals,
        'timestamp': datetime.now()
    }


def analyze_pair_5m(symbol):
    """تحليل زوج واحد على فريم 5 دقائق - محسّن"""
    df = fetch_pair_data_5m(symbol, period='2d')  # زيادة البيانات للتحليل الأفضل
    if df is None or len(df) < 30:  # تخفيف الحد الأدنى لزيادة التغطية
        return None

    try:
        # مؤشرات 5 دقائق - التأكد من أن البيانات Series
        close_series = df['close'].squeeze()
        high_series = df['high'].squeeze()
        low_series = df['low'].squeeze()
        volume_series = df['volume'].squeeze() if 'volume' in df.columns else None
        
        # المؤشرات الأساسية
        df['RSI'] = ta.momentum.rsi(close_series, window=14)
        df['MACD'] = ta.trend.macd_diff(close_series)
        df['MACD_signal'] = ta.trend.macd_signal(close_series)
        
        # إضافة EMA لتحديد الاتجاه
        df['EMA_20'] = ta.trend.ema_indicator(close_series, window=20)
        df['EMA_50'] = ta.trend.ema_indicator(close_series, window=50)

        close_price = float(df['close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        macd = float(df['MACD'].iloc[-1])
        macd_signal = float(df['MACD_signal'].iloc[-1])
        ema_20 = float(df['EMA_20'].iloc[-1])
        ema_50 = float(df['EMA_50'].iloc[-1])
        
        # حساب ATR للـ Stop Loss و Take Profit (محسّن)
        atr = ta.volatility.average_true_range(high_series, low_series, close_series, window=14)
        current_atr = float(atr.iloc[-1]) if not atr.empty else close_price * 0.003
        
        # حساب مستويات الدعم والمقاومة من آخر 30 شمعة
        recent_high = float(high_series.tail(30).max())
        recent_low = float(low_series.tail(30).min())
        
        # تحديد الاتجاه العام
        trend = "صاعد" if ema_20 > ema_50 else "هابط"
        trend_strength = abs(ema_20 - ema_50) / close_price * 100  # قوة الاتجاه %
        
    except Exception as e:
        print(f"خطأ في تحليل {symbol}: {e}")
        return None

    signals = []
    entry_price = None
    stop_loss = None
    take_profit = None
    take_profit_2 = None
    take_profit_3 = None
    recommendation = "حياد"
    
    # شروط دخول محسّنة وأكثر صرامة
    buy_signal = False
    sell_signal = False
    strong_signal = False
    medium_signal = False
    
    # شرط البيع القوي (تحليل عميق - فلاتر متعددة)
    if (rsi > 68 and  # RSI مرتفع
        macd < 0 and
        macd < macd_signal and  # تأكيد MACD crossover
        close_price > ema_20 and  # السعر فوق EMA (overbought)
        close_price > ema_50 and  # تأكيد إضافي
        trend_strength > 0.15):  # اتجاه واضح

        signals.append("🔴 بيع قوي - RSI مرتفع + MACD هابط + اتجاه واضح + تأكيد مضاعف")
        sell_signal = True
        strong_signal = True
        recommendation = "بيع"

    # شرط الشراء القوي (تحليل عميق - فلاتر متعددة)
    elif (rsi < 32 and  # RSI منخفض
          macd > 0 and
          macd > macd_signal and  # تأكيد MACD crossover
          close_price < ema_20 and  # السعر تحت EMA (oversold)
          close_price < ema_50 and  # تأكيد إضافي
          trend_strength > 0.15):  # اتجاه واضح

        signals.append("🟢 شراء قوي - RSI منخفض + MACD صاعد + اتجاه واضح + تأكيد مضاعف")
        buy_signal = True
        strong_signal = True
        recommendation = "شراء"
    
    # شروط متوسطة (تحليل 5 دقائق - بفلاتر إضافية)
    elif (rsi > 55 and rsi < 68 and
          macd < 0 and
          macd < macd_signal and  # تأكيد MACD
          trend == "هابط" and
          close_price > ema_50):
        
        signals.append("🟡 بيع - RSI مرتفع + اتجاه هابط + MACD متأكد")
        sell_signal = True
        medium_signal = True
        recommendation = "بيع"
        
    elif (rsi < 45 and rsi > 32 and
          macd > 0 and
          macd > macd_signal and  # تأكيد MACD
          trend == "صاعد" and
          close_price < ema_50):
        
        signals.append("🟡 شراء - RSI منخفض + اتجاه صاعد + MACD متأكد")
        buy_signal = True
        medium_signal = True
        recommendation = "شراء"
    
    # إشارات اتجاهية إضافية عند غياب الشروط القوية
    if not buy_signal and not sell_signal:
        if trend == "صاعد" and macd > 0 and 45 <= rsi <= 65 and trend_strength > 0.2:
            signals.append("🟢 شراء اتجاهي - EMA صاعد + MACD موجب")
            buy_signal = True
            medium_signal = True
            recommendation = "شراء"
        elif trend == "هابط" and macd < 0 and 35 <= rsi <= 55 and trend_strength > 0.2:
            signals.append("🔴 بيع اتجاهي - EMA هابط + MACD سالب")
            sell_signal = True
            medium_signal = True
            recommendation = "بيع"

    # حساب مناطق التداول بـ RR ratio محسّن
    if buy_signal:
        entry_price = close_price
        # Stop Loss أضيق (1.2 ATR بدلاً من 1.5)
        stop_loss = close_price - (current_atr * 1.2)
        
        # Take Profits بنسب أفضل لتحقيق RR >= 2:1
        take_profit = close_price + (current_atr * 2.5)   # TP1 على 2.5 ATR (RR 2:1)
        take_profit_2 = close_price + (current_atr * 4.0) # TP2 على 4.0 ATR (RR 3.3:1)
        take_profit_3 = close_price + (current_atr * 5.5) # TP3 على 5.5 ATR (RR 4.6:1)
        
        # التحقق من أن TP1 ممكن (تخفيف الشرط)
        if take_profit > recent_high * 1.05:
            take_profit = recent_high * 1.05
            
    elif sell_signal:
        entry_price = close_price
        # Stop Loss أضيق (1.2 ATR بدلاً من 1.5)
        stop_loss = close_price + (current_atr * 1.2)
        
        # Take Profits بنسب أفضل لتحقيق RR >= 2:1
        take_profit = close_price - (current_atr * 2.5)   # TP1 على 2.5 ATR (RR 2:1)
        take_profit_2 = close_price - (current_atr * 4.0) # TP2 على 4.0 ATR (RR 3.3:1)
        take_profit_3 = close_price - (current_atr * 5.5) # TP3 على 5.5 ATR (RR 4.6:1)
        
        # التحقق من أن TP1 ممكن (تخفيف الشرط)
        if take_profit < recent_low * 0.95:
            take_profit = recent_low * 0.95
    
    # إذا لم تتحقق الشروط القوية، لا توصية
    if not buy_signal and not sell_signal:
        return None

    # حساب الجودة
    quality_score = 60
    if strong_signal:
        quality_score = 85
    elif medium_signal:
        quality_score = 75

    # حساب RR
    rr_ratio = 0
    if entry_price and stop_loss and take_profit:
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0

    return {
        'symbol': symbol,
        'interval': '5min',
        'close_price': close_price,
        'current_price': close_price,
        'rsi': rsi,
        'macd': macd,
        'recommendation': recommendation,
        'signals': signals,
        'entry': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'take_profit_2': take_profit_2,
        'take_profit_3': take_profit_3,
        'atr': current_atr,
        'support': recent_low,
        'resistance': recent_high,
        'trend': trend,
        'ema_20': ema_20,
        'ema_50': ema_50,
        'quality_score': quality_score,
        'rr_ratio': rr_ratio,
        'timestamp': datetime.now()
    }


def generate_pair_report(analysis):
    """إنشاء تقرير تفصيلي لزوج واحد مع 3 مستويات لأخذ الربح"""
    if not analysis:
        return None
    
    # تحديد emoji حسب نوع التوصية
    rec_emoji = "🔼" if "شراء" in analysis['recommendation'] else "🔽" if "بيع" in analysis['recommendation'] else "⏸️"
    
    report = f"""
{'='*50}
🚨 <b>إشارة تداول جديدة</b> 🚨
{'='*50}

📊 <b>الزوج / الأصل:</b> {analysis['symbol']}
⏱️ <b>الإطار الزمني:</b> {analysis['interval']}

💰 <b>السعر الحالي:</b> {analysis['close_price']:.5f}

{rec_emoji} <b>التوصية: {analysis['recommendation']}</b> {rec_emoji}
"""
    
    # إضافة مناطق التداول إذا كانت موجودة
    if analysis.get('entry') and analysis['recommendation'] != 'حياد':
        # حساب Risk/Reward Ratio
        entry = analysis['entry']
        sl = analysis['stop_loss']
        tp1 = analysis['take_profit']
        
        risk = abs(entry - sl)
        reward = abs(tp1 - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        
        report += f"""
{'─'*50}
<b>📍 خطة التداول:</b>

🟢 <b>نقطة الدخول:</b> {analysis['entry']:.5f}

🔴 <b>وقف الخسارة (SL):</b> {analysis['stop_loss']:.5f}
   المخاطرة: {risk:.5f} نقطة

💚 <b>أهداف الربح:</b>
   🎯 TP1: {analysis['take_profit']:.5f}
   🎯 TP2: {analysis['take_profit_2']:.5f}
   🎯 TP3: {analysis['take_profit_3']:.5f}

⚖️ <b>نسبة المخاطرة/العائد:</b> 1:{rr_ratio:.2f}

{'─'*50}
<b>📈 التحليل الفني:</b>

RSI: {analysis['rsi']:.2f}
MACD: {analysis['macd']:.5f}
الدعم: {analysis.get('support', 0):.5f}
المقاومة: {analysis.get('resistance', 0):.5f}
ATR: {analysis.get('atr', 0):.5f}
"""
    else:
        report += f"""
{'─'*50}
📈 <b>المؤشرات الفنية:</b>

RSI: {analysis['rsi']:.2f}
MACD: {analysis['macd']:.5f}
"""
    
    if analysis['signals']:
        report += f"\n{'─'*50}\n⚡ <b>الإشارات:</b>\n"
        for signal in analysis['signals']:
            report += f"   • {signal}\n"
    
    report += f"\n{'─'*50}\n🕐 الوقت: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}"
    
    return report


def load_active_trades():
    """تحميل الصفقات النشطة من الملف"""
    try:
        if os.path.exists(ACTIVE_TRADES_FILE):
            with open(ACTIVE_TRADES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                # إذا كان ملف قديم بشكل قائمة، تجاهله وأعد قاموس فارغ
                return {}
        return {}
    except Exception as e:
        print(f"خطأ في تحميل الصفقات: {e}")
        return {}


def save_active_trades(trades):
    """حفظ الصفقات النشطة في الملف"""
    try:
        with open(ACTIVE_TRADES_FILE, 'w', encoding='utf-8') as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطأ في حفظ الصفقات: {e}")


def load_closed_trades():
    """تحميل أرشيف الصفقات المنتهية"""
    try:
        if os.path.exists(CLOSED_TRADES_FILE):
            with open(CLOSED_TRADES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        return []
    except Exception as e:
        print(f"خطأ في تحميل الأرشيف: {e}")
        return []


def save_closed_trades(trades):
    """حفظ أرشيف الصفقات المنتهية"""
    try:
        with open(CLOSED_TRADES_FILE, 'w', encoding='utf-8') as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطأ في حفظ الأرشيف: {e}")


def save_signal_for_broadcast(symbol, recommendation, entry, stop_loss, take_profit, take_profit_2=None, take_profit_3=None, timeframe='5m', quality_score=None, rr_ratio=None):
    """حفظ الإشارة باستخدام النظام الموحد (ويب + بوت)"""
    if recommendation == 'حياد' or not entry:
        return None
    
    # تحديد نوع الإشارة
    rec_type = 'BUY' if 'شراء' in recommendation else 'SELL'
    
    # بناء بيانات الإشارة
    # حساب RR بسيط
    if rr_ratio is None:
        rr_ratio = 0
        try:
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
            rr_ratio = reward / risk if risk > 0 else 0
        except Exception:
            rr_ratio = 0

    if quality_score is None:
        quality_score = 75 if 'قوي' in recommendation else 70

    signal_data = {
        'symbol': symbol,
        'rec': rec_type,
        'entry': entry,
        'sl': stop_loss,
        'tp1': take_profit,
        'tp2': take_profit_2,
        'tp3': take_profit_3,
        'tf': timeframe,
        'timestamp': datetime.now().isoformat(),
        'recommendation': recommendation,
        'quality_score': quality_score,
        'rr': rr_ratio
    }
    
    signal_id = f"{symbol}_{rec_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # استخدام النظام الموحد إذا كان متوفراً
    if UNIFIED_SYSTEM_AVAILABLE:
        try:
            unified_manager = UnifiedSignalManager()
            report = unified_manager.publish_signal(signal_data)
            
            print(f"📡 نشر موحد - ويب: {'✅' if report['web_saved'] else '❌'} | بوت: {report['telegram_sent']} مستخدم")
            return signal_id
        except Exception as e:
            print(f"⚠️ فشل النشر الموحد: {e}, استخدام الطريقة التقليدية...")
    
    # الطريقة التقليدية (حفظ ملف فقط)
    signal_file = os.path.join(SIGNALS_DIR, f"{signal_id}.json")
    
    try:
        with open(signal_file, 'w', encoding='utf-8') as f:
            json.dump(signal_data, f, ensure_ascii=False, indent=2)
        print(f"✅ تم حفظ الإشارة: {signal_file}")
        return signal_id
    except Exception as e:
        print(f"❌ خطأ في حفظ الإشارة: {e}")
        return None


def save_trade(symbol, recommendation, entry, stop_loss, take_profit, take_profit_2=None, take_profit_3=None, quality_score=None, rr_ratio=None):
    """حفظ صفقة جديدة مع 3 مستويات من أخذ الربح + حفظ الإشارة للبث"""
    if recommendation == 'حياد' or not entry:
        return
    
    # حفظ الإشارة للبث عبر البوت
    signal_id = save_signal_for_broadcast(
        symbol,
        recommendation,
        entry,
        stop_loss,
        take_profit,
        take_profit_2,
        take_profit_3,
        timeframe='5m',
        quality_score=quality_score,
        rr_ratio=rr_ratio
    )
    
    trades = load_active_trades()
    trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    direction = 'buy' if 'شراء' in recommendation else 'sell'
    
    trades[trade_id] = {
        'symbol': symbol,
        'direction': direction,
        'recommendation': recommendation,
        'entry': entry,
        'stop_loss': stop_loss,
        'take_profit': take_profit,
        'take_profit_2': take_profit_2,
        'take_profit_3': take_profit_3,
        'status': 'active',
        'open_time': datetime.now().isoformat(),
        'close_time': None,
        'result': None,
        'signal_id': signal_id
    }
    
    save_active_trades(trades)
    return trade_id


def check_trade_status(trade_id, trade, current_price):
    """التحقق من حالة الصفقة"""
    if trade['status'] != 'active':
        return trade['status'], trade.get('result')
    
    direction = trade['direction']
    entry = trade['entry']
    stop_loss = trade['stop_loss']
    take_profit = trade['take_profit']
    
    # التحقق من اتجاه الشراء
    if direction == 'buy':
        if current_price >= take_profit:
            return 'closed', 'win'
        elif current_price <= stop_loss:
            return 'closed', 'loss'
    
    # التحقق من اتجاه البيع
    elif direction == 'sell':
        if current_price <= take_profit:
            return 'closed', 'win'
        elif current_price >= stop_loss:
            return 'closed', 'loss'
    
    return 'active', None


def update_trades():
    """تحديث حالة جميع الصفقات النشطة"""
    trades = load_active_trades()
    closed_trades = load_closed_trades()
    closed_ids = []
    updated = False
    notifications = []
    
    for trade_id, trade in list(trades.items()):
        if trade['status'] != 'active':
            continue
        
        symbol = trade['symbol']
        
        # جلب السعر الحالي
        try:
            df = fetch_pair_data_5m(symbol, period='1d')
            if df is None or df.empty:
                continue
            
            current_price = float(df['close'].iloc[-1])
            
            # التحقق من حالة الصفقة
            status, result = check_trade_status(trade_id, trade, current_price)
            
            if status == 'closed':
                # تحديث الصفقة
                trade['status'] = status
                trade['result'] = result
                trade['close_time'] = datetime.now().isoformat()
                trade['close_price'] = current_price
                
                # حساب الربح/الخسارة
                entry = trade['entry']
                
                # تحديد عدد الأرقام العشرية بناءً على الزوج
                if symbol in ['XAUUSD', 'GC=F']:
                    # المعادن الثمينة: 2 رقم عشري
                    pip_multiplier = 100
                elif symbol in ['BTCUSD', 'BTC', 'EURCAD', 'GBPUSD', 'AUDNZD']:
                    # البيتكوين والعملات الأخرى: 2-4 أرقام عشرية
                    pip_multiplier = 10000
                else:
                    # العملات الافتراضية: 4 أرقام عشرية
                    pip_multiplier = 10000
                
                if trade['direction'] == 'buy':
                    pips = (current_price - entry) * pip_multiplier
                else:
                    pips = (entry - current_price) * pip_multiplier
                
                trade['pips'] = round(pips, 1)

                # أرشفة الصفقة المنتهية
                closed_trade = dict(trade)
                closed_trade['trade_id'] = trade_id
                closed_trades.append(closed_trade)
                closed_ids.append(trade_id)
                
                updated = True
                
                # إنشاء إشعار
                result_emoji = "✅" if result == 'win' else "❌"
                result_text = "رابحة" if result == 'win' else "خاسرة"
                
                notification = f"""
{result_emoji} <b>صفقة {result_text}</b>

📊 الزوج: {symbol}
📍 الاتجاه: {'شراء' if trade['direction'] == 'buy' else 'بيع'}

💰 سعر الدخول: {entry:.5f}
💰 سعر الإغلاق: {current_price:.5f}

📈 النتيجة: {pips:+.1f} نقطة

⏰ وقت الفتح: {datetime.fromisoformat(trade['open_time']).strftime('%Y-%m-%d %H:%M')}
⏰ وقت الإغلاق: {datetime.fromisoformat(trade['close_time']).strftime('%Y-%m-%d %H:%M')}
"""
                notifications.append(notification)
        
        except Exception as e:
            print(f"خطأ في تحديث صفقة {trade_id}: {e}")
    
    if updated:
        # حذف الصفقات المنتهية من النشطة
        for trade_id in closed_ids:
            trades.pop(trade_id, None)
        save_active_trades(trades)
        # الاحتفاظ بآخر 2000 صفقة منتهية
        if len(closed_trades) > 2000:
            closed_trades = closed_trades[-2000:]
        save_closed_trades(closed_trades)
    
    # إرسال الإشعارات
    for notification in notifications:
        send_telegram_message(notification)
    
    return len(notifications)


def build_trade_report(hours=1):
    """بناء تقرير الصفقات المنتهية خلال آخر عدد ساعات"""
    closed_trades = load_closed_trades()
    active_trades = load_active_trades()
    now = datetime.now()
    cutoff = now.timestamp() - (hours * 3600)

    recent = []
    wins = 0
    losses = 0

    for t in closed_trades:
        close_time = t.get('close_time')
        if not close_time:
            continue
        try:
            ts = datetime.fromisoformat(close_time).timestamp()
        except Exception:
            continue
        if ts >= cutoff:
            recent.append(t)
            if t.get('result') == 'win':
                wins += 1
            elif t.get('result') == 'loss':
                losses += 1

    total = wins + losses
    win_rate = round((wins / total) * 100, 1) if total else 0

    recent_sorted = sorted(recent, key=lambda x: x.get('close_time', ''), reverse=True)

    return {
        'hours': hours,
        'active_count': len([t for t in active_trades.values() if t.get('status') == 'active']),
        'total_closed': len(closed_trades),
        'recent_closed_count': len(recent),
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'recent_closed': recent_sorted[:20]
    }


def run_daily_analysis():
    """تشغيل التحليل الشامل اليومي"""
    global last_auto_analysis_date, auto_analysis_results
    
    today = date.today()
    if last_auto_analysis_date == today:
        return False  # تم التحليل اليوم بالفعل
    
    # إرسال رسالة البدء
    start_msg = f"🚀 بدء التحليل الشامل\nالأزواج: {len(PAIRS_TO_ANALYZE)}\nالوقت: {datetime.now().strftime('%H:%M:%S')}"
    send_telegram_message(start_msg)
    
    auto_analysis_results = {}
    strong_recommendations = []
    
    # تحليل كل زوج
    for symbol, interval in PAIRS_TO_ANALYZE:
        analysis = analyze_pair(symbol, interval)
        if analysis:
            auto_analysis_results[symbol] = analysis
            
            # إرسال تقرير تفصيلي لكل زوج
            report = generate_pair_report(analysis)
            if report:
                send_telegram_message(report)
            
            # تجميع التوصيات القوية
            if 'قوي' in analysis['recommendation']:
                strong_recommendations.append(f"{symbol}: {analysis['recommendation']}")
    
    # إرسال ملخص نهائي
    summary = f"""
✅ انتهى التحليل الشامل

إجمالي الأزواج المحللة: {len(auto_analysis_results)}

التوصيات القوية:
"""
    if strong_recommendations:
        for rec in strong_recommendations:
            summary += f"• {rec}\n"
    else:
        summary += "لا توجد توصيات قوية حالياً"
    
    summary += f"\nالوقت: {datetime.now().strftime('%H:%M:%S')}"
    send_telegram_message(summary)
    
    last_auto_analysis_date = today
    return True


def run_hourly_5min_analysis():
    """تشغيل تحليل 5 دقائق لكل الأزواج وإرسال التوصيات (مرة كل ساعة)"""
    print(f"\n{'='*60}")
    print(f"🚀 بدء التحليل الساعي - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # أولاً: التحقق من الصفقات النشطة
    print("📊 جاري التحقق من الصفقات النشطة...")
    closed_count = update_trades()
    if closed_count > 0:
        msg = f"📊 تم إغلاق {closed_count} صفقة في هذه الجولة"
        print(f"✅ {msg}")
        send_telegram_message(msg)
    else:
        print("✅ لا توجد صفقات مغلقة")
    
    # إرسال رسالة بدء التحليل
    start_msg = f"⏱️ بدء تحليل فريم 5 دقائق\nالأزواج: {len(PAIRS_TO_ANALYZE)}\nتركيز خاص: الذهب/الفضة/النفط/المؤشرات الأمريكية\nالوقت: {datetime.now().strftime('%H:%M:%S')}"
    print(f"📤 إرسال: {start_msg}")
    send_telegram_message(start_msg)

    results = {}
    strong_recommendations = []
    saved_trades = 0

    for symbol, _ in PAIRS_TO_ANALYZE:
        print(f"\n📈 تحليل {symbol}...")
        try:
            analysis = analyze_pair_5m(symbol)
            if analysis:
                results[symbol] = analysis
                report = generate_pair_report(analysis)
                if report:
                    print(f"📤 إرسال تقرير {symbol}")
                    send_telegram_message(report)
                
                # حفظ التوصية كصفقة نشطة مع 3 نقاط أخذ الربح
                if analysis.get('entry') and analysis.get('stop_loss') and analysis.get('take_profit'):
                    trade_id = save_trade(
                              symbol,
                              analysis['recommendation'],
                              analysis['entry'],
                              analysis['stop_loss'],
                              analysis['take_profit'],
                              analysis.get('take_profit_2'),
                              analysis.get('take_profit_3'),
                              analysis.get('quality_score'),
                              analysis.get('rr_ratio')
                              )
                    saved_trades += 1
                    print(f"✅ تم حفظ الصفقة: {trade_id}")
                
                if 'قوي' in analysis['recommendation']:
                    strong_recommendations.append(f"{symbol}: {analysis['recommendation']}")
        except Exception as e:
            print(f"❌ خطأ في تحليل {symbol}: {e}")

    # إرسال الملخص النهائي
    summary = f"""
📊 ملخص التحليل العميق (5 دقائق)
{'='*40}

📈 إجمالي الأصول المحللة: {len(results)}
💼 عدد الصفقات المحفوظة: {saved_trades}
"""
    summary += "\n🎯 التوصيات القوية:\n"
    if strong_recommendations:
        for rec in strong_recommendations:
            summary += f"  • {rec}\n"
    else:
        summary += "  ⚪ لا توجد توصيات قوية حالياً\n"
    summary += f"\n⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}"
    summary += f"\n📡 التحليل التالي بعد: 5 دقائق\n"
    summary += f"{'='*40}"

    print(f"📤 إرسال الملخص النهائي")
    send_telegram_message(summary)
    
    print(f"{'='*60}")
    print(f"✅ انتهى التحليل العميق (5 دقائق) بنجاح")
    print(f"{'='*60}\n")
    return True


if __name__ == "__main__":
    print("🤖 بدء التحليل التلقائي...")
    run_daily_analysis()
    print("✅ انتهى التحليل")

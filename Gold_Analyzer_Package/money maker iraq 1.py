import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import requests
import pandas as pd
import ta
import matplotlib.pyplot as plt
import webbrowser
import urllib.parse
import numpy as np
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
from datetime import datetime, timedelta
import hashlib
import uuid
import json
import os
from fpdf import FPDF
import time
import sys
import platform
import psutil
import threading
import re
from PIL import Image, ImageTk
from datetime import datetime, timedelta

# إعدادات إرسال تلجرام (اضبط القيم عبر متغيرات البيئة لتجنب حفظها في الكود)
TELEGRAM_BOT_TOKEN = os.environ.get("MM_TELEGRAM_BOT_TOKEN", "8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
TELEGRAM_CHAT_ID = os.environ.get("MM_TELEGRAM_CHAT_ID", "7657829546")

# متغيرات الجدولة اليومية
daily_summary_sent = {}  # تتبع الأزواج المرسلة اليوم {pair: timestamp}
last_daily_summary_date = None  # آخر تاريخ تم فيه إرسال الملخص اليومي
pairs_analysis = {}  # تخزين تحليلات الأزواج {pair: analysis_data}
market_open_notified = False  # التحقق من إرسال تنبيه افتتاح السوق

# ============== إعدادات التفعيل المحسنة ==============
ACTIVATION_SERVER = "https://api.smartforex.com"
PREMIUM_FEATURES = False
ACTIVATION_INFO = {
    "activated": False,
    "license_key": "",
    "expiry_date": None,
    "machine_id": "",
    "user_email": ""
}

# كود التفعيل الثابت للمطور
DEVELOPER_LICENSE_KEY = "DEV-2024-SMARTFOREX-ANALYZER"
DEVELOPER_EMAIL = "MAHMOODALQAISE750@GMAIL.COM"

def get_machine_id():
    """إنشاء معرف فريد للجهاز مع تجميع معلومات النظام"""
    try:
        # معلومات النظام الأساسية
        system_info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "ram": str(round(psutil.virtual_memory().total / (1024 ** 3))) + " GB",
            "mac": ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        }
        return hashlib.sha256(json.dumps(system_info).encode('utf-8')).hexdigest()
    except:
        return str(uuid.uuid4())

def check_activation():
    """التحقق من حالة التفعيل مع معالجة أفضل للأخطاء"""
    global PREMIUM_FEATURES, ACTIVATION_INFO
    
    if ACTIVATION_INFO["activated"]:
        if ACTIVATION_INFO["license_key"] == DEVELOPER_LICENSE_KEY:
            # نسخة المطور لا تنتهي صلاحيتها
            PREMIUM_FEATURES = True
            return True
            
        if ACTIVATION_INFO["expiry_date"] and datetime.now() < ACTIVATION_INFO["expiry_date"]:
            PREMIUM_FEATURES = True
            return True
        else:
            ACTIVATION_INFO["activated"] = False
            save_activation_info()
    
    try:
        machine_id = get_machine_id()
        response = requests.post(
            f"{ACTIVATION_SERVER}/verify",
            json={
                "license_key": ACTIVATION_INFO["license_key"],
                "machine_id": machine_id,
                "app_id": "smart_forex_analyzer",
                "app_version": "2.0"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["valid"]:
                ACTIVATION_INFO["activated"] = True
                ACTIVATION_INFO["expiry_date"] = datetime.strptime(data["expiry_date"], "%Y-%m-%d")
                ACTIVATION_INFO["machine_id"] = machine_id
                PREMIUM_FEATURES = True
                save_activation_info()
                return True
    
    except requests.exceptions.RequestException as e:
        print(f"خطأ في الاتصال بالخادم: {str(e)}")
    except Exception as e:
        print(f"خطأ غير متوقع: {str(e)}")
    
    PREMIUM_FEATURES = False
    return False

def save_activation_info():
    """حفظ معلومات التفعيل مع تشفير أساسي"""
    try:
        activation_data = {
            "activated": ACTIVATION_INFO["activated"],
            "license_key": ACTIVATION_INFO["license_key"],
            "expiry_date": ACTIVATION_INFO["expiry_date"].strftime("%Y-%m-%d") if ACTIVATION_INFO["expiry_date"] else None,
            "machine_id": ACTIVATION_INFO["machine_id"],
            "user_email": ACTIVATION_INFO["user_email"]
        }
        
        # تشفير بسيط للمعلومات
        encoded_data = json.dumps(activation_data).encode('utf-8')
        hashed_data = hashlib.sha256(encoded_data).hexdigest()
        
        with open("activation.dat", "w") as f:
            f.write(hashed_data)
            f.write('\n')
            f.write(encoded_data.decode('utf-8'))
            
    except Exception as e:
        print(f"فشل حفظ معلومات التفعيل: {str(e)}")

def load_activation_info():
    """تحميل معلومات التفعيل مع فك التشفير والتحقق"""
    global ACTIVATION_INFO
    
    try:
        if os.path.exists("activation.dat"):
            with open("activation.dat", "r") as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return
                
                stored_hash = lines[0].strip()
                data_json = ''.join(lines[1:])
                
                # التحقق من صحة البيانات
                current_hash = hashlib.sha256(data_json.encode('utf-8')).hexdigest()
                if current_hash != stored_hash:
                    print("تم العبث ببيانات التفعيل!")
                    return
                
                data = json.loads(data_json)
                
                ACTIVATION_INFO["activated"] = data["activated"]
                ACTIVATION_INFO["license_key"] = data["license_key"]
                ACTIVATION_INFO["machine_id"] = data["machine_id"]
                ACTIVATION_INFO["user_email"] = data.get("user_email", "")
                
                if data["expiry_date"]:
                    ACTIVATION_INFO["expiry_date"] = datetime.strptime(data["expiry_date"], "%Y-%m-%d")
                
                if ACTIVATION_INFO["activated"]:
                    threading.Thread(target=check_activation, daemon=True).start()
    except Exception as e:
        print(f"خطأ في تحميل معلومات التفعيل: {str(e)}")
        ACTIVATION_INFO = {
            "activated": False,
            "license_key": "",
            "expiry_date": None,
            "machine_id": get_machine_id(),
            "user_email": ""
        }


def send_telegram_bot_message(text):
    """إرسال توصية إلى بوت تلجرام باستخدام التوكن ومعرف الدردشة"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "لم يتم ضبط TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # فرار الأحرف الخاصة لتجنب خطأ parse entities
    escaped_text = text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace("(", "\\(").replace(")", "\\)").replace("~", "\\~").replace("`", "\\`").replace(">", "\\>").replace("#", "\\#").replace("+", "\\+").replace("-", "\\-").replace("=", "\\=").replace("|", "\\|").replace("{", "\\{").replace("}", "\\}").replace(".", "\\.")
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": escaped_text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200 and response.json().get("ok"):
            return True, "تم الإرسال"
        return False, f"فشل: {response.text}"
    except Exception as exc:
        return False, f"خطأ: {exc}"


def send_daily_summary(pairs_list):
    """إرسال ملخص يومي لتحليل جميع الأزواج"""
    global last_daily_summary_date
    
    today = datetime.now().date()
    if last_daily_summary_date == today:
        return False  # تم الإرسال اليوم بالفعل
    
    summary = f"📊 ملخص التحليل اليومي {today}\n\n"
    summary += f"الأزواج المحللة: {len(pairs_analysis)}\n\n"
    
    strong_buy = 0
    strong_sell = 0
    for pair, data in pairs_analysis.items():
        rec = data.get('recommendation', '')
        if 'شراء قوي' in rec:
            strong_buy += 1
        elif 'بيع قوي' in rec:
            strong_sell += 1
    
    summary += f"شراء قوي: {strong_buy}\n"
    summary += f"بيع قوي: {strong_sell}\n"
    summary += f"\nوقت الإرسال: {datetime.now().strftime('%H:%M:%S')}"
    
    sent, info = send_telegram_bot_message(summary)
    if sent:
        last_daily_summary_date = today
    return sent


def send_strong_recommendation(symbol, interval, recommendation, levels):
    """إرسال توصيات قوية فوراً"""
    entry_price = levels.get('entry_price', 0) if levels else 0
    tp1 = levels.get('tp1', 0) if levels else 0
    tp2 = levels.get('tp2', 0) if levels else 0
    tp3 = levels.get('tp3', 0) if levels else 0
    sl = levels.get('sl', 0) if levels else 0
    
    message = f"تنبيه قوي {symbol} {interval}\n\n"
    message += f"التوصية: {recommendation}\n\n"
    if entry_price:
        message += f"السعر: {entry_price:.5f}\n"
    message += f"المستويات:\n"
    if tp1:
        message += f"TP1: {tp1:.5f}\n"
    if tp2:
        message += f"TP2: {tp2:.5f}\n"
    if tp3:
        message += f"TP3: {tp3:.5f}\n"
    if sl:
        message += f"SL: {sl:.5f}"
    
    return send_telegram_bot_message(message)


def is_market_open():
    """التحقق مما إذا كانت السوق مفتوحة (الأحد 22:00 UTC إلى الجمعة 22:00 UTC)"""
    import pytz
    utc = pytz.UTC
    now = datetime.now(utc)
    weekday = now.weekday()  # 0=الاثنين, 6=الأحد
    hour = now.hour
    
    # السوق تفتح يوم الأحد 22:00 UTC
    if weekday == 6 and hour >= 22:  # الأحد من 22:00
        return True
    # السوق مغلقة يوم الجمعة 22:00 UTC فما فوق
    if weekday == 4 and hour >= 22:  # الجمعة من 22:00
        return False
    # الأيام من الاثنين إلى الخميس
    if 0 <= weekday <= 3:
        return True
    return False


def send_market_open_analysis():
    """إرسال تحليل شامل لجميع الأزواج عند افتتاح السوق"""
    global market_open_notified
    
    if not is_market_open() or market_open_notified:
        return False
    
    # تحقق إذا كنا في الساعة الأولى من الفتح
    import pytz
    utc = pytz.UTC
    now = datetime.now(utc)
    if now.hour != 22:  # غير 22:00 بالـ UTC
        return False
    
    summary = f"تحليل افتتاح السوق\n"
    summary += f"الوقت: {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    summary += f"عدد الأزواج المحللة: {len(pairs_analysis)}\n\n"
    
    if pairs_analysis:
        summary += "التوصيات:\n"
        strong_buy = 0
        strong_sell = 0
        neutral = 0
        
        for pair, data in pairs_analysis.items():
            rec = data.get('recommendation', '')
            if 'شراء قوي' in rec:
                strong_buy += 1
                summary += f"شراء قوي: {data['symbol']}\n"
            elif 'بيع قوي' in rec:
                strong_sell += 1
                summary += f"بيع قوي: {data['symbol']}\n"
            elif 'حياد' not in rec:
                neutral += 1
        
        summary += f"\nالملخص:\n"
        summary += f"شراء قوي: {strong_buy}\n"
        summary += f"بيع قوي: {strong_sell}\n"
        summary += f"محايد: {neutral}"
    
    sent, info = send_telegram_bot_message(summary)
    if sent:
        market_open_notified = True
    return sent


def activate_license(key, email=""):
    """تفعيل الترخيص مع إمكانية إضافة البريد الإلكتروني"""
    global ACTIVATION_INFO
    
    # التحقق من كود المطور
    if key == DEVELOPER_LICENSE_KEY:
        try:
            machine_id = get_machine_id()
            ACTIVATION_INFO["license_key"] = key
            ACTIVATION_INFO["activated"] = True
            ACTIVATION_INFO["expiry_date"] = datetime(2100, 1, 1)  # تاريخ انتهاء بعيد جداً
            ACTIVATION_INFO["machine_id"] = machine_id
            ACTIVATION_INFO["user_email"] = DEVELOPER_EMAIL
            
            save_activation_info()
            return True, "تم تفعيل نسخة المطور بنجاح!"
        except Exception as e:
            return False, f"خطأ في تفعيل نسخة المطور: {str(e)}"
    
    try:
        machine_id = get_machine_id()
        response = requests.post(
            f"{ACTIVATION_SERVER}/activate",
            json={
                "license_key": key,
                "machine_id": machine_id,
                "app_id": "smart_forex_analyzer",
                "app_version": "2.0",
                "user_email": email
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                ACTIVATION_INFO["license_key"] = key
                ACTIVATION_INFO["activated"] = True
                ACTIVATION_INFO["expiry_date"] = datetime.strptime(data["expiry_date"], "%Y-%m-%d")
                ACTIVATION_INFO["machine_id"] = machine_id
                ACTIVATION_INFO["user_email"] = email
                
                save_activation_info()
                return True, data["message"]
            else:
                return False, data["message"]
        else:
            return False, f"خطأ في الخادم: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return False, f"خطأ في الاتصال: {str(e)}"
    except Exception as e:
        return False, f"خطأ غير متوقع: {str(e)}"

# تحميل معلومات التفعيل عند التشغيل
load_activation_info()

# ============== إعدادات التطبيق المحسنة ==============
API_KEY = "079cdb64bbc8415abcf8f7be7e389349"
BASE_URL = "https://api.twelvedata.com/time_series"
BACKUP_API_URL = "https://api.marketdata.app/v1/forex/ohlc/"


symbols_list = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "XAU/USD", "XAG/USD", "BTC/USD", "ETH/USD",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/GBP", "CHF/JPY", "CAD/JPY",
    "NZD/JPY", "AUD/NZD", "EUR/CAD", "GBP/CAD", "EUR/AUD", "GBP/AUD",
    # إضافة الأزواج الجديدة
    "CL/USD",  # النفط الخام
    "NAS100/USD",  # مؤشر ناسداك
    "DJI/USD"  # مؤشر داو جونز
]


intervals_list = ["1min", "5min", "15min", "30min", "1h", "4h", "1day"]
chart_types = ["Candlestick", "Line", "Heikin Ashi", "Renko"]
indicator_types = ["BB", "RSI", "MACD", "EMA", "Stochastic", "ATR", "All", "None"]

translations = {
    "ar": {
        "app_title": "☬🌍MONEY MAKER IRAQ🌍☬",
        "select_symbol": "اختر الزوج:",
        "time_interval": "الفترة الزمنية:",
        "chart_type": "نوع الرسم:",
        "indicators": "المؤشرات:",
        "analyze_button": "تحليل",
        "update_api_button": "تحديث مفتاح API",
        "language_label": "اللغة:",
        "contact_button": "الدعم الفني",
        "education_button": "تعليم الفوركس",
        "whatsapp_share": "مشاركة واتساب",
        "telegram_share": "مشاركة تلجرام",
        "twitter_share": "مشاركة تويتر",
        "daily_analysis_button": "تحليل يومي",
        "pdf_button": "حفظ PDF",
        "auto_trade_button": "تداول آلي",
        "analyze_title": "تحليل",
        "current_price": "السعر الحالي",
        "rsi_label": "مؤشر القوة النسبية",
        "macd_label": "المتوسط المتحرك",
        "pivot_point_label": "نقطة الارتكاز",
        "resistance_label": "مستويات المقاومة",
        "support_label": "مستويات الدعم",
        "fibonacci_title": "مستويات فيبوناتشي",
        "volatility_label": "معدل التقلب",
        "recommendation_title": "التوصية",
        "signals_title": "الإشارات",
        "levels_title": "المستويات الهامة",
        "premium_pdf": "الميزة المدفوعة",
        "pdf_success": "تم الحفظ بنجاح",
        "pdf_error": "خطأ في الحفظ",
        "api_key_updated": "تم التحديث",
        "enter_api_key": "أدخل مفتاح API الجديد:",
        "api_key_success_message": "تم تحديث مفتاح API بنجاح!",
        "no_data_fetch_error": "خطأ في جلب البيانات",
        "not_enough_data_warning": "بيانات غير كافية",
        "not_enough_data_analysis": "لا توجد بيانات كافية للتحليل",
        "volatility_high_warning": "تقلبات عالية - كن حذراً",
        "volatility_low_warning": "تقلبات منخفضة - فرص محدودة",
        "neutral_recommendation": "حياد",
        "signal_rsi_overbought": "إشارة: مؤشر القوة النسبية في منطقة الشراء المفرط",
        "signal_rsi_oversold": "إشارة: مؤشر القوة النسبية في منطقة البيع المفرط",
        "signal_macd_crossover_buy": "إشارة: تقاطع MACD إيجابي (إشارة شراء)",
        "signal_macd_crossover_sell": "إشارة: تقاطع MACD سلبي (إشارة بيع)",
        "signal_ema_buy": "إشارة: تقاطع المتوسطات المتحركة (إشارة شراء)",
        "signal_ema_sell": "إشارة: تقاطع المتوسطات المتحركة (إشارة بيع)",
        "signal_bollinger_buy": "إشارة: السعر تحت باند بولينجر السفلي (إشارة شراء)",
        "signal_bollinger_sell": "إشارة: السعر فوق باند بولينجر العلوي (إشارة بيع)",
        "signal_fibonacci_buy": "إشارة: السعر قرب مستوى فيبوناتشي {0} (إشارة شراء)",
        "signal_fibonacci_sell": "إشارة: السعر قرب مستوى فيبوناتشي {0} (إشارة بيع)",
        "signal_pivot_buy": "إشارة: السعر فوق نقطة الارتكاز (إشارة شراء)",
        "signal_pivot_sell": "إشارة: السعر تحت نقطة الارتكاز (إشارة بيع)",
        "contact_message": "للتواصل مع الدعم الفني:\nالبريد الإلكتروني: MAHMOODALQAISE750@GMAIL.COM\nالهاتف: +962770078321",
        "education_message": "دورات تعليم الفوركس:\n1. أساسيات التداول\n2. التحليل الفني المتقدم\n3. إدارة المخاطر\nزوروا موقعنا: www.smartforexacademy.com",
        "share_unavailable_title": "مشاركة غير متاحة",
        "share_no_data_message": "لا توجد بيانات لمشاركتها",
        "share_success_title": "تمت المشاركة",
        "whatsapp_share_success": "تم إعداد المشاركة على واتساب بنجاح",
        "telegram_share_success": "تم إعداد المشاركة على تلجرام بنجاح",
        "twitter_share_success": "تم إعداد المشاركة على تويتر بنجاح",
        "telegram_share_message": "انضم لقناتنا على تلجرام: t.me/smartforex_signals",
        "premium_features": "ميزات النسخة المدفوعة",
        "activate_premium": "تفعيل النسخة المدفوعة",
        "free_version": "النسخة المجانية",
        "premium_activated": "النسخة المدفوعة مفعلة",
        "loading_data": "جاري تحميل البيانات...",
        "analysis_complete": "اكتمل التحليل",
        "error_occurred": "حدث خطأ",
        "trial_remaining": "الأيام المتبقية للتجربة: {0}",
        "expired_license": "انتهت صلاحية الترخيص",
        "developer_version": "نسخة المطور",
        "auto_trade_success": "تم تصدير إشارة التداول",
        "auto_trade_error": "خطأ في التداول الآلي",
        "no_trade_signal": "لا توجد إشارة تداول"
    },
    "en": {
        "app_title": "MONEY MAKER",
        "select_symbol": "Select Symbol:",
        "time_interval": "Time Interval:",
        "chart_type": "Chart Type:",
        "indicators": "Indicators:",
        "analyze_button": "Analyze",
        "update_api_button": "Update API Key",
        "language_label": "Language:",
        "contact_button": "Technical Support",
        "education_button": "Forex Education",
        "whatsapp_share": "Share via WhatsApp",
        "telegram_share": "Share via Telegram",
        "twitter_share": "Share via Twitter",
        "daily_analysis_button": "Daily Analysis",
        "pdf_button": "Save PDF",
        "auto_trade_button": "Auto Trade",
        "analyze_title": "Analysis",
        "current_price": "Current Price",
        "rsi_label": "Relative Strength Index",
        "macd_label": "Moving Average",
        "pivot_point_label": "Pivot Point",
        "resistance_label": "Resistance Levels",
        "support_label": "Support Levels",
        "fibonacci_title": "Fibonacci Levels",
        "volatility_label": "Volatility Rate",
        "recommendation_title": "Recommendation",
        "signals_title": "Signals",
        "levels_title": "Key Levels",
        "premium_pdf": "Premium Feature",
        "pdf_success": "Saved Successfully",
        "pdf_error": "Save Error",
        "api_key_updated": "Updated",
        "enter_api_key": "Enter new API key:",
        "api_key_success_message": "API key updated successfully!",
        "no_data_fetch_error": "Data Fetch Error",
        "not_enough_data_warning": "Insufficient Data",
        "not_enough_data_analysis": "Not enough data for analysis",
        "volatility_high_warning": "High volatility - Be cautious",
        "volatility_low_warning": "Low volatility - Limited opportunities",
        "neutral_recommendation": "Neutral",
        "signal_rsi_overbought": "Signal: RSI in overbought area",
        "signal_rsi_oversold": "Signal: RSI in oversold area",
        "signal_macd_crossover_buy": "Signal: Positive MACD crossover (Buy signal)",
        "signal_macd_crossover_sell": "Signal: Negative MACD crossover (Sell signal)",
        "signal_ema_buy": "Signal: Moving averages crossover (Buy signal)",
        "signal_ema_sell": "Signal: Moving averages crossover (Sell signal)",
        "signal_bollinger_buy": "Signal: Price below Bollinger lower band (Buy signal)",
        "signal_bollinger_sell": "Signal: Price above Bollinger upper band (Sell signal)",
        "signal_fibonacci_buy": "Signal: Price near Fibonacci level {0} (Buy signal)",
        "signal_fibonacci_sell": "Signal: Price near Fibonacci level {0} (Sell signal)",
        "signal_pivot_buy": "Signal: Price above pivot point (Buy signal)",
        "signal_pivot_sell": "Signal: Price below pivot point (Sell signal)",
        "contact_message": "For technical support:\nEmail: support@smartforex.com\nPhone: +966532145698",
        "education_message": "Forex Education Courses:\n1. Trading Fundamentals\n2. Advanced Technical Analysis\n3. Risk Management\nVisit our website: www.smartforexacademy.com",
        "share_unavailable_title": "Share Unavailable",
        "share_no_data_message": "No data to share",
        "share_success_title": "Shared Successfully",
        "whatsapp_share_success": "WhatsApp share prepared successfully",
        "telegram_share_success": "Telegram share prepared successfully",
        "twitter_share_success": "Twitter share prepared successfully",
        "telegram_share_message": "Join our Telegram channel: t.me/smartforex_signals",
        "premium_features": "Premium Features",
        "activate_premium": "Activate Premium",
        "free_version": "Free Version",
        "premium_activated": "Premium Activated",
        "loading_data": "Loading data...",
        "analysis_complete": "Analysis complete",
        "error_occurred": "Error occurred",
        "trial_remaining": "Trial days remaining: {0}",
        "expired_license": "License expired",
        "developer_version": "Developer Version",
        "auto_trade_success": "Trading signal exported",
        "auto_trade_error": "Auto trade error",
        "no_trade_signal": "No trading signal"
    }
}

class DataFetchError(Exception):
    pass

def fetch_data(symbol, interval="1h", outputsize=100):
    """جلب البيانات مع محاولات متعددة ومصادر احتياطية"""
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        try:
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": API_KEY,
                "format": "JSON"
            }
            response = requests.get(BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "code" in data and data["code"] != 200:
                error_message = data.get('message', 'Unknown API error')
                raise DataFetchError(f"Error fetching data: {error_message}")
            
            if "values" not in data or not data["values"]:
                raise DataFetchError("No data available for this pair and time frame")
            
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={"datetime": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close"})
            
            for col in ["Open", "High", "Low", "Close"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            df = df.dropna()
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date").reset_index(drop=True)
            df['symbol'] = symbol
            
            return df
        
        except requests.exceptions.RequestException as e:
            attempts += 1
            if attempts < max_attempts:
                time.sleep(2)  # انتظار قبل إعادة المحاولة
                continue
            raise DataFetchError(f"Connection error: {str(e)}")
        
        except Exception as e:
            attempts += 1
            if attempts < max_attempts:
                time.sleep(2)
                continue
            raise DataFetchError(f"Unexpected error: {str(e)}")

def analyze(df, indicators="All"):
    """تحليل البيانات مع خيارات اختيار المؤشرات"""
    if len(df) < 14:
        return df
    
    # Bollinger Bands
    if indicators in ["All", "BB"] and len(df) >= 20:
        bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
        df["BB_High"] = bb.bollinger_hband()
        df["BB_Low"] = bb.bollinger_lband()
        df["BB_Mid"] = bb.bollinger_mavg()
    else:
        df["BB_High"] = np.nan
        df["BB_Low"] = np.nan
        df["BB_Mid"] = np.nan
    
    # RSI
    if indicators in ["All", "RSI"] and len(df) >= 14:
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    else:
        df["RSI"] = np.nan
    
    # MACD
    if indicators in ["All", "MACD"] and len(df) >= 26:
        macd = ta.trend.MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9)
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Hist"] = macd.macd_diff()
    else:
        df["MACD"] = np.nan
        df["MACD_Signal"] = np.nan
        df["MACD_Hist"] = np.nan
    
    # EMAs
    if indicators in ["All", "EMA"] and len(df) >= 50:
        df["EMA_50"] = ta.trend.ema_indicator(df["Close"], window=50)
    else:
        df["EMA_50"] = np.nan
        
    if indicators in ["All", "EMA"] and len(df) >= 200:
        df["EMA_200"] = ta.trend.ema_indicator(df["Close"], window=200)
    else:
        df["EMA_200"] = np.nan
    
    # Stochastic Oscillator
    if indicators in ["All", "Stochastic"] and len(df) >= 14:
        stoch = ta.momentum.StochasticOscillator(
            high=df["High"], 
            low=df["Low"], 
            close=df["Close"], 
            window=14, 
            smooth_window=3
        )
        df['STOCH_K'] = stoch.stoch()
        df['STOCH_D'] = stoch.stoch_signal()
    else:
        df['STOCH_K'] = np.nan
        df['STOCH_D'] = np.nan
    
    # ATR
    if indicators in ["All", "ATR"] and len(df) >= 14:
        df["ATR"] = ta.volatility.AverageTrueRange(
            high=df["High"], 
            low=df["Low"], 
            close=df["Close"], 
            window=14
        ).average_true_range()
    else:
        df["ATR"] = np.nan
    
    return df

def calculate_fibonacci_levels(df):
    """حساب مستويات فيبوناتشي بدقة أعلى"""
    if df.empty or len(df) < 10:
        return {}
    
    # استخدام فترة أطول وأكثر دقة
    recent_df = df.tail(100)
    high = recent_df["High"].max()
    low = recent_df["Low"].min()
    diff = high - low
    
    # مستويات فيبوناتشي موسعة
    levels = {
        "0.0%": round(high, 5),
        "23.6%": round(high - 0.236 * diff, 5),
        "38.2%": round(high - 0.382 * diff, 5),
        "50.0%": round(high - 0.5 * diff, 5),
        "61.8%": round(high - 0.618 * diff, 5),
        "78.6%": round(high - 0.786 * diff, 5),
        "100.0%": round(low, 5),
        "127.2%": round(low - 0.272 * diff, 5),
        "161.8%": round(low - 0.618 * diff, 5)
    }
    return levels

def calculate_pivot_point(df):
    """حساب نقاط الارتكاز مع معالجة أفضل للبيانات"""
    if df.empty or len(df) < 2:
        return None, None, None, None, None
    
    df['Date'] = pd.to_datetime(df['Date'])
    df['DateOnly'] = df['Date'].dt.date
    
    last_date = df.iloc[-1]["DateOnly"]
    
    # إيجاد اليوم السابق مع التحقق من وجود بيانات كافية
    prev_dates = df[df['DateOnly'] < last_date]['DateOnly'].unique()
    if len(prev_dates) == 0:
        return None, None, None, None, None
        
    prev_day = max(prev_dates)
    prev_day_df = df[df['DateOnly'] == prev_day]
    
    if len(prev_day_df) == 0:
        return None, None, None, None, None
        
    prev_high = prev_day_df["High"].max()
    prev_low = prev_day_df["Low"].min()
    prev_close = prev_day_df.iloc[-1]["Close"]

    pp = (prev_high + prev_low + prev_close) / 3
    r1 = (2 * pp) - prev_low
    s1 = (2 * pp) - prev_high
    r2 = pp + (prev_high - prev_low)
    s2 = pp - (prev_high - prev_low)
    
    return pp, r1, r2, s1, s2

def calculate_volatility(df):
    """حساب التقلبات بدقة أعلى"""
    if len(df) < 20:
        return 1.0
    
    # حساب التقلبات باستخدام الانحراف المعياري للعوائد اللوغاريتمية
    returns = np.log(df['Close'] / df['Close'].shift(1)).dropna()
    volatility = returns.std() * np.sqrt(252) * 100  # كنسبة مئوية
    
    return volatility

def calculate_tp_sl(recommendation, entry_price, atr_value, volatility, app_instance):
    """حساب مستويات جني الربح ووقف الخسارة بشكل ديناميكي"""
    # تعديل المضاعفات بناء على التقلبات
    if volatility > 2.0:
        tp_multipliers = [1.0, 1.8, 2.5]
        sl_multiplier = 1.2
    elif volatility < 0.5:
        tp_multipliers = [0.8, 1.2, 1.8]
        sl_multiplier = 0.8
    else:
        tp_multipliers = [1.2, 1.8, 2.5]
        sl_multiplier = 1.0
    
    # تعديل بناء على قوة التوصية
    if "قوي" in recommendation:
        tp_multipliers = [x * 1.2 for x in tp_multipliers]
    elif "محتمل" in recommendation:
        tp_multipliers = [x * 0.8 for x in tp_multipliers]
    
    # حساب TP/SL بناء على نوع التوصية
    if "شراء" in recommendation:
        tp1 = entry_price + tp_multipliers[0] * atr_value
        tp2 = entry_price + tp_multipliers[1] * atr_value
        tp3 = entry_price + tp_multipliers[2] * atr_value
        sl = entry_price - sl_multiplier * atr_value
    elif "بيع" in recommendation:
        tp1 = entry_price - tp_multipliers[0] * atr_value
        tp2 = entry_price - tp_multipliers[1] * atr_value
        tp3 = entry_price - tp_multipliers[2] * atr_value
        sl = entry_price + sl_multiplier * atr_value
    else:  # Neutral
        tp1 = entry_price + 0.5 * atr_value 
        tp2 = entry_price + 1.0 * atr_value
        tp3 = entry_price + 1.5 * atr_value
        sl = entry_price - 0.5 * atr_value
    
    return tp1, tp2, tp3, sl

def detect_signals(df, interval, app_instance):
    """كشف الإشارات مع نظام نقاط متقدم"""
    symbol = df['symbol'].iloc[0] if 'symbol' in df.columns else "N/A"
    signals = []
    
    # تخزين البيانات للاستخدام في المشاركة
    analysis_data = {
        'symbol': symbol,
        'interval': interval,
        'entry_price': None,
        'recommendation': '',
        'tp1': None,
        'tp2': None,
        'tp3': None,
        'sl': None
    }
    
    signals.append(f"📈 {app_instance.get_text('analyze_title')} {symbol} ({interval})")
    signals.append("=" * 50)
    
    if df.empty or len(df) < 50:
        signals.append(app_instance.get_text("not_enough_data_analysis"))
        return signals, app_instance.get_text("neutral_recommendation"), {}, {}

    entry_price = df.iloc[-1]["Close"]
    analysis_data['entry_price'] = entry_price
    
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    # حساب نقاط الارتكاز ومستويات فيبوناتشي
    pp, r1, r2, s1, s2 = calculate_pivot_point(df)
    fib_levels = calculate_fibonacci_levels(df)

    signals.append(f"📊 {app_instance.get_text('current_price')}: {round(entry_price, 5)}")
    
    # تحليل RSI
    if 'RSI' in df.columns and not np.isnan(last["RSI"]):
        rsi_value = last["RSI"]
        rsi_status = ""
        if rsi_value > 70:
            rsi_status = "⬆️ شراء مفرط"
            signals.append(app_instance.get_text("signal_rsi_overbought"))
        elif rsi_value < 30:
            rsi_status = "⬇️ بيع مفرط"
            signals.append(app_instance.get_text("signal_rsi_oversold"))
        else:
            rsi_status = "⚖️ طبيعي"
        signals.append(f"📉 {app_instance.get_text('rsi_label')}: {round(rsi_value, 2)} ({rsi_status})")
    
    # تحليل MACD
    if 'MACD' in df.columns and not np.isnan(last["MACD"]):
        macd_diff = last['MACD'] - last['MACD_Signal']
        macd_status = ""
        if macd_diff > 0:
            macd_status = "⬆️ إيجابي"
            if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
                signals.append(app_instance.get_text("signal_macd_crossover_buy"))
        else:
            macd_status = "⬇️ سلبي"
            if last['MACD'] < last['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
                signals.append(app_instance.get_text("signal_macd_crossover_sell"))
        signals.append(f"📈 {app_instance.get_text('macd_label')}: {round(macd_diff, 5)} ({macd_status})")

    levels = {}
    if pp is not None:
        signals.append(f"📍 {app_instance.get_text('pivot_point_label')}: {round(pp, 5)}")
        signals.append(f"🛑 {app_instance.get_text('resistance_label')}: {round(r1, 5)} / {round(r2, 5)}")
        signals.append(f"🟢 {app_instance.get_text('support_label')}: {round(s1, 5)} / {round(s2, 5)}")
        levels.update({
            "Pivot Point": round(pp, 5),
            "Resistance 1": round(r1, 5),
            "Resistance 2": round(r2, 5),
            "Support 1": round(s1, 5),
            "Support 2": round(s2, 5)
        })

    # مستويات فيبوناتشي
    if fib_levels:
        signals.append("✨ " + app_instance.get_text("fibonacci_title"))
        fib_signals = []
        for level, price in fib_levels.items():
            distance = abs(entry_price - price)
            distance_percent = (distance / entry_price) * 100
            
            if distance_percent < 0.1:
                fib_signals.append(f"  ⚡ {level}: {price:.5f} (قريب جداً)")
            elif distance_percent < 0.5:
                fib_signals.append(f"  ➡️ {level}: {price:.5f} (قريب)")
            else:
                fib_signals.append(f"  • {level}: {price:.5f}")
        
        fib_signals.reverse()
        signals.extend(fib_signals)
    
    # ==== نظام نقاط متقدم للإشارات ====
    buy_score = 0
    sell_score = 0
    confidence_factors = []
    
    # 1. تقاطع المتوسطات (إشارة قوية)
    if len(df) >= 200:
        if last['EMA_50'] > last['EMA_200'] and prev['EMA_50'] <= prev['EMA_200']:
            signals.append(app_instance.get_text("signal_ema_buy"))
            buy_score += 2
            confidence_factors.append("تقاطع المتوسطات لصالح الشراء")
        elif last['EMA_50'] < last['EMA_200'] and prev['EMA_50'] >= prev['EMA_200']:
            signals.append(app_instance.get_text("signal_ema_sell"))
            sell_score += 2
            confidence_factors.append("تقاطع المتوسطات لصالح البيع")
    
    # 2. باند بولينجر (إشارة متوسطة)
    if "BB_Low" in df.columns and not pd.isna(last["BB_Low"]):
        if last['Close'] < last['BB_Low']:
            signals.append(app_instance.get_text("signal_bollinger_buy"))
            buy_score += 1
            confidence_factors.append("السعر تحت باند بولينجر السفلي")
    if "BB_High" in df.columns and not pd.isna(last["BB_High"]):
        if last['Close'] > last['BB_High']:
            signals.append(app_instance.get_text("signal_bollinger_sell"))
            sell_score += 1
            confidence_factors.append("السعر فوق باند بولينجر العلوي")
    
    # 3. مستويات فيبوناتشي (إشارة متوسطة)
    if fib_levels:
        for level, price in fib_levels.items():
            if abs(entry_price - price) < (entry_price * 0.001):
                if level in ["61.8%", "78.6%"]:
                    signals.append(app_instance.get_text("signal_fibonacci_buy").format(level))
                    buy_score += 1
                    confidence_factors.append(f"السعر قرب مستوى فيبوناتشي {level} للشراء")
                elif level in ["23.6%", "38.2%"]:
                    signals.append(app_instance.get_text("signal_fibonacci_sell").format(level))
                    sell_score += 1
                    confidence_factors.append(f"السعر قرب مستوى فيبوناتشي {level} للبيع")
    
    # 4. نقاط الارتكاز (إشارة متوسطة)
    if r1 and entry_price > r1:
        signals.append(app_instance.get_text("signal_pivot_buy"))
        buy_score += 1
        confidence_factors.append("السعر فوق نقطة الارتكاز")
    if s1 and entry_price < s1:
        signals.append(app_instance.get_text("signal_pivot_sell"))
        sell_score += 1
        confidence_factors.append("السعر تحت نقطة الارتكاز")
    
    # 5. RSI (إشارة متوسطة)
    if 'RSI' in df.columns and not np.isnan(last["RSI"]):
        if last["RSI"] < 30:
            buy_score += 1
            confidence_factors.append("RSI في منطقة البيع المفرط")
        elif last["RSI"] > 70:
            sell_score += 1
            confidence_factors.append("RSI في منطقة الشراء المفرط")
    
    # 6. MACD (إشارة متوسطة)
    if 'MACD' in df.columns and not np.isnan(last["MACD"]):
        if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
            buy_score += 1
            confidence_factors.append("تقاطع MACD إيجابي")
        elif last['MACD'] < last['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
            sell_score += 1
            confidence_factors.append("تقاطع MACD سلبي")
    
    # 7. ستوكاستك (إشارة ضعيفة)
    if 'STOCH_K' in df.columns and 'STOCH_D' in df.columns:
        if last['STOCH_K'] < 20 and last['STOCH_D'] < 20:
            buy_score += 0.5
            confidence_factors.append("ستوكاستك في منطقة البيع المفرط")
        elif last['STOCH_K'] > 80 and last['STOCH_D'] > 80:
            sell_score += 0.5
            confidence_factors.append("ستوكاستك في منطقة الشراء المفرط")
    
    # 8. وضع السعر بالنسبة لباند بولينجر الأوسط
    if "BB_Mid" in df.columns and not pd.isna(last["BB_Mid"]):
        if last['Close'] > last['BB_Mid']:
            buy_score += 0.5
        else:
            sell_score += 0.5
    
    # 9. اتجاه الترند العام
    if len(df) > 100:
        short_ma = df['Close'].tail(20).mean()
        long_ma = df['Close'].tail(50).mean()
        if short_ma > long_ma:
            buy_score += 0.5
            confidence_factors.append("اتجاه صاعد")
        else:
            sell_score += 0.5
            confidence_factors.append("اتجاه هابط")
    
    # تحديد التوصية النهائية مع مستويات الثقة
    confidence = ""
    confidence_description = ""
    if buy_score > sell_score:
        if buy_score >= 4:
            final_recommendation = "شراء قوي"
            confidence = "🔥 ثقة عالية"
            confidence_description = "إشارات متعددة وقوية تؤيد الشراء"
        elif buy_score >= 2.5:
            final_recommendation = "شراء"
            confidence = "🟢 ثقة متوسطة"
            confidence_description = "إشارات جيدة تؤيد الشراء"
        else:
            final_recommendation = "شراء محتمل"
            confidence = "🟡 ثقة منخفضة"
            confidence_description = "إشارات ضعيفة تؤيد الشراء"
    elif sell_score > buy_score:
        if sell_score >= 4:
            final_recommendation = "بيع قوي"
            confidence = "🔥 ثقة عالية"
            confidence_description = "إشارات متعددة وقوية تؤيد البيع"
        elif sell_score >= 2.5:
            final_recommendation = "بيع"
            confidence = "🔴 ثقة متوسطة"
            confidence_description = "إشارات جيدة تؤيد البيع"
        else:
            final_recommendation = "بيع محتمل"
            confidence = "🟠 ثقة منخفضة"
            confidence_description = "إشارات ضعيفة تؤيد البيع"
    else:
        final_recommendation = "حياد"
        confidence = "⚪ انتظار"
        confidence_description = "لا توجد إشارات واضحة، انتظر تأكيدات"
    
    # إضافة مستوى الثقة والإشارات المؤثرة
    signals.append(f"\n🔰 مستوى الثقة: {confidence}")
    signals.append(f"📌 الإشارات المؤثرة: {', '.join(confidence_factors[:3])}")
    
    # حساب التقلبات
    volatility = calculate_volatility(df)
    atr_value = last["ATR"] if "ATR" in df.columns and not np.isnan(last["ATR"]) else (df["High"].mean() - df["Low"].mean()) * 0.003
    
    # حساب مستويات جني الربح ووقف الخسارة
    tp1, tp2, tp3, sl = calculate_tp_sl(final_recommendation, entry_price, atr_value, volatility, app_instance)
    
    # تخزين مستويات TP/SL
    analysis_data.update({
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3,
        'sl': sl,
        'recommendation': final_recommendation
    })
    
    # إضافة معلومات التقلبات
    volatility_status = ""
    if volatility > 2.0:
        volatility_status = "🟠 " + app_instance.get_text("volatility_high_warning")
    elif volatility < 0.5:
        volatility_status = "🟢 " + app_instance.get_text("volatility_low_warning")
    else:
        volatility_status = "⚪ تقلب طبيعي"
    
    signals.append(f"📊 {app_instance.get_text('volatility_label')} {volatility:.2f}% - {volatility_status}")
    
    # إضافة معلومات التوصية إلى القاموس
    levels.update({
        "TP1": round(tp1, 5), 
        "TP2": round(tp2, 5),
        "TP3": round(tp3, 5),
        "SL": round(sl, 5),
        "Entry Price": round(entry_price, 5),
        "Time Frame": interval,
        "Recommendation": final_recommendation,
        "Confidence": confidence
    })
    
    # تخزين بيانات التحليل للتشارك
    app_instance.last_analysis_data = analysis_data
    
    return signals, final_recommendation, levels, fib_levels

class MoneyMakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # إنشاء المتغيرات النصية أولاً
        self.current_language = tk.StringVar(value="العربية")
        self.symbol_var = tk.StringVar()
        self.interval_var = tk.StringVar()
        self.chart_type_var = tk.StringVar()
        self.indicators_var = tk.StringVar()
        
        # تخزين بيانات التحليل الأخير
        self.last_analysis_data = {}
        
        self.languages = {"العربية": "ar", "English": "en"} 
        
        self.title(self.get_text("app_title"))
        self.geometry("1200x800")
        self.configure(bg="#2c3e50")
        self.minsize(1200, 800)
        
        # إعداد النمط
        self.setup_styles()
        
        # حالة النسخة المدفوعة
        self.premium_status = PREMIUM_FEATURES
        
        # إنشاء واجهة المستخدم
        self.create_widgets()
        
        # تحميل أيقونة التطبيق
        self.set_icon()
        
        # تحليل أولي
        self.run_analysis()
        
        # تذكير بالنسخة المدفوعة إذا لزم الأمر
        if not self.premium_status:
            self.after(2000, self.show_premium_reminder)
        self.status_var = tk.StringVar(value="جاري التحقق من الترخيص...")        # تحديث حالة الترخيص
        self.update_license_status()
        
        # إعداد شريط الحالة
        self.setup_status_bar()

    def setup_styles(self):
        """تهيئة أنماط التطبيق"""
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background="#2c3e50")
        style.configure("TLabel", background="#2c3e50", foreground="white", font=("Arial", 11))
        style.configure("Title.TLabel", font=("Arial", 18, "bold"), foreground="#1abc9c", background="#2c3e50")
        style.configure("TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"), borderwidth=0, relief="flat")
        style.map("TButton", background=[('active', '#2980b9')])
        style.configure("TCombobox", fieldbackground="#34495e", background="#34495e", foreground="white", arrowcolor="white")
        style.map("TCombobox", fieldbackground=[('readonly', '#34495e')], foreground=[('readonly', 'white')])
        style.configure("Premium.TButton", background="#9b59b6", foreground="white")
        style.configure("Developer.TButton", background="#e67e22", foreground="white")
        style.configure("StrongBuy.TLabel", background="#2c3e50", foreground="#2ecc71", font=("Arial", 12, "bold"))
        style.configure("Buy.TLabel", background="#2c3e50", foreground="#27ae60", font=("Arial", 12))
        style.configure("Neutral.TLabel", background="#2c3e50", foreground="#f39c12", font=("Arial", 12))
        style.configure("Sell.TLabel", background="#2c3e50", foreground="#e74c3c", font=("Arial", 12))
        style.configure("StrongSell.TLabel", background="#2c3e50", foreground="#c0392b", font=("Arial", 12, "bold"))
        style.configure("Status.TFrame", background="#34495e")
        style.configure("Status.TLabel", background="#34495e", foreground="#bdc3c7", font=("Arial", 9))

    def set_icon(self):
        """تعيين أيقونة للتطبيق"""
        try:
            icon_path = "icon.ico" if os.path.exists("icon.ico") else None
            if icon_path:
                self.iconbitmap(icon_path)
        except:
            pass

    def update_license_status(self):
        """تحديث حالة الترخيص في شريط الحالة"""
        if ACTIVATION_INFO["activated"]:
            if ACTIVATION_INFO["license_key"] == DEVELOPER_LICENSE_KEY:
                self.status_var.set(self.get_text("developer_version"))
            elif ACTIVATION_INFO["expiry_date"]:
                days_left = (ACTIVATION_INFO["expiry_date"] - datetime.now()).days
                if days_left > 0:
                    self.status_var.set(self.get_text("trial_remaining").format(days_left))
                else:
                    self.status_var.set(self.get_text("expired_license"))
                    ACTIVATION_INFO["activated"] = False
                    self.premium_status = False
                    self.premium_button.config(text=self.get_text("free_version"), style="TButton")
            else:
                self.status_var.set(self.get_text("premium_activated"))
        else:
            self.status_var.set(self.get_text("free_version"))
        
        self.after(60000, self.update_license_status)  # تحديث كل دقيقة

    def setup_status_bar(self):
        """إنشاء شريط الحالة"""
        status_frame = ttk.Frame(self, style="Status.TFrame", height=20)
        status_frame.pack(side="bottom", fill="x", padx=0, pady=0)
        
        self.status_var = tk.StringVar(value=self.get_text("free_version"))
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel")
        status_label.pack(side="left", padx=10)
        
        version_label = ttk.Label(status_frame, text="Smart Forex Analyzer v2.0", style="Status.TLabel")
        version_label.pack(side="right", padx=10)

    def show_premium_reminder(self):
        """عرض تذكير بالنسخة المدفوعة"""
        if not self.premium_status:
            reminder = tk.Toplevel(self)
            reminder.title("النسخة المجانية")
            reminder.geometry("600x450")
            reminder.resizable(False, False)
            reminder.transient(self)
            reminder.grab_set()
            
            # مركزية النافذة
            reminder.update_idletasks()
            width = reminder.winfo_width()
            height = reminder.winfo_height()
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            reminder.geometry(f'+{x}+{y}')
            
            frame = ttk.Frame(reminder, padding=20)
            frame.pack(fill="both", expand=True)
            
            ttk.Label(frame, text="النسخة المجانية محدودة الميزات", font=("Arial", 14, "bold"), foreground="#3498db").pack(pady=10)
            
            ttk.Label(frame, text="مزايا النسخة المدفوعة:", font=("Arial", 11)).pack(anchor="w", padx=20)
            features = [
                "• جميع أزواج العملات (23 زوج)",
                "• جميع الفترات الزمنية (7 فترات)",
                "• أنواع الرسوم البيانية المتقدمة",
                "• خيارات متعددة للمؤشرات الفنية",
                "• إشارات تداول متقدمة",
                "• تحليل تقني متعمق",
                "• تحديثات مستمرة",
                "• حفظ التقارير كملفات PDF",
                "• دعم فني متخصص"
            ]
            for feature in features:
                ttk.Label(frame, text=feature).pack(anchor="w", padx=40)
            
            ttk.Label(frame, text="أسعار خاصة:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10,0))
            prices = [
                "• اشتراك شهري: 50$",
                "• اشتراك ربع سنوي: 100$ (توفير 17%)",
                "• اشتراك سنوي: 300$ (توفير 38%)"
            ]
            for price in prices:
                ttk.Label(frame, text=price).pack(anchor="w", padx=40)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=20)
            
            ttk.Button(btn_frame, text="ترقية الآن", command=lambda: [reminder.destroy(), self.activate_premium()], 
                      style="Premium.TButton").pack(side="left", padx=10)
            
            ttk.Button(btn_frame, text="لاحقاً", command=reminder.destroy).pack(side="left", padx=10)

    def activate_premium(self):
        """نافذة تفعيل النسخة المدفوعة"""
        activation_win = tk.Toplevel(self)
        activation_win.title("تفعيل النسخة المدفوعة")
        activation_win.geometry("500x500")
        activation_win.resizable(False, False)
        activation_win.transient(self)
        activation_win.grab_set()
        
        # مركزية النافذة
        activation_win.update_idletasks()
        width = activation_win.winfo_width()
        height = activation_win.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        activation_win.geometry(f'+{x}+{y}')
        
        frame = ttk.Frame(activation_win, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="أدخل مفتاح الترخيص", font=("Arial", 12)).pack(pady=10)
        
        license_frame = ttk.Frame(frame)
        license_frame.pack(fill="x", pady=10)
        
        ttk.Label(license_frame, text="مفتاح الترخيص:").pack(side="left")
        license_var = tk.StringVar()
        license_entry = ttk.Entry(license_frame, textvariable=license_var, width=30)
        license_entry.pack(side="left", padx=5)
        license_entry.focus()
        
        email_frame = ttk.Frame(frame)
        email_frame.pack(fill="x", pady=5)
        
        ttk.Label(email_frame, text="البريد الإلكتروني (اختياري):").pack(side="left")
        email_var = tk.StringVar()
        email_entry = ttk.Entry(email_frame, textvariable=email_var, width=30)
        email_entry.pack(side="left", padx=5)
        
        activate_btn = ttk.Button(frame, text="تفعيل", command=lambda: self.do_activation(license_var.get(), email_var.get(), activation_win), 
                                style="Premium.TButton")
        activate_btn.pack(pady=15)
        
        ttk.Label(frame, text="طرق الدفع المتاحة:", font=("Arial", 11)).pack(anchor="w", pady=(20,5))
        
        payment_frame = ttk.Frame(frame)
        payment_frame.pack(fill="x")
        
        methods = [
            ("بطاقة ائتمان", "credit_card"),
            ("PayPal", "paypal"),
            ("تحويل بنكي", "bank_transfer"),
            ("محافظ إلكترونية", "ewallet")
        ]
        
        for method, method_id in methods:
            ttk.Button(payment_frame, text=method, 
                      command=lambda m=method_id: self.show_payment_page(m),
                      width=15).pack(side="left", padx=5, pady=5)
        
        ttk.Label(frame, text="يمكنك شراء ترخيص من موقعنا الرسمي", foreground="blue", cursor="hand2").pack(pady=5)
        link_label = ttk.Label(frame, text=f"{ACTIVATION_SERVER}/pricing", foreground="blue", cursor="hand2")
        link_label.pack()
        link_label.bind("<Button-1>", lambda e: webbrowser.open(f"{ACTIVATION_SERVER}/pricing"))
        
        ttk.Label(frame, text="أو التواصل مع الدعم: support@smartforex.com", foreground="blue", cursor="hand2").pack(pady=5)
        support_label = ttk.Label(frame, text="support@smartforex.com", foreground="blue", cursor="hand2")
        support_label.pack()
        support_label.bind("<Button-1>", lambda e: webbrowser.open("mailto:support@smartforex.com"))

    def do_activation(self, license_key, email, window):
        """تنفيذ عملية التفعيل"""
        if not license_key:
            messagebox.showerror("خطأ", "يرجى إدخال مفتاح الترخيص")
            return
            
        self.status_var.set("جاري التفعيل...")
        window.update()
        
        success, message = activate_license(license_key, email)
        if success:
            messagebox.showinfo("تم التفعيل", "تم تفعيل النسخة المدفوعة بنجاح!")
            self.premium_status = True
            
            # تحديث نص زر النسخة المدفوعة
            if license_key == DEVELOPER_LICENSE_KEY:
                self.premium_button.config(text=self.get_text("developer_version"), style="Developer.TButton")
            else:
                self.premium_button.config(text=self.get_text("premium_activated"), style="Premium.TButton")
                
            self.premium_button.config(state="disabled")
            self.symbol_combo["values"] = symbols_list
            self.interval_combo["values"] = intervals_list
            self.chart_combo["values"] = chart_types
            self.indicator_combo["values"] = indicator_types
            window.destroy()
            self.update_license_status()
            self.run_analysis()
        else:
            messagebox.showerror("خطأ في التفعيل", message)
            self.status_var.set(self.get_text("free_version"))

    def show_payment_page(self, method):
        """فتح صفحة الدفع"""
        webbrowser.open(f"{ACTIVATION_SERVER}/pay?method={method}")
        messagebox.showinfo("إتمام الدفع", "بعد إتمام الدفع، سيتم إرسال مفتاح الترخيص على بريدك الإلكتروني")

    def get_text(self, key):
        """الحصول على النص المترجم"""
        lang_display_name = self.current_language.get()
        lang_code = self.languages.get(lang_display_name, "en")
        return translations[lang_code].get(key, f"KEY_NOT_FOUND: {key}")

    def create_widgets(self):
        """إنشاء واجهة المستخدم"""
        # الإطار العلوي
        frame_top = ttk.Frame(self, padding=(15, 15, 15, 5))
        frame_top.pack(fill="x", padx=15, pady=10)
        
        self.title_label_widget = ttk.Label(frame_top, text=self.get_text("app_title"), style="Title.TLabel")
        self.title_label_widget.pack(side="top", pady=(0, 15))

        # إطار أدوات التحكم
        control_frame = ttk.Frame(frame_top)
        control_frame.pack(fill="x", pady=5)
        
        # صف الإدخالات
        input_frame = ttk.Frame(control_frame)
        input_frame.pack(fill="x", pady=5)
        
        # قيم افتراضية للمتغيرات
        self.symbol_var.set(symbols_list[0])
        self.interval_var.set("1h")
        self.chart_type_var.set("Candlestick")
        self.indicators_var.set("All")
        
        # عناصر التحكم
        controls = [
            ("select_symbol", self.symbol_var, symbols_list[:3] if not self.premium_status else symbols_list, "symbol_combo"),
            ("time_interval", self.interval_var, ["1h", "4h"] if not self.premium_status else intervals_list, "interval_combo"),
            ("chart_type", self.chart_type_var, ["Candlestick", "Line"] if not self.premium_status else chart_types, "chart_combo"),
            ("indicators", self.indicators_var, indicator_types, "indicator_combo")
        ]
        
        # تخزين العناصر للوصول إليها لاحقًا
        self.control_labels = {}
        
        for i, (label_key, var, values, combo_name) in enumerate(controls):
            frame = ttk.Frame(input_frame)
            frame.pack(side="left", padx=5, fill="x", expand=True)
            
            # تخزين التسميات للوصول إليها عند تغيير اللغة
            label = ttk.Label(frame, text=self.get_text(label_key))
            label.pack(anchor="w")
            self.control_labels[label_key] = label
            
            combo = ttk.Combobox(frame, textvariable=var, values=values, state="readonly")
            combo.pack(fill="x", pady=2)
            setattr(self, combo_name, combo)
        
        # أزرار التحكم
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill="x", pady=10)
        
        buttons = [
            ("analyze_button", self.run_analysis),
            ("update_api_button", self.update_api_key),
            ("language_label", None),
            ("premium_features", self.activate_premium)
        ]
        
        self.control_buttons = {}
        
        for btn_key, command in buttons:
            if btn_key == "language_label":
                frame = ttk.Frame(button_frame)
                frame.pack(side="left", padx=5)
                
                lang_label = ttk.Label(frame, text=self.get_text("language_label"))
                lang_label.pack()
                self.language_combo = ttk.Combobox(frame, textvariable=self.current_language, 
                                                  values=list(self.languages.keys()), state="readonly", width=10)
                self.language_combo.pack()
                self.language_combo.bind("<<ComboboxSelected>>", lambda e: self.update_language())
            else:
                if btn_key == "premium_features":
                    text = self.get_text("free_version") if not self.premium_status else self.get_text("premium_activated")
                    state = "normal" if not self.premium_status else "disabled"
                    style = "TButton" if self.premium_status else "Premium.TButton"
                    btn = ttk.Button(button_frame, text=text, command=command, 
                                    style=style, state=state)
                    self.premium_button = btn  # تخزين كمرجع لتحديثه لاحقًا
                else:
                    btn = ttk.Button(button_frame, text=self.get_text(btn_key), command=command)
                
                btn.pack(side="left", padx=5)
                self.control_buttons[btn_key] = btn
        
        # إطار الأزرار السفلي أولاً - يجب أن يكون قبل المحتوى الرئيسي
        button_bottom_frame = ttk.Frame(self, padding=(10, 5, 10, 10))
        button_bottom_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        
        # الصف الأول: أزرار التواصل والتعليم
        row1_frame = ttk.Frame(button_bottom_frame)
        row1_frame.pack(fill="x", pady=(0, 5))
        
        self.contact_button = ttk.Button(row1_frame, text=self.get_text("contact_button"), 
                  command=self.open_contact_page, width=15)
        self.contact_button.pack(side="left", padx=3)
        
        self.education_button = ttk.Button(row1_frame, text=self.get_text("education_button"), 
                  command=self.open_educational_page, width=15)
        self.education_button.pack(side="left", padx=3)
        
        # الصف الثاني: أزرار المشاركة والتحليل
        row2_frame = ttk.Frame(button_bottom_frame)
        row2_frame.pack(fill="x")
        
        self.auto_trade_button = ttk.Button(row2_frame, text=self.get_text("auto_trade_button"), 
                                  command=self.export_trading_signal, style="TButton", width=15)
        self.auto_trade_button.pack(side="left", padx=3)
        
        self.pdf_button = ttk.Button(row2_frame, text=self.get_text("pdf_button"), command=self.save_as_pdf, 
                                  style="Premium.TButton" if self.premium_status else "TButton", width=12)
        self.pdf_button.pack(side="left", padx=3)
        
        self.whatsapp_button = ttk.Button(row2_frame, text=self.get_text("whatsapp_share"), 
                                         command=self.share_whatsapp, style="TButton", width=12)
        self.whatsapp_button.pack(side="left", padx=3)
        
        self.telegram_button = ttk.Button(row2_frame, text=self.get_text("telegram_share"), 
                                         command=self.share_telegram, style="TButton", width=12)
        self.telegram_button.pack(side="left", padx=3)
        
        self.twitter_button = ttk.Button(row2_frame, text=self.get_text("twitter_share"), 
                                        command=self.share_twitter, style="TButton", width=12)
        self.twitter_button.pack(side="left", padx=3)

        self.daily_analysis_button = ttk.Button(row2_frame, text=self.get_text("daily_analysis_button"), 
                                               command=self.trigger_daily_analysis, style="TButton", width=15)
        self.daily_analysis_button.pack(side="left", padx=3)
        
        # زر VIP Bot
        self.vip_bot_button = ttk.Button(row2_frame, text="🤖 VIP Bot", 
                                         command=self.launch_vip_system, style="Premium.TButton", width=12)
        self.vip_bot_button.pack(side="left", padx=3)
        
        # الإطار الرئيسي للمحتوى
        main_content_frame = ttk.Frame(self)
        main_content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # منطقة النتائج النصية
        text_frame = ttk.Frame(main_content_frame)
        text_frame.pack(side="left", fill="both", padx=(0, 10))
        
        self.text_output = tk.Text(text_frame, height=25, width=50, font=("Arial", 11), 
                                  bg="#34495e", fg="white", wrap="word", relief="flat", borderwidth=0)
        scrollbar = ttk.Scrollbar(text_frame, command=self.text_output.yview)
        self.text_output.configure(yscrollcommand=scrollbar.set)
        self.text_output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # منطقة الرسم البياني
        chart_frame = ttk.Frame(main_content_frame)
        chart_frame.pack(side="right", fill="both", expand=True)
        
        self.fig = plt.figure(figsize=(8, 5), facecolor="#2c3e50")
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)
        
        # شريط أدوات الرسم البياني
        toolbar_frame = ttk.Frame(chart_frame)
        toolbar_frame.pack(fill="x")
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

    def update_api_key(self):
        api_key = simpledialog.askstring(self.get_text("update_api_button"), self.get_text("enter_api_key"), parent=self)
        if api_key:
            global API_KEY
            API_KEY = api_key
            messagebox.showinfo(self.get_text("api_key_updated"), self.get_text("api_key_success_message"))
            self.run_analysis()

    def update_language(self):
        self.title(self.get_text("app_title"))
        self.title_label_widget.config(text=self.get_text("app_title"))
        
        # تحديث التسميات
        self.control_labels["select_symbol"].config(text=self.get_text("select_symbol"))
        self.control_labels["time_interval"].config(text=self.get_text("time_interval"))
        self.control_labels["chart_type"].config(text=self.get_text("chart_type"))
        self.control_labels["indicators"].config(text=self.get_text("indicators"))
        
        # تحديث الأزرار
        self.control_buttons["analyze_button"].config(text=self.get_text("analyze_button"))
        self.control_buttons["update_api_button"].config(text=self.get_text("update_api_button"))
        
        # تحديث أزرار الشريط السفلي
        self.contact_button.config(text=self.get_text("contact_button"))
        self.education_button.config(text=self.get_text("education_button"))
        self.pdf_button.config(text=self.get_text("pdf_button"))
        self.whatsapp_button.config(text=self.get_text("whatsapp_share"))
        self.telegram_button.config(text=self.get_text("telegram_share"))
        self.twitter_button.config(text=self.get_text("twitter_share"))
        self.auto_trade_button.config(text=self.get_text("auto_trade_button"))
        self.daily_analysis_button.config(text=self.get_text("daily_analysis_button"))
        
        # تحديث زر النسخة المدفوعة
        if not self.premium_status:
            self.premium_button.config(text=self.get_text("free_version"))
        else:
            if ACTIVATION_INFO["license_key"] == DEVELOPER_LICENSE_KEY:
                self.premium_button.config(text=self.get_text("developer_version"), style="Developer.TButton")
            else:
                self.premium_button.config(text=self.get_text("premium_activated"), style="Premium.TButton")
                
        # إعادة التحليل لتحديث النصوص
        self.run_analysis()

    def run_analysis(self):
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()
        
        if not self.premium_status:
            allowed_pairs = ["EUR/USD", "USD/JPY", "GBP/USD"]
            allowed_intervals = ["1h", "4h"]
            
            if symbol not in allowed_pairs:
                messagebox.showwarning("النسخة المجانية", "هذا الزوج متاح فقط في النسخة المدفوعة")
                return
                
            if interval not in allowed_intervals:
                messagebox.showwarning("النسخة المجانية", "هذه الفترة الزمنية متاحة فقط في النسخة المدفوعة")
                return
        
        self.text_output.delete(1.0, tk.END)
        self.ax.clear()

        try:
            df = fetch_data(symbol, interval)
        except DataFetchError as e:
            messagebox.showerror(self.get_text("no_data_fetch_error"), str(e))
            return

        if len(df) < 50:
            messagebox.showwarning(self.get_text("not_enough_data_warning"), self.get_text("not_enough_data_analysis"))
            try:
                df = fetch_data(symbol, interval, outputsize=500) 
                if len(df) < 50:
                    self.text_output.insert(tk.END, self.get_text("not_enough_data_analysis"))
                    self.text_output.insert(tk.END, "\n⚠️ بعض المؤشرات تتطلب بيانات أكثر ولن تظهر")
                    self.canvas.draw()
                    return
            except DataFetchError as e:
                self.text_output.insert(tk.END, f"{self.get_text('no_data_fetch_error')}: {str(e)}")
                self.canvas.draw()
                return
            except Exception as e:
                self.text_output.insert(tk.END, f"{self.get_text('no_data_fetch_error')}: {str(e)}")
                self.canvas.draw()
                return
            # Add a finally clause to satisfy the try statement requirement
            finally:
                pass
        
        df = analyze(df, self.indicators_var.get())
        signals, recommendation, levels, fib_levels = detect_signals(df, interval, self)

        # تخزين البيانات للملخص اليومي والمشاركة
        pair_key = f"{symbol}_{interval}"
        analysis_data = {
            'symbol': symbol,
            'interval': interval,
            'recommendation': recommendation,
            'entry_price': levels.get('entry_price', 0) if levels else 0,
            'tp1': levels.get('tp1', 0) if levels else 0,
            'tp2': levels.get('tp2', 0) if levels else 0,
            'tp3': levels.get('tp3', 0) if levels else 0,
            'sl': levels.get('sl', 0) if levels else 0,
            'signals': signals,
            'fib_levels': fib_levels,
            'current_price': df['Close'].iloc[-1] if not df.empty else 0,
            'rsi': df['RSI'].iloc[-1] if 'RSI' in df.columns and not df['RSI'].empty else 0,
            'macd': df['MACD'].iloc[-1] if 'MACD' in df.columns and not df['MACD'].empty else 0,
            'atr': df['ATR'].iloc[-1] if 'ATR' in df.columns and not df['ATR'].empty else 0,
            'pivot_point': levels.get('Pivot Point', 0) if levels else 0,
            'resistance_1': levels.get('Resistance 1', 0) if levels else 0,
            'resistance_2': levels.get('Resistance 2', 0) if levels else 0,
            'support_1': levels.get('Support 1', 0) if levels else 0,
            'support_2': levels.get('Support 2', 0) if levels else 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        pairs_analysis[pair_key] = analysis_data
        self.last_analysis_data = analysis_data
        
        # التحقق من افتتاح السوق وإرسال التحليل
        send_market_open_analysis()
        
        # إرسال الملخص اليومي مرة واحدة فقط
        if not daily_summary_sent.get('sent_today'):
            send_daily_summary(pairs_analysis)
            daily_summary_sent['sent_today'] = True

        # إرسال فوري للتوصيات القوية على أي فريم
        if "شراء قوي" in recommendation or "بيع قوي" in recommendation:
            sent, info = send_strong_recommendation(symbol, interval, recommendation, levels)
            if sent:
                self.text_output.insert(tk.END, f"✅ تم إرسال التوصية القوية إلى تلجرام\n\n", "important")

        # Apply appropriate style based on recommendation strength
        if "قوي" in recommendation and "شراء" in recommendation:
            rec_style = "StrongBuy.TLabel"
        elif "شراء" in recommendation:
            rec_style = "Buy.TLabel"
        elif "قوي" in recommendation and "بيع" in recommendation:
            rec_style = "StrongSell.TLabel"
        elif "بيع" in recommendation:
            rec_style = "Sell.TLabel"
        else:
            rec_style = "Neutral.TLabel"
        
        self.text_output.tag_configure("recommendation", foreground="#1abc9c", font=("Arial", 12, "bold"))
        self.text_output.insert(tk.END, f"🔔 {self.get_text('recommendation_title')} ", "recommendation")
        self.text_output.insert(tk.END, f"{recommendation}\n\n", rec_style)
        
        self.text_output.tag_configure("section_title", foreground="#3498db", font=("Arial", 11, "bold"))
        self.text_output.insert(tk.END, f"📋 {self.get_text('signals_title')}\n", "section_title")
        
        for sig in signals:
            if "⚡" in sig:
                self.text_output.tag_configure("important", foreground="#e74c3c")
                self.text_output.insert(tk.END, f"  {sig}\n", "important")
            elif "➡️" in sig:
                self.text_output.tag_configure("warning", foreground="#f39c12")
                self.text_output.insert(tk.END, f"  {sig}\n", "warning")
            else:
                self.text_output.insert(tk.END, f"  {sig}\n")
        
        self.text_output.insert(tk.END, f"\n⚡ {self.get_text('levels_title')}\n", "section_title")
        
        level_keys = ["Entry Price", "SL", "TP1", "TP2", "TP3", "Pivot Point", "Resistance 1", "Resistance 2", "Support 1", "Support 2"]
        level_labels = {
            "Entry Price": "سعر الدخول",
            "SL": "وقف الخسارة",
            "TP1": "جني الربح 1",
            "TP2": "جني الربح 2",
            "TP3": "جني الربح 3",
            "Pivot Point": "نقطة الارتكاز",
            "Resistance 1": "المقاومة 1",
            "Resistance 2": "المقاومة 2",
            "Support 1": "الدعم 1",
            "Support 2": "الدعم 2"
        }
        
        for key in level_keys:
            if key in levels:
                value = levels[key]
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.5f}"
                else:
                    formatted_value = str(value)
                
                if key in ["SL", "TP1", "TP2", "TP3"]:
                    self.text_output.tag_configure("key_important", foreground="#e74c3c")
                    self.text_output.insert(tk.END, f"  • {level_labels[key]}: ", "key_important")
                    self.text_output.insert(tk.END, f"{formatted_value}\n", "key_important")
                else:
                    self.text_output.insert(tk.END, f"  • {level_labels[key]}: {formatted_value}\n")

        plot_df = df.tail(100)

        if self.chart_type_var.get() == "Line":
            self.ax.plot(plot_df["Date"], plot_df["Close"], label=self.get_text("current_price"), color="cyan", linewidth=1.5)
        else:
            df_ohlc = plot_df[["Date", "Open", "High", "Low", "Close"]].copy()
            df_ohlc["Date"] = mdates.date2num(df_ohlc["Date"].dt.to_pydatetime())
            candlestick_ohlc(self.ax, df_ohlc.values, width=0.015 * (plot_df['Date'].iloc[-1] - plot_df['Date'].iloc[0]).total_seconds() / (86400 * len(plot_df)), colorup='#2ecc71', colordown='#e74c3c', alpha=0.8)

        # Plot indicators
        if "BB_High" in plot_df and not plot_df["BB_High"].isnull().all():
            self.ax.plot(plot_df["Date"], plot_df["BB_High"], label="BB High", color="red", linestyle="--", linewidth=0.8)
        if "BB_Low" in plot_df and not plot_df["BB_Low"].isnull().all():
            self.ax.plot(plot_df["Date"], plot_df["BB_Low"], label="BB Low", color="green", linestyle="--", linewidth=0.8)
        if "BB_Mid" in plot_df and not plot_df["BB_Mid"].isnull().all():
            self.ax.plot(plot_df["Date"], plot_df["BB_Mid"], label="BB Mid", color="yellow", linestyle="--", linewidth=0.8)
        if "EMA_50" in plot_df and not plot_df["EMA_50"].isnull().all():
            self.ax.plot(plot_df["Date"], plot_df["EMA_50"], label="EMA 50", color="orange", linewidth=1.0)
        if "EMA_200" in plot_df and not plot_df["EMA_200"].isnull().all():
            self.ax.plot(plot_df["Date"], plot_df["EMA_200"], label="EMA 200", color="purple", linewidth=1.0)

        # Plot Fibonacci levels
        for level_name, price in fib_levels.items():
            if not np.isnan(price):
                color = "#9b59b6" if "23.6%" in level_name else "#3498db" if "38.2%" in level_name else "#2ecc71" if "50.0%" in level_name else "#f1c40f" if "61.8%" in level_name else "#e74c3c"
                self.ax.axhline(price, linestyle=":", label=f"Fib {level_name}", color=color, alpha=0.7, linewidth=0.8)
        
        # Plot support/resistance levels
        pp_val = levels.get("Pivot Point")
        if pp_val and not np.isnan(pp_val):
            self.ax.axhline(pp_val, linestyle="-.", label=self.get_text("pivot_point_label"), color="white", linewidth=1.2)
        r1_val = levels.get("Resistance 1")
        if r1_val and not np.isnan(r1_val):
             self.ax.axhline(r1_val, linestyle="--", label=f"R1: {round(r1_val,5)}", color="#f1c40f", linewidth=0.9)
        s1_val = levels.get("Support 1")
        if s1_val and not np.isnan(s1_val):
             self.ax.axhline(s1_val, linestyle="--", label=f"S1: {round(s1_val,5)}", color="#3498db", linewidth=0.9)

        # Plot Stochastic Oscillator
        if "STOCH_K" in plot_df and "STOCH_D" in plot_df:
            ax2 = self.ax.twinx()
            ax2.plot(plot_df["Date"], plot_df["STOCH_K"], label="Stoch %K", color="blue", linewidth=0.8)
            ax2.plot(plot_df["Date"], plot_df["STOCH_D"], label="Stoch %D", color="red", linewidth=0.8)
            ax2.axhline(80, color='gray', linestyle='--', alpha=0.5)
            ax2.axhline(20, color='gray', linestyle='--', alpha=0.5)
            ax2.set_ylim(0, 100)
            ax2.set_ylabel("Stochastic", color="white")
            ax2.tick_params(axis='y', colors='white')
            ax2.legend(loc="upper right")

        # Format chart
        self.ax.set_title(f"{self.get_text('analyze_title')} {symbol} - {self.get_text('time_interval')}: {interval}", color="white", fontsize=14)
        self.ax.set_xlabel(self.get_text("time_interval"), color="white")
        self.ax.set_ylabel(self.get_text("current_price"), color="white")

        if len(plot_df) > 0:
            if interval in ["1day", "4h", "1h"]:
                self.ax.xaxis.set_major_locator(mdates.DayLocator())
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            elif interval in ["30min", "15min", "5min"]:
                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            else:
                self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            
            plt.setp(self.ax.get_xticklabels(), rotation=30, ha="right")

        self.ax.legend(loc="best", fontsize="small", facecolor="#2c3e50", edgecolor="white", labelcolor="white", framealpha=0.7)
        self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
        self.ax.set_facecolor("#34495e")
        self.fig.patch.set_facecolor("#2c3e50")
        
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.fig.tight_layout()

        self.canvas.draw()

    def save_as_pdf(self):
        if not self.premium_status:
            messagebox.showinfo(self.get_text("premium_pdf"), self.get_text("premium_pdf"))
            return
            
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Use a font that supports Arabic
            pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
            pdf.add_font('DejaVuB', '', 'DejaVuSansCondensed-Bold.ttf', uni=True)
            
            symbol = self.symbol_var.get()
            interval = self.interval_var.get()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            pdf.set_font('DejaVuB', '', 16)
            pdf.cell(0, 10, f"{self.get_text('app_title')} - تقرير تحليل فني", 0, 1, 'C')
            pdf.set_font('DejaVu', '', 12)
            pdf.cell(0, 10, f"الزوج: {symbol} | الفترة: {interval} | تاريخ الإصدار: {current_time}", 0, 1, 'C')
            pdf.ln(10)
            
            analysis_text = self.text_output.get(1.0, tk.END)
            pdf.set_font('DejaVu', '', 11)
            pdf.multi_cell(0, 8, analysis_text)
            pdf.ln(10)
            
            chart_path = "temp_chart.png"
            self.fig.savefig(chart_path, facecolor='#2c3e50', dpi=100)
            
            pdf.image(chart_path, x=10, w=190)
            
            if self.premium_status:
                pdf.set_font('DejaVu', '', 10)
                pdf.set_text_color(200, 200, 200)
                if ACTIVATION_INFO["license_key"] == DEVELOPER_LICENSE_KEY:
                    pdf.text(10, 280, "MoneyMakerApp - نسخة المطور")
                else:
                    pdf.text(10, 280, "MoneyMakerApp - النسخة المدفوعة")

            
            os.remove(chart_path)
            
            filename = f"MoneyMakers_{symbol.replace('/', '_')}_{interval}_{current_time.replace(':', '-')}.pdf"
            pdf.output(filename)
            
            messagebox.showinfo(self.get_text("pdf_success"), 
                              f"{self.get_text('pdf_success')}\nتم حفظ الملف باسم: {filename}")
        except Exception as e:
            messagebox.showerror(self.get_text("pdf_error"), f"{self.get_text('pdf_error')}: {str(e)}")

    def open_contact_page(self):
        messagebox.showinfo(self.get_text("contact_button"), self.get_text("contact_message"))

    def open_educational_page(self):
        messagebox.showinfo(self.get_text("education_button"), self.get_text("education_message"))

    def generate_full_analysis_report(self, data):
        """توليد تقرير تحليل كامل ومنسق للمشاركة"""
        symbol = data.get('symbol', '')
        interval = data.get('interval', '')
        recommendation = data.get('recommendation', '')
        entry_price = data.get('entry_price', 0)
        tp1 = data.get('tp1', 0)
        tp2 = data.get('tp2', 0)
        tp3 = data.get('tp3', 0)
        sl = data.get('sl', 0)
        current_price = data.get('current_price', 0)
        rsi = data.get('rsi', 0)
        macd = data.get('macd', 0)
        atr = data.get('atr', 0)
        pivot_point = data.get('pivot_point', 0)
        resistance_1 = data.get('resistance_1', 0)
        resistance_2 = data.get('resistance_2', 0)
        support_1 = data.get('support_1', 0)
        support_2 = data.get('support_2', 0)
        timestamp = data.get('timestamp', '')
        signals = data.get('signals', [])
        
        report = f"📊 تحليل شامل - {symbol}\n"
        report += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        report += f"⏰ الإطار الزمني: {interval}\n"
        report += f"🕐 وقت التحليل: {timestamp}\n\n"
        
        report += f"💰 السعر الحالي: {current_price:.5f}\n\n"
        
        report += f"🎯 التوصية: {recommendation}\n\n"
        
        report += "📍 مناطق التداول:\n"
        if entry_price:
            report += f"  🟢 الدخول: {entry_price:.5f}\n"
        if sl:
            report += f"  🔴 وقف الخسارة: {sl:.5f}\n"
        if tp1:
            report += f"  🟡 جني الربح 1: {tp1:.5f}\n"
        if tp2:
            report += f"  🟡 جني الربح 2: {tp2:.5f}\n"
        if tp3:
            report += f"  🟡 جني الربح 3: {tp3:.5f}\n"
        
        report += f"\n📊 المؤشرات الفنية:\n"
        if rsi:
            report += f"  • RSI: {rsi:.2f}\n"
        if macd:
            report += f"  • MACD: {macd:.5f}\n"
        if atr:
            report += f"  • ATR: {atr:.5f}\n"
        
        report += f"\n📈 مستويات الدعم والمقاومة:\n"
        if pivot_point:
            report += f"  • نقطة الارتكاز: {pivot_point:.5f}\n"
        if resistance_1:
            report += f"  • المقاومة 1: {resistance_1:.5f}\n"
        if resistance_2:
            report += f"  • المقاومة 2: {resistance_2:.5f}\n"
        if support_1:
            report += f"  • الدعم 1: {support_1:.5f}\n"
        if support_2:
            report += f"  • الدعم 2: {support_2:.5f}\n"
        
        if signals:
            report += f"\n⚡ إشارات التداول:\n"
            for signal in signals[:5]:  # أول 5 إشارات
                report += f"  • {signal}\n"
        
        report += f"\n━━━━━━━━━━━━━━━━━━━━\n"
        report += "📱 Smart Forex Analyzer"
        
        return report


    def share_whatsapp(self):
        """مشاركة التحليل الكامل على واتساب"""
        if not hasattr(self, 'last_analysis_data') or not self.last_analysis_data:
            messagebox.showinfo(self.get_text("share_unavailable_title"), 
                              self.get_text("share_no_data_message"))
            return
            
        data = self.last_analysis_data
        formatted_text = self.generate_full_analysis_report(data)
        encoded_text = urllib.parse.quote(formatted_text)
        url = f"https://wa.me/?text={encoded_text}"
        webbrowser.open(url)
        messagebox.showinfo(self.get_text("share_success_title"), self.get_text("whatsapp_share_success"))

    def share_telegram(self):
        """مشاركة التحليل الكامل على تلجرام (يدوي فقط، فصل عن البوت الآلي)"""
        if not hasattr(self, 'last_analysis_data') or not self.last_analysis_data:
            messagebox.showinfo(self.get_text("share_unavailable_title"), 
                              self.get_text("share_no_data_message"))
            return
            
        data = self.last_analysis_data
        formatted_text = self.generate_full_analysis_report(data)
        
        # مشاركة يدوية فقط عبر t.me - فصل عن البوت الآلي
        encoded_text = urllib.parse.quote(formatted_text)
        url = f"https://t.me/share/url?url=&text={encoded_text}"
        webbrowser.open(url)
        messagebox.showinfo(self.get_text("share_success_title"), "تم فتح نافذة المشاركة")

    def trigger_daily_analysis(self):
        """تشغيل التحليل الشامل اليومي وإرسال التقارير إلى تيليجرام دون تجميد الواجهة"""
        try:
            self.status_var.set("بدء التحليل اليومي...")
        except Exception:
            pass

        def _run_daily():
            try:
                # الاستيراد داخل المهمة لتجنب مشاكل زمن التحميل
                from auto_pairs_analyzer import run_daily_analysis, send_telegram_message
            except Exception as e:
                try:
                    messagebox.showerror(self.get_text("error_occurred"), f"تعذر تحميل وحدة التحليل التلقائي: {e}")
                except Exception:
                    pass
                return

            try:
                # إرسال إشعار بدء (اختياري)
                try:
                    send_telegram_message("🚀 بدء التحليل اليومي من الواجهة")
                except Exception:
                    pass

                run_daily_analysis()

                try:
                    self.status_var.set("اكتمل التحليل اليومي")
                    messagebox.showinfo("تحليل يومي", "تم تنفيذ التحليل اليومي وإرسال التقارير")
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.status_var.set(self.get_text("error_occurred"))
                    messagebox.showerror(self.get_text("error_occurred"), f"خطأ في التحليل اليومي: {str(e)}")
                except Exception:
                    pass

        threading.Thread(target=_run_daily, daemon=True).start()

    def launch_vip_system(self):
        """تشغيل نظام VIP Bot والمحلل التلقائي"""
        try:
            import subprocess
            import sys
            
            # نافذة تأكيد
            vip_window = tk.Toplevel(self)
            vip_window.title("🤖 تشغيل نظام VIP")
            vip_window.geometry("500x400")
            vip_window.resizable(False, False)
            
            # تمركز النافذة
            vip_window.update_idletasks()
            x = (vip_window.winfo_screenwidth() // 2) - (500 // 2)
            y = (vip_window.winfo_screenheight() // 2) - (400 // 2)
            vip_window.geometry(f"500x400+{x}+{y}")
            
            # محتوى النافذة
            title_frame = ttk.Frame(vip_window)
            title_frame.pack(fill="x", padx=20, pady=20)
            
            ttk.Label(title_frame, text="🚀 نظام التوصيات VIP", 
                     font=("Arial", 18, "bold")).pack()
            ttk.Label(title_frame, text="اختر ما تريد تشغيله:", 
                     font=("Arial", 12)).pack(pady=10)
            
            # معلومات
            info_frame = ttk.LabelFrame(vip_window, text="📊 معلومات النظام", padding=15)
            info_frame.pack(fill="both", padx=20, pady=10)
            
            info_text = """
✅ بوت التليجرام VIP:
   • إدارة الاشتراكات
   • نظام الإحالة
   • 4 خطط (Bronze-Platinum)

✅ المحلل التلقائي:
   • تحليل ساعي لـ 9 أزواج
   • مراقبة الصفقات كل 30 دقيقة
   • إرسال توصيات ذكية
            """
            
            ttk.Label(info_frame, text=info_text, justify="right", 
                     font=("Arial", 10)).pack()
            
            # أزرار التشغيل
            buttons_frame = ttk.Frame(vip_window)
            buttons_frame.pack(fill="x", padx=20, pady=20)
            
            def launch_bot():
                try:
                    # الحصول على مسار Python
                    python_exe = sys.executable
                    vip_bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                                'vip_telegram_bot.py')
                    
                    if os.path.exists(vip_bot_path):
                        subprocess.Popen([python_exe, vip_bot_path], 
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
                        messagebox.showinfo("✅ نجح", "تم تشغيل بوت التليجرام VIP!\nتحقق من النافذة الجديدة")
                        vip_window.destroy()
                    else:
                        messagebox.showerror("❌ خطأ", f"لم يتم العثور على الملف:\n{vip_bot_path}")
                except Exception as e:
                    messagebox.showerror("❌ خطأ", f"فشل تشغيل البوت:\n{str(e)}")
            
            def launch_analyzer():
                try:
                    python_exe = sys.executable
                    scheduler_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                                  'daily_scheduler.py')
                    
                    if os.path.exists(scheduler_path):
                        subprocess.Popen([python_exe, scheduler_path], 
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
                        messagebox.showinfo("✅ نجح", "تم تشغيل المحلل التلقائي!\nتحقق من النافذة الجديدة")
                        vip_window.destroy()
                    else:
                        messagebox.showerror("❌ خطأ", f"لم يتم العثور على الملف:\n{scheduler_path}")
                except Exception as e:
                    messagebox.showerror("❌ خطأ", f"فشل تشغيل المحلل:\n{str(e)}")
            
            def launch_both():
                try:
                    python_exe = sys.executable
                    base_dir = os.path.dirname(os.path.dirname(__file__))
                    vip_bot_path = os.path.join(base_dir, 'vip_telegram_bot.py')
                    scheduler_path = os.path.join(base_dir, 'daily_scheduler.py')
                    
                    if os.path.exists(vip_bot_path) and os.path.exists(scheduler_path):
                        subprocess.Popen([python_exe, vip_bot_path], 
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
                        time.sleep(2)
                        subprocess.Popen([python_exe, scheduler_path], 
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
                        messagebox.showinfo("✅ نجح", "تم تشغيل النظام الكامل!\n\nنافذتان جديدتان:\n• بوت التليجرام VIP\n• المحلل التلقائي")
                        vip_window.destroy()
                    else:
                        messagebox.showerror("❌ خطأ", "لم يتم العثور على أحد الملفات المطلوبة")
                except Exception as e:
                    messagebox.showerror("❌ خطأ", f"فشل تشغيل النظام:\n{str(e)}")
            
            # الأزرار
            ttk.Button(buttons_frame, text="🤖 بوت التليجرام فقط", 
                      command=launch_bot, width=25).pack(pady=5)
            ttk.Button(buttons_frame, text="📊 المحلل التلقائي فقط", 
                      command=launch_analyzer, width=25).pack(pady=5)
            ttk.Button(buttons_frame, text="🚀 النظام الكامل (الكل)", 
                      command=launch_both, width=25).pack(pady=5)
            ttk.Button(buttons_frame, text="❌ إلغاء", 
                      command=vip_window.destroy, width=25).pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل فتح نافذة VIP:\n{str(e)}")

    def share_twitter(self):
        """مشاركة ملخص التحليل على تويتر"""
        if not hasattr(self, 'last_analysis_data') or not self.last_analysis_data:
            messagebox.showinfo(self.get_text("share_unavailable_title"), 
                              self.get_text("share_no_data_message"))
            return
        
        data = self.last_analysis_data
        symbol = data.get('symbol', '')
        interval = data.get('interval', '')
        recommendation = data.get('recommendation', '')
        entry_price = data.get('entry_price', 0)
        tp1 = data.get('tp1', 0)
        sl = data.get('sl', 0)
        
        # نسخة مختصرة لتويتر (حد 280 حرف)
        formatted_text = f"📊 {symbol} {interval}\n"
        formatted_text += f"🎯 {recommendation}\n"
        if entry_price:
            formatted_text += f"💰 Entry: {entry_price:.5f}\n"
        if sl:
            formatted_text += f"🔴 SL: {sl:.5f}\n"
        if tp1:
            formatted_text += f"🟢 TP: {tp1:.5f}\n"
        formatted_text += "#Forex #Trading #TechnicalAnalysis"
        
        encoded_text = urllib.parse.quote(formatted_text[:280]) 
        url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        webbrowser.open(url)
        messagebox.showinfo(self.get_text("share_success_title"), self.get_text("twitter_share_success"))
        
    def generate_trading_signals(self):
        """إنشاء إشارات تداول بتنسيق JSON قابلة للاستخدام الآلي"""
        if not hasattr(self, 'last_analysis_data') or not self.last_analysis_data:
            return None
            
        data = self.last_analysis_data
        symbol = data.get('symbol', '')
        interval = data.get('interval', '')
        recommendation = data.get('recommendation', '')
        entry_price = data.get('entry_price', '')
        tp1 = data.get('tp1', '')
        tp2 = data.get('tp2', '')
        tp3 = data.get('tp3', '')
        sl = data.get('sl', '')
        
        # تحديد نوع الصفقة بناءً على التوصية
        trade_type = "BUY" if "شراء" in recommendation else "SELL" if "بيع" in recommendation else "NEUTRAL"
        
        # تحديد مستوى الثقة
        confidence = "HIGH" if "قوي" in recommendation else "MEDIUM" if not "محتمل" in recommendation else "LOW"
        
        signal = {
            "symbol": symbol.replace("/", ""),
            "trade_type": trade_type,
            "entry_price": round(entry_price, 5),
            "take_profit": [
                round(tp1, 5),
                round(tp2, 5),
                round(tp3, 5)
            ],
            "stop_loss": round(sl, 5),
            "confidence": confidence,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timeframe": interval,
            "recommendation_text": recommendation
        }
        
        return signal

    def export_trading_signal(self):
        """تصدير إشارة التداول للاستخدام الآلي"""
        signal = self.generate_trading_signals()
        
        if not signal:
            messagebox.showinfo(self.get_text("no_trade_signal"), self.get_text("no_trade_signal"))
            return
            
        try:
            # حفظ الإشارة في ملف JSON
            filename = f"MoneyMakers_{signal['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(signal, f, indent=4)
            
            messagebox.showinfo(self.get_text("auto_trade_success"), 
                               f"{self.get_text('auto_trade_success')}\nتم حفظ الإشارة في ملف: {filename}")
        except Exception as e:
            messagebox.showerror(self.get_text("auto_trade_error"), 
                               f"{self.get_text('auto_trade_error')}: {str(e)}")

if __name__ == "__main__":
    app = MoneyMakerApp()
    app.mainloop()
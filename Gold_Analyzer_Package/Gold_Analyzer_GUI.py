import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import requests
import pandas as pd
import ta
import matplotlib.pyplot as plt
import webbrowser
import numpy as np
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
from datetime import datetime, timedelta
import hashlib
import uuid
import json
import os
import base64
from fpdf import FPDF
import time
import platform
import psutil
import threading
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from PIL import Image, ImageTk
from license_manager import check_license, show_license_window

try:
    import nltk  # type: ignore
    nltk.download('vader_lexicon', quiet=True)
    from nltk.sentiment.vader import SentimentIntensityAnalyzer  # type: ignore
    NLTK_AVAILABLE = True
except (ImportError, Exception) as e:
    nltk = None
    SentimentIntensityAnalyzer = None
    NLTK_AVAILABLE = False

class DataFetchError(Exception):
    """Exception raised for data fetching errors."""
    pass

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

DEVELOPER_LICENSE_KEY = "DEV-2024-SMARTFOREX-ANALYZER"
DEVELOPER_EMAIL = "MAHMOODALQAISE750@GMAIL.COM"

# API Configuration
API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://api.example.com/query"

def get_machine_id():
    try:
        system_info = {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "ram": str(round(psutil.virtual_memory().total / (1024 ** 3))) + " GB",
            "mac": ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        }
        return hashlib.sha256(json.dumps(system_info).encode('utf-8')).hexdigest()
    except:
        return str(uuid.uuid4())

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
    
    # RSI
    if indicators in ["All", "RSI"] and len(df) >= 14:
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

    # MACD
    if indicators in ["All", "MACD"] and len(df) >= 26:
        macd = ta.trend.MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9)
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Hist"] = macd.macd_diff()

    # EMAs
    if indicators in ["All", "EMA"] and len(df) >= 50:
        df["EMA_50"] = ta.trend.ema_indicator(df["Close"], window=50)
    
    if indicators in ["All", "EMA"] and len(df) >= 200:
        df["EMA_200"] = ta.trend.ema_indicator(df["Close"], window=200)
    
    return df

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
            df = pd.DataFrame(data["values"])
            df = df.rename(columns={"datetime": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close"})
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values("Date").reset_index(drop=True)
            return df
        except requests.exceptions.RequestException as e:
            attempts += 1
            if attempts < max_attempts:
                time.sleep(2)
                continue
            raise DataFetchError(f"Connection error: {str(e)}")

# نموذج تعلم الآلي لتحليل البيانات
def train_ml_model(df):
    """تدريب نموذج تعلم آلي لتحسين التوصيات بناءً على البيانات."""
    if len(df) < 50:
        return None, None  # يحتاج إلى بيانات أكثر
    
    # إعداد البيانات
    df['RSI'] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df['MACD'] = ta.trend.MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9).macd()
    df['EMA_50'] = ta.trend.ema_indicator(df["Close"], window=50)
    df['EMA_200'] = ta.trend.ema_indicator(df["Close"], window=200)
    df = df.dropna()
    
    # الميزات المستخلصة
    features = ['RSI', 'MACD', 'EMA_50', 'EMA_200']
    target = ['Close']  # نستخدم سعر الإغلاق كهدف

    X = df[features]
    y = df[target]
    
    # القياس
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # استخدام Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y.values.ravel())
    
    return model, scaler

def predict_price(model, scaler, df):
    """التنبؤ بالسعر باستخدام النموذج المدرب"""
    features = ['RSI', 'MACD', 'EMA_50', 'EMA_200']
    X = df[features]
    X_scaled = scaler.transform(X)
    
    prediction = model.predict(X_scaled)
    return prediction[-1]

# كشف الأخبار باستخدام NLTK
def analyze_news_sentiment(news_text):
    """تحليل مشاعر الأخبار باستخدام مكتبة NLTK"""
    nltk.download('vader_lexicon')
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(news_text)
    
    if sentiment['compound'] >= 0.05:
        return "Positive"
    elif sentiment['compound'] <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def detect_signals(df, model, scaler, news=None):
    """كشف الإشارات بناءً على التحليل الفني والنموذج المدرب"""
    entry_price = df.iloc[-1]["Close"]
    prediction = predict_price(model, scaler, df)
    
    # تحليل الأخبار إذا كانت موجودة
    if news:
        sentiment = analyze_news_sentiment(news)
    else:
        sentiment = "Neutral"
    
    # تحديد التوصية بناءً على التحليل الفني والنموذج المدرب
    if prediction > entry_price and sentiment == "Positive":
        return "شراء"
    elif prediction < entry_price and sentiment == "Negative":
        return "بيع"
    else:
        return "انتظار"

# التطبيق الرئيسي
class MoneyMakerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.symbol_var = tk.StringVar()
        self.interval_var = tk.StringVar()
        self.model, self.scaler = None, None
        self.premium_status = PREMIUM_FEATURES
        self.symbol_var.set("EUR/USD")
        self.interval_var.set("1h")

        self.create_widgets()
        self.load_and_train_model()

    def load_and_train_model(self):
        """تحميل البيانات وتدريب النموذج لتحسين التوصيات."""
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()

        try:
            df = fetch_data(symbol, interval)
            df = analyze(df)
            self.model, self.scaler = train_ml_model(df)
            messagebox.showinfo("تدريب النموذج", "تم تدريب النموذج بنجاح!")
        except Exception as e:
            messagebox.showerror("خطأ في تحميل البيانات", str(e))

    def run_analysis(self):
        """تشغيل التحليل باستخدام النموذج المدرب."""
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()
        
        if self.model is None or self.scaler is None:
            messagebox.showerror("النموذج غير مدرب", "يرجى تدريب النموذج أولاً.")
            return
        
        df = fetch_data(symbol, interval)
        df = analyze(df)
        
        # إضافة نص الأخبار لتحليل المشاعر
        news_text = "أخبار السوق الحالية المتعلقة بالعملات..."  # يمكن إضافة الأخبار هنا
        recommendation = detect_signals(df, self.model, self.scaler, news=news_text)
        
        messagebox.showinfo("التوصية", f"التوصية: {recommendation}")

    def create_widgets(self):
        frame_top = ttk.Frame(self, padding=(15, 15, 15, 5))
        frame_top.pack(fill="x", padx=15, pady=10)

        symbol_label = ttk.Label(frame_top, text="اختيار الزوج")
        symbol_label.pack(side="left")
        symbol_combobox = ttk.Combobox(frame_top, textvariable=self.symbol_var, values=["EUR/USD", "GBP/USD", "USD/JPY"])
        symbol_combobox.pack(side="left")
        
        interval_label = ttk.Label(frame_top, text="اختيار الفترة الزمنية")
        interval_label.pack(side="left")
        interval_combobox = ttk.Combobox(frame_top, textvariable=self.interval_var, values=["1h", "4h", "1d"])
        interval_combobox.pack(side="left")

        analyze_button = ttk.Button(frame_top, text="تشغيل التحليل", command=self.run_analysis)
        analyze_button.pack(side="left", padx=5)

if __name__ == "__main__":
    app = MoneyMakerApp()
    app.mainloop()

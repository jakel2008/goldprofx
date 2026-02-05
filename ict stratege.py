import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
import textwrap

# Configuration
API_KEY = "079cdb64bbc8415abcf8f7be7e389349"  # Replace with your API key
BASE_URL = "https://api.twelvedata.com/time_series"

# List of currency pairs and intervals
symbols_list = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "XAU/USD", "XAG/USD", "BTC/USD", "ETH/USD",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/GBP", "CHF/JPY", "CAD/JPY",
    "NZD/JPY", "AUD/NZD", "EUR/CAD", "GBP/CAD", "EUR/AUD", "GBP/AUD"
]

intervals_list = ["1min", "5min", "15min", "30min", "1h", "4h", "1day"]

class DataFetchError(Exception):
    """Custom exception for data fetching errors"""
    pass

def fetch_data(symbol, interval, outputsize=100):
    """Fetch historical data from Twelve Data API"""
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "values" not in data:
            error_message = data.get("message", "Unknown error occurred")
            raise DataFetchError(f"API Error: {error_message}")
        
        df = pd.DataFrame(data["values"])
        df = df.iloc[::-1].reset_index(drop=True)  # Reverse to chronological order
        
        # Convert to numeric and datetime
        df["open"] = pd.to_numeric(df["open"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["close"] = pd.to_numeric(df["close"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.rename(columns={"datetime": "Date"}, inplace=True)
        
        return df
    
    except requests.exceptions.RequestException as e:
        raise DataFetchError(f"Network error: {str(e)}")
    except (KeyError, ValueError) as e:
        raise DataFetchError(f"Data processing error: {str(e)}")

def analyze(df):
    """Add technical indicators to the DataFrame"""
    # Ensure we have enough data
    if len(df) < 50:
        return df
    
    # Moving Averages
    df["EMA_50"] = ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()
    df["EMA_200"] = ta.trend.EMAIndicator(df["close"], window=200).ema_indicator()
    
    # RSI
    df["RSI"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    
    # MACD
    macd = ta.trend.MACD(df["close"])
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["close"])
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    
    # Pivot Points
    df["Pivot"] = (df["high"] + df["low"] + df["close"]) / 3
    df["R1"] = 2 * df["Pivot"] - df["low"]
    df["S1"] = 2 * df["Pivot"] - df["high"]
    
    return df

def detect_signals(df, interval, app):
    """Detect trading signals based on technical indicators"""
    signals = []
    recommendation = app.get_text("neutral_recommendation")
    
    # Ensure we have enough data for analysis
    if len(df) < 50:
        return signals, recommendation, {}, {}
    
    # Get the latest data point
    latest = df.iloc[-1]
    
    # EMA Crossover Signal
    if not pd.isna(latest["EMA_50"]) and not pd.isna(latest["EMA_200"]):
        if latest["EMA_50"] > latest["EMA_200"]:
            signals.append(app.get_text("signal_ema_buy"))
            recommendation = app.get_text("buy_recommendation")
        elif latest["EMA_50"] < latest["EMA_200"]:
            signals.append(app.get_text("signal_ema_sell"))
            recommendation = app.get_text("sell_recommendation")
    
    # RSI Signal
    if not pd.isna(latest["RSI"]):
        if latest["RSI"] > 70:
            signals.append(app.get_text("signal_rsi_overbought"))
        elif latest["RSI"] < 30:
            signals.append(app.get_text("signal_rsi_oversold"))
    
    # MACD Crossover Signal
    if len(df) > 1 and not pd.isna(latest["MACD"]) and not pd.isna(latest["MACD_Signal"]):
        prev = df.iloc[-2]
        if latest["MACD"] > latest["MACD_Signal"] and prev["MACD"] <= prev["MACD_Signal"]:
            signals.append(app.get_text("signal_macd_crossover_buy"))
            recommendation = app.get_text("buy_recommendation")
        elif latest["MACD"] < latest["MACD_Signal"] and prev["MACD"] >= prev["MACD_Signal"]:
            signals.append(app.get_text("signal_macd_crossover_sell"))
            recommendation = app.get_text("sell_recommendation")
    
    # Calculate key levels
    levels = {
        app.get_text("current_price"): latest["close"],
        app.get_text("rsi_label"): latest["RSI"] if not pd.isna(latest["RSI"]) else "N/A",
        app.get_text("macd_label"): f"{latest['MACD']:.5f}" if not pd.isna(latest["MACD"]) else "N/A",
        app.get_text("pivot_point_label"): latest["Pivot"],
        app.get_text("resistance_label"): f"{latest['R1']:.5f}",
        app.get_text("support_label"): f"{latest['S1']:.5f}"
    }
    
    # Calculate Fibonacci levels
    fib_levels = {}
    if len(df) > 20:
        high = df["high"].tail(20).max()
        low = df["low"].tail(20).min()
        
        fib_levels["0.0"] = high
        fib_levels["0.236"] = high - (high - low) * 0.236
        fib_levels["0.382"] = high - (high - low) * 0.382
        fib_levels["0.5"] = high - (high - low) * 0.5
        fib_levels["0.618"] = high - (high - low) * 0.618
        fib_levels["1.0"] = low
    
    return signals, recommendation, levels, fib_levels

def detect_ict_signals(data, app):
    """Detect ICT (Inner Circle Trader) trading signals based on price action analysis"""
    signals = {
        'market_structure': app.get_text("neutral_structure"),
        'market_phase': app.get_text("accumulation_phase"),
        'liquidity_levels': [],
        'market_shift': app.get_text("no_significant_shift"),
        'key_levels': "",
        'primary_scenario': "",
        'alternative_scenario': "",
        'entry_strategy': "",
        'risk_management': "",
        'recommendation': app.get_text("neutral_recommendation"),
        'fair_value_gaps': [],
        'entry_points': [],
        'take_profit': [],
        'stop_loss': None,
        'ist_details': ""
    }
    
    # Check if we have enough data
    if len(data) < 50:
        return signals
    
    # Extract recent price action (last 50 candles)
    recent_data = data.tail(50)
    high = recent_data['high'].max()
    low = recent_data['low'].min()
    close = recent_data['close'].iloc[-1]
    
    # Determine market structure
    if close > recent_data['close'].iloc[-5]:
        signals['market_structure'] = app.get_text("bullish_structure")
    elif close < recent_data['close'].iloc[-5]:
        signals['market_structure'] = app.get_text("bearish_structure")
    
    # Identify liquidity levels (recent swing highs and lows)
    swing_highs = recent_data[recent_data['high'] == recent_data['high'].rolling(5, center=True).max()]['high']
    swing_lows = recent_data[recent_data['low'] == recent_data['low'].rolling(5, center=True).min()]['low']
    
    signals['liquidity_levels'] = list(set(swing_highs.tolist() + swing_lows.tolist()))
    
    # Identify key levels (pivot points)
    pivot_point = (high + low + close) / 3
    r1 = 2 * pivot_point - low
    s1 = 2 * pivot_point - high
    signals['key_levels'] = f"PP: {round(pivot_point, 5)}, R1: {round(r1, 5)}, S1: {round(s1, 5)}"
    
    # Detect fair value gaps (FVG)
    for i in range(2, len(recent_data)):
        candle1 = recent_data.iloc[i-2]
        candle2 = recent_data.iloc[i-1]
        candle3 = recent_data.iloc[i]
        
        # Bullish FVG: current candle low > previous candle high
        if candle3['low'] > candle2['high']:
            signals['fair_value_gaps'].append({
                'type': 'Bullish',
                'price': candle2['high'] + (candle3['low'] - candle2['high']) / 2,
                'start': candle2['Date'],
                'end': candle3['Date']
            })
        # Bearish FVG: current candle high < previous candle low
        elif candle3['high'] < candle2['low']:
            signals['fair_value_gaps'].append({
                'type': 'Bearish',
                'price': candle2['low'] - (candle2['low'] - candle3['high']) / 2,
                'start': candle2['Date'],
                'end': candle3['Date']
            })
    
    # Determine market phase based on RSI
    rsi = ta.momentum.RSIIndicator(recent_data['close'], window=14).rsi().iloc[-1]
    if 30 < rsi < 70:
        signals['market_phase'] = app.get_text("accumulation_phase")
    elif rsi > 70:
        signals['market_phase'] = app.get_text("distribution_phase")
    else:
        signals['market_phase'] = app.get_text("manipulation_phase")
    
    # Identify market shift points
    if abs(rsi - 50) > 20:
        signals['market_shift'] = app.get_text("bullish_shift") if rsi < 30 else app.get_text("bearish_shift")
    
    # Generate trading scenarios
    if signals['market_structure'] == app.get_text("bullish_structure"):
        signals['primary_scenario'] = app.get_text("primary_scenario") + ": " + textwrap.fill(
            "Price is in an uptrend. Look for buying opportunities at support levels with targets at recent highs.",
            width=60
        )
        signals['alternative_scenario'] = app.get_text("alternative_scenario") + ": " + textwrap.fill(
            "If price breaks below key support, it could indicate trend reversal. Watch for bearish reversal patterns.",
            width=60
        )
        signals['recommendation'] = app.get_text("buy_recommendation")
        signals['entry_strategy'] = textwrap.fill(
            "Enter long positions near support levels (S1) or bullish fair value gaps with confirmation.",
            width=60
        )
    elif signals['market_structure'] == app.get_text("bearish_structure"):
        signals['primary_scenario'] = app.get_text("primary_scenario") + ": " + textwrap.fill(
            "Price is in a downtrend. Look for selling opportunities at resistance levels with targets at recent lows.",
            width=60
        )
        signals['alternative_scenario'] = app.get_text("alternative_scenario") + ": " + textwrap.fill(
            "If price breaks above key resistance, it could indicate trend reversal. Watch for bullish reversal patterns.",
            width=60
        )
        signals['recommendation'] = app.get_text("sell_recommendation")
        signals['entry_strategy'] = textwrap.fill(
            "Enter short positions near resistance levels (R1) or bearish fair value gaps with confirmation.",
            width=60
        )
    else:
        signals['primary_scenario'] = app.get_text("primary_scenario") + ": " + textwrap.fill(
            "Price is ranging. Trade the range between support and resistance levels.",
            width=60
        )
        signals['alternative_scenario'] = app.get_text("alternative_scenario") + ": " + textwrap.fill(
            "If price breaks out of range with volume, follow the breakout direction.",
            width=60
        )
        signals['entry_strategy'] = textwrap.fill(
            "Enter positions at range boundaries with tight stop losses.",
            width=60
        )
    
    # Risk management
    signals['risk_management'] = textwrap.fill(
        "Use 1:2 risk-reward ratio. Set stop loss below key support for longs, above resistance for shorts. Never risk more than 1% of account per trade.",
        width=60
    )
    
    # Generate entry points based on Fibonacci retracement
    if len(signals['liquidity_levels']) >= 2:
        high_level = max(signals['liquidity_levels'])
        low_level = min(signals['liquidity_levels'])
        
        # Fibonacci retracement levels
        fib_382 = high_level - (high_level - low_level) * 0.382
        fib_618 = high_level - (high_level - low_level) * 0.618
        
        if signals['market_structure'] == app.get_text("bullish_structure"):
            signals['entry_points'] = [fib_618, fib_382]
        elif signals['market_structure'] == app.get_text("bearish_structure"):
            signals['entry_points'] = [fib_382, fib_618]
        else:
            signals['entry_points'] = [fib_618, fib_382]
    
    # Take profit levels
    if signals['entry_points']:
        entry = signals['entry_points'][0]
        if signals['market_structure'] == app.get_text("bullish_structure"):
            signals['take_profit'] = [entry + (high - entry) * 0.5, entry + (high - entry) * 1.0]
            signals['stop_loss'] = entry - (entry - low) * 0.1
        elif signals['market_structure'] == app.get_text("bearish_structure"):
            signals['take_profit'] = [entry - (entry - low) * 0.5, entry - (entry - low) * 1.0]
            signals['stop_loss'] = entry + (high - entry) * 0.1
        else:
            signals['take_profit'] = [entry + (high - entry) * 0.5, entry - (entry - low) * 0.5]
            signals['stop_loss'] = entry * 0.995  # 0.5% stop loss
    
    # IST analysis details
    signals['ist_details'] = textwrap.fill(
        f"Comprehensive Institutional Strategy Analysis: The market is currently in the {signals['market_phase']}. "
        f"Key levels to watch are {signals['key_levels']}. Recent price action shows {len(signals['fair_value_gaps'])} "
        "fair value gaps. Institutional activity suggests following the primary scenario with appropriate risk management.",
        width=60
    )
    
    return signals

class MoneyMakerApp(tk.Tk):
    translations = {
        "ar": {
            "app_title": "محلل الفوركس الذكي",
            "select_symbol": "اختر زوج العملات:",
            "time_interval": "الفترة الزمنية:",
            "chart_type": "نوع الرسم البياني:",
            "analyze_button": "تحليل السوق",
            "update_api_button": "تحديث مفتاح API",
            "language_label": "اللغة:",
            "contact_button": "تواصل معنا",
            "education_button": "القسم التعليمي",
            "whatsapp_share": "واتساب",
            "telegram_share": "تليجرام",
            "twitter_share": "تويتر",
            "recommendation_title": "التوصية:",
            "signals_title": "إشارات وتحليل السوق:",
            "levels_title": "مستويات جني الأرباح ووقف الخسارة:",
            "current_price": "السعر الحالي:",
            "rsi_label": "RSI:",
            "macd_label": "MACD:",
            "pivot_point_label": "نقطة الارتكاز:",
            "resistance_label": "المقاومة (R1/R2):",
            "support_label": "الدعم (S1/S2):",
            "fibonacci_title": "مستويات فيبوناتشي:",
            "no_data_fetch_error": "خطأ في جلب البيانات",
            "not_enough_data_warning": "بيانات غير كافية",
            "not_enough_data_analysis": "لا توجد بيانات كافية للتحليل.",
            "update_api_title": "تحديث مفتاح API",
            "enter_api_key": "أدخل مفتاح API الجديد:",
            "api_key_updated": "تم التحديث",
            "api_key_success_message": "تم تحديث مفتاح API بنجاح!",
            "share_unavailable_title": "المشاركة غير متاحة",
            "share_no_data_message": "لا توجد بيانات لمشاركتها.",
            "share_success_title": "تمت المشاركة",
            "whatsapp_share_success": "تم مشاركة التوصية بنجاح على واتساب!",
            "telegram_share_success": "تم مشاركة التوصية بنجاح على تليجرام!",
            "twitter_share_success": "تم مشاركة التوصية بنجاح على تويتر!",
            "neutral_recommendation": "حياد",
            "buy_recommendation": "شراء",
            "sell_recommendation": "بيع",
            "signal_ema_buy": "إشارة شراء (EMA 50 يتقاطع فوق EMA 200 - اتجاه صاعد)",
            "signal_ema_sell": "إشارة بيع (EMA 50 يتقاطع تحت EMA 200 - اتجاه هابط)",
            "signal_rsi_overbought": "RSI في منطقة الشراء المفرط (أعلى من 70)",
            "signal_rsi_oversold": "RSI في منطقة البيع المفرط (أقل من 30)",
            "signal_macd_crossover_buy": "إشارة شراء (MACD يتقاطع فوق خط الإشارة)",
            "signal_macd_crossover_sell": "إشارة بيع (MACD يتقاطع تحت خط الإشارة)",
            "analyze_title": "تحليل فني لـ",
            "contact_message": "للتواصل، يرجى إرسال بريد إلكتروني إلى: support@example.com",
            "education_message": "تفضل بزيارة قسمنا التعليمي على: example.com/education",
            "telegram_share_message": "تمت المشاركة من خلال محلل الفوركس الذكي",
            "currency_pair_label": "زوج العملات:",
            "ict_analysis_button": "تحليل ICT",
            "ict_title": "تحليل استراتيجية ICT",
            "liquidity_levels": "مستويات السيولة:",
            "market_structure": "هيكل السوق:",
            "fair_value_gaps": "فجوات القيمة العادلة:",
            "order_blocks": "كتل الأوامر:",
            "entry_points": "نقاط الدخول:",
            "take_profit": "جني الأرباح:",
            "stop_loss": "وقف الخسارة:",
            "optimal_entry": "نقطة الدخول المثالية:",
            "ict_buy_signal": "إشارة شراء (ICT)",
            "ict_sell_signal": "إشارة بيع (ICT)",
            "bullish_structure": "هيكل صاعد",
            "bearish_structure": "هيكل هابط",
            "neutral_structure": "هيكل محايد",
            "market_structure_label": "هيكل السوق:",
            "liquidity_zones": "مناطق السيولة:",
            "fvg_label": "فجوات القيمة العادلة:",
            "ote_label": "نقاط الدخول المثلى (OTE):",
            "tp_label": "أهداف جني الأرباح:",
            "sl_label": "وقف الخسارة:",
            "scenario_title": "سيناريو التداول",
            "primary_scenario": "السيناريو الرئيسي:",
            "alternative_scenario": "السيناريو البديل:",
            "ist_title": "تحليل الـ IST المتكامل",
            "market_phase": "مرحلة السوق الحالية:",
            "market_shift": "نقاط التحول في السوق:",
            "key_levels": "المستويات الرئيسية:",
            "entry_strategy": "استراتيجية الدخول:",
            "risk_management": "إدارة المخاطر:",
            "accumulation_phase": "مرحلة التراكم",
            "manipulation_phase": "مرحلة التلاعب",
            "distribution_phase": "مرحلة التوزيع",
            "bullish_shift": "تحول صاعد",
            "bearish_shift": "تحول هابط",
            "ist_details": "تفاصيل تحليل الـ IST:",
            "analysis_for": "تحليل لزوج:",
            "timeframe": "الفترة الزمنية:",
            "no_significant_shift": "لا توجد تحولات كبيرة",
        },
        "en": {
            "app_title": "Smart Forex Analyzer",
            "select_symbol": "Select Currency Pair:",
            "time_interval": "Time Interval:",
            "chart_type": "Chart Type:",
            "analyze_button": "Analyze Market",
            "update_api_button": "Update API Key",
            "language_label": "Language:",
            "contact_button": "Contact Us",
            "education_button": "Educational Section",
            "whatsapp_share": "WhatsApp",
            "telegram_share": "Telegram",
            "twitter_share": "Twitter",
            "recommendation_title": "Recommendation:",
            "signals_title": "Market Signals and Analysis:",
            "levels_title": "Take Profit and Stop Loss Levels:",
            "current_price": "Current Price:",
            "rsi_label": "RSI:",
            "macd_label": "MACD:",
            "pivot_point_label": "Pivot Point:",
            "resistance_label": "Resistance (R1/R2):",
            "support_label": "Support (S1/S2):",
            "fibonacci_title": "Fibonacci Levels:",
            "no_data_fetch_error": "Data Fetch Error",
            "not_enough_data_warning": "Insufficient Data",
            "not_enough_data_analysis": "Not enough data available for analysis.",
            "update_api_title": "Update API Key",
            "enter_api_key": "Enter New API Key:",
            "api_key_updated": "Updated",
            "api_key_success_message": "API Key updated successfully!",
            "share_unavailable_title": "Sharing Unavailable",
            "share_no_data_message": "No data to share.",
            "share_success_title": "Shared",
            "whatsapp_share_success": "Recommendation shared successfully on WhatsApp!",
            "telegram_share_success": "Recommendation shared successfully on Telegram!",
            "twitter_share_success": "Recommendation shared successfully on Twitter!",
            "neutral_recommendation": "Neutral",
            "buy_recommendation": "Buy",
            "sell_recommendation": "Sell",
            "signal_ema_buy": "Buy Signal (EMA 50 crosses above EMA 200 - bullish trend)",
            "signal_ema_sell": "Sell Signal (EMA 50 crosses below EMA 200 - bearish trend)",
            "signal_rsi_overbought": "RSI Overbought (above 70)",
            "signal_rsi_oversold": "RSI Oversold (below 30)",
            "signal_macd_crossover_buy": "Buy Signal (MACD crosses above signal line)",
            "signal_macd_crossover_sell": "Sell Signal (MACD crosses below signal line)",
            "analyze_title": "Technical Analysis for",
            "contact_message": "For support, please email: support@example.com",
            "education_message": "Visit our educational section at: example.com/education",
            "telegram_share_message": "Shared via Smart Forex Analyzer",
            "currency_pair_label": "Currency Pair:",
            "ict_analysis_button": "ICT Analysis",
            "ict_title": "ICT Strategy Analysis",
            "liquidity_levels": "Liquidity Levels:",
            "market_structure": "Market Structure:",
            "fair_value_gaps": "Fair Value Gaps:",
            "order_blocks": "Order Blocks:",
            "entry_points": "Entry Points:",
            "take_profit": "Take Profit:",
            "stop_loss": "Stop Loss:",
            "optimal_entry": "Optimal Entry Point:",
            "ict_buy_signal": "Buy Signal (ICT)",
            "ict_sell_signal": "Sell Signal (ICT)",
            "bullish_structure": "Bullish Structure",
            "bearish_structure": "Bearish Structure",
            "neutral_structure": "Neutral Structure",
            "market_structure_label": "Market Structure:",
            "liquidity_zones": "Liquidity Zones:",
            "fvg_label": "Fair Value Gaps:",
            "ote_label": "Optimal Trade Entry (OTE):",
            "tp_label": "Take Profit Targets:",
            "sl_label": "Stop Loss:",
            "scenario_title": "Trading Scenario",
            "primary_scenario": "Primary Scenario:",
            "alternative_scenario": "Alternative Scenario:",
            "ist_title": "Comprehensive IST Analysis",
            "market_phase": "Current Market Phase:",
            "market_shift": "Market Shift Points:",
            "key_levels": "Key Levels:",
            "entry_strategy": "Entry Strategy:",
            "risk_management": "Risk Management:",
            "accumulation_phase": "Accumulation Phase",
            "manipulation_phase": "Manipulation Phase",
            "distribution_phase": "Distribution Phase",
            "bullish_shift": "Bullish Shift",
            "bearish_shift": "Bearish Shift",
            "ist_details": "IST Analysis Details:",
            "analysis_for": "Analysis for:",
            "timeframe": "Timeframe:",
            "no_significant_shift": "No significant shift",
        }
    }

    def __init__(self):
        super().__init__()
        # تعريف المتغيرات المطلوبة
        self.last_analysis_time = None
        self.analysis_interval = timedelta(minutes=5)
        self.current_data = None
        self.current_symbol = None
        self.current_interval = None
        self.ict_mode = False
        
        self.current_language = tk.StringVar(value="العربية")  # Default language
        self.languages = {"العربية": "ar", "English": "en"}
        self.title(self.get_text("app_title"))
        self.geometry("1200x850")  # Window size
        self.configure(bg="#2c3e50")  # Background color
        
        # Style configuration
        style = ttk.Style(self)
        style.theme_use('clam')  # Use a modern theme
        style.configure("TFrame", background="#2c3e50")
        style.configure("TLabel", background="#2c3e50", foreground="white", font=("Arial", 11))
        style.configure("Title.TLabel", font=("Arial", 18, "bold"), foreground="#1abc9c", background="#2c3e50")
        style.configure("TButton", background="#3498db", foreground="white", font=("Arial", 10, "bold"), borderwidth=0, relief="flat")
        style.map("TButton", background=[('active', '#2980b9')])
        style.configure("TCombobox", fieldbackground="#34495e", background="#34495e", foreground="white", arrowcolor="white")
        style.map("TCombobox", fieldbackground=[('readonly', '#34495e')], foreground=[('readonly', 'white')])
        style.configure("Accent.TButton", background="#9b59b6", foreground="white")  # For ICT button
        
        # Initialize chart variables
        self.fig = None
        self.ax = None
        self.canvas = None
        self.canvas_widget = None
        
        self.create_widgets()

    def get_text(self, key):
        lang_display_name = self.current_language.get()
        lang_code = self.languages.get(lang_display_name, "en")  # Default to English if not found
        return self.translations[lang_code].get(key, f"KEY_NOT_FOUND: {key}")

    def create_widgets(self):
        # Top frame for inputs
        frame_top = ttk.Frame(self, padding=(15, 15, 15, 5))
        frame_top.pack(fill="x", padx=15, pady=10)
        
        # Title label
        self.title_label_widget = ttk.Label(frame_top, text=self.get_text("app_title"), style="Title.TLabel")
        self.title_label_widget.pack(side="top", pady=(0, 15))
        
        # Input frame
        input_frame = ttk.Frame(frame_top)  # Sub-frame for inputs
        input_frame.pack(pady=5)
        
        # Symbol selection
        self.symbol_label_widget = ttk.Label(input_frame, text=self.get_text("select_symbol"))
        self.symbol_label_widget.pack(side="left", padx=5)
        
        self.symbol_var = tk.StringVar(value=symbols_list[0])
        self.symbol_combo = ttk.Combobox(input_frame, textvariable=self.symbol_var, values=symbols_list, state="readonly", width=15)
        self.symbol_combo.pack(side="left", padx=10)
        self.symbol_combo.bind("<<ComboboxSelected>>", lambda e: self.run_analysis())
        
        # Interval selection
        self.interval_label_widget = ttk.Label(input_frame, text=self.get_text("time_interval"))
        self.interval_label_widget.pack(side="left", padx=5)
        
        self.interval_var = tk.StringVar(value="1h")
        self.interval_combo = ttk.Combobox(input_frame, textvariable=self.interval_var, values=intervals_list, state="readonly", width=10)
        self.interval_combo.pack(side="left", padx=10)
        self.interval_combo.bind("<<ComboboxSelected>>", lambda e: self.run_analysis())
        
        # Chart type selection
        self.chart_type_label_widget = ttk.Label(input_frame, text=self.get_text("chart_type"))
        self.chart_type_label_widget.pack(side="left", padx=5)
        
        self.chart_type_var = tk.StringVar(value="Candlestick")  # Default chart type
        self.chart_combo = ttk.Combobox(input_frame, textvariable=self.chart_type_var, values=["Line", "Candlestick"], state="readonly", width=12)
        self.chart_combo.pack(side="left", padx=10)
        self.chart_combo.bind("<<ComboboxSelected>>", lambda e: self.run_analysis())
        
        # Analyze button
        self.analyze_button_widget = ttk.Button(input_frame, text=self.get_text("analyze_button"), command=self.run_analysis)
        self.analyze_button_widget.pack(side="left", padx=(20, 5))
        
        # Update API key button
        self.update_api_button_widget = ttk.Button(input_frame, text=self.get_text("update_api_button"), command=self.update_api_key)
        self.update_api_button_widget.pack(side="left", padx=10)
        
        # ICT Analysis button
        self.ict_button = ttk.Button(input_frame, text=self.get_text("ict_analysis_button"), 
                                    command=self.toggle_ict_analysis)
        self.ict_button.pack(side="left", padx=10)
        
        # Language selection
        self.language_label_widget = ttk.Label(input_frame, text=self.get_text("language_label"))
        self.language_label_widget.pack(side="left", padx=5)
        
        self.language_combo = ttk.Combobox(input_frame, textvariable=self.current_language, values=list(self.languages.keys()), state="readonly", width=10)
        self.language_combo.pack(side="left", padx=10)
        self.language_combo.bind("<<ComboboxSelected>>", lambda e: self.update_language())
        
        # Main content frame
        self.main_content_frame = ttk.Frame(self)
        self.main_content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Text output area with RTL support for Arabic
        self.text_output = tk.Text(self.main_content_frame, height=20, width=50, 
                                  font=("Arial", 11), bg="#34495e", fg="white", 
                                  wrap="word", relief="flat", borderwidth=0)
        
        # Set RTL for Arabic language
        if self.current_language.get() == "العربية":
            self.text_output.configure(justify="right")
        
        scrollbar = ttk.Scrollbar(self.main_content_frame, command=self.text_output.yview)
        self.text_output.configure(yscrollcommand=scrollbar.set)
        self.text_output.pack(side="left", fill="both", padx=(0, 5))
        scrollbar.pack(side="left", fill="y")
        
        # Chart area will be created on demand in run_analysis
        
        # Bottom buttons frame
        frame_bottom_buttons = ttk.Frame(self, padding=(15, 5, 15, 15))
        frame_bottom_buttons.pack(fill="x", padx=15, pady=10)
        
        # Contact button
        self.contact_button_widget = ttk.Button(frame_bottom_buttons, text=self.get_text("contact_button"), command=self.open_contact_page)
        self.contact_button_widget.pack(side="left", padx=5)
        
        # Education button
        self.education_button_widget = ttk.Button(frame_bottom_buttons, text=self.get_text("education_button"), command=self.open_educational_page)
        self.education_button_widget.pack(side="left", padx=5)
        
        # Sharing frame
        frame_share = ttk.Frame(frame_bottom_buttons)
        frame_share.pack(side="right", padx=5)
        
        # WhatsApp share button
        self.whatsapp_button_widget = ttk.Button(frame_share, text=self.get_text("whatsapp_share"), command=self.share_whatsapp)
        self.whatsapp_button_widget.pack(side="left", padx=5)
        
        # Telegram share button
        self.telegram_button_widget = ttk.Button(frame_share, text=self.get_text("telegram_share"), command=self.share_telegram)
        self.telegram_button_widget.pack(side="left", padx=5)
        
        # Twitter share button
        self.twitter_button_widget = ttk.Button(frame_share, text=self.get_text("twitter_share"), command=self.share_twitter)
        self.twitter_button_widget.pack(side="left", padx=5)

    def toggle_ict_analysis(self):
        """Toggle between regular analysis and ICT analysis"""
        self.ict_mode = not self.ict_mode
        if self.ict_mode:
            self.ict_button.config(style="Accent.TButton")
            self.title(f"{self.get_text('app_title')} - {self.get_text('ict_title')}")
        else:
            self.ict_button.config(style="TButton")
            self.title(self.get_text("app_title"))
        self.run_analysis()

    def update_api_key(self):
        api_key = simpledialog.askstring(self.get_text("update_api_title"), self.get_text("enter_api_key"), parent=self)
        if api_key:
            global API_KEY
            API_KEY = api_key.strip()  # التأكد من إزالة المسافات البيضاء
            messagebox.showinfo(self.get_text("api_key_updated"), self.get_text("api_key_success_message"))
            self.run_analysis()  # إعادة تشغيل التحليل باستخدام API Key الجديد

    def update_language(self):
        # Update the main window title
        self.title(self.get_text("app_title"))
        
        # Update static text elements
        self.title_label_widget.config(text=self.get_text("app_title"))
        self.symbol_label_widget.config(text=self.get_text("select_symbol"))
        self.interval_label_widget.config(text=self.get_text("time_interval"))
        self.chart_type_label_widget.config(text=self.get_text("chart_type"))
        self.analyze_button_widget.config(text=self.get_text("analyze_button"))
        self.update_api_button_widget.config(text=self.get_text("update_api_button"))
        self.language_label_widget.config(text=self.get_text("language_label"))
        self.contact_button_widget.config(text=self.get_text("contact_button"))
        self.education_button_widget.config(text=self.get_text("education_button"))
        self.whatsapp_button_widget.config(text=self.get_text("whatsapp_share"))
        self.telegram_button_widget.config(text=self.get_text("telegram_share"))
        self.twitter_button_widget.config(text=self.get_text("twitter_share"))
        self.ict_button.config(text=self.get_text("ict_analysis_button"))
        
        # Update text direction for Arabic
        if self.current_language.get() == "العربية":
            self.text_output.configure(justify="right")
        else:
            self.text_output.configure(justify="left")
        
        # Re-run analysis to update dynamic text in the chart and text area
        self.run_analysis()

    def run_analysis(self):
        current_time = datetime.now()
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()

        if (self.last_analysis_time is None or
            current_time - self.last_analysis_time >= self.analysis_interval or
            symbol != self.current_symbol or
            interval != self.current_interval):
            
            self.text_output.delete(1.0, tk.END)  # Clear previous text
            
            # Create chart if not exists
            if self.ax is None:
                self.fig, self.ax = plt.subplots(figsize=(8, 5))
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.main_content_frame)
                self.canvas_widget = self.canvas.get_tk_widget()
                self.canvas_widget.pack(side="right", fill="both", expand=True)
            else:
                # Clear previous chart only if it exists
                self.ax.clear()
            
            try:
                self.current_data = fetch_data(symbol, interval)
                self.last_analysis_time = current_time  # Update last analysis time
                self.current_symbol = symbol
                self.current_interval = interval
            except DataFetchError as e:
                messagebox.showerror(self.get_text("no_data_fetch_error"), str(e))
                return
            
            if len(self.current_data) < 50:  # Check if there's enough data for analysis
                messagebox.showwarning(self.get_text("not_enough_data_warning"), self.get_text("not_enough_data_analysis"))
                try:
                    self.current_data = fetch_data(symbol, interval, outputsize=500)
                    if len(self.current_data) < 50:
                        self.text_output.insert(tk.END, self.get_text("not_enough_data_analysis"))
                        if self.ax is not None:
                            self.canvas.draw()  # Update the empty chart
                        return
                except DataFetchError as e:
                    self.text_output.insert(tk.END, f"{self.get_text('no_data_fetch_error')}: {str(e)}")
                    if self.ax is not None:
                        self.canvas.draw()
                    return

            self.current_data = analyze(self.current_data)
            
            if self.ict_mode:
                # Perform ICT analysis
                signals = detect_ict_signals(self.current_data, self)
                
                # Display ICT-specific results
                self.text_output.insert(tk.END, f"🔥 **{self.get_text('ict_title')}**\n\n")
                self.text_output.insert(tk.END, f"📊 **{self.get_text('market_structure_label')}** {signals['market_structure']}\n")
                self.text_output.insert(tk.END, f"📈 **{self.get_text('market_phase')}** {signals['market_phase']}\n\n")
                
                # Display IST analysis details
                self.text_output.insert(tk.END, f"🔍 **{self.get_text('ist_title')}**\n")
                self.text_output.insert(tk.END, f"💧 **{self.get_text('liquidity_zones')}** {', '.join([str(round(l, 5)) for l in signals['liquidity_levels']])}\n")
                self.text_output.insert(tk.END, f"🔄 **{self.get_text('market_shift')}** {signals['market_shift']}\n")
                self.text_output.insert(tk.END, f"📏 **{self.get_text('key_levels')}** {signals['key_levels']}\n\n")
                
                # Display scenarios
                self.text_output.insert(tk.END, f"🎯 **{self.get_text('scenario_title')}**\n")
                self.text_output.insert(tk.END, f"📘 **{self.get_text('primary_scenario')}**\n")
                self.text_output.insert(tk.END, self.wrap_text(signals['primary_scenario']) + "\n\n")
                self.text_output.insert(tk.END, f"📙 **{self.get_text('alternative_scenario')}**\n")
                self.text_output.insert(tk.END, self.wrap_text(signals['alternative_scenario']) + "\n\n")
                
                # Display entry strategy and risk management
                self.text_output.insert(tk.END, f"⚔️ **{self.get_text('entry_strategy')}**\n")
                self.text_output.insert(tk.END, self.wrap_text(signals['entry_strategy']) + "\n\n")
                self.text_output.insert(tk.END, f"🛡️ **{self.get_text('risk_management')}**\n")
                self.text_output.insert(tk.END, self.wrap_text(signals['risk_management']) + "\n\n")
                
                # Detailed IST analysis
                self.text_output.insert(tk.END, f"📚 **{self.get_text('ist_details')}**\n")
                self.text_output.insert(tk.END, self.wrap_text(signals['ist_details']) + "\n\n")
                
                # Recommendation
                self.text_output.insert(tk.END, f"🔔 **{self.get_text('recommendation_title')}** {signals['recommendation']}\n")
                
                # Plot ICT-specific levels
                self.plot_ict_levels(signals)
                
            else:
                # Regular analysis
                signals, recommendation, levels, fib_levels = detect_signals(self.current_data, interval, self)
                
                # Display results in the text area
                self.text_output.insert(tk.END, f"🔔 **{self.get_text('recommendation_title')}** {recommendation}\n\n")
                self.text_output.insert(tk.END, f"📋 **{self.get_text('signals_title')}**\n")
                for sig in signals:
                    self.text_output.insert(tk.END, f" - {sig}\n")
                
                self.text_output.insert(tk.END, f"\n⚡ **{self.get_text('levels_title')}**\n")
                for key, val in levels.items():
                    if isinstance(val, (int, float)) and not np.isnan(val):
                        self.text_output.insert(tk.END, f" - {key}: {round(val, 5)}\n")
                    else:
                        self.text_output.insert(tk.END, f" - {key}: {val}\n")
                
                self.text_output.insert(tk.END, f"\n📊 **{self.get_text('fibonacci_title')}**\n")
                for level, price in fib_levels.items():
                    if not np.isnan(price):
                        self.text_output.insert(tk.END, f" - {level}: {round(price, 5)}\n")

                # Prepare data for plotting
                plot_df = self.current_data.tail(100)  # Show last 100 candles

                if self.chart_type_var.get() == "Line":
                    self.ax.plot(plot_df["Date"], plot_df["close"], label=self.get_text("current_price"), color="cyan", linewidth=1.5)
                else:  # Candlestick chart
                    # Convert dates to numerical format
                    plot_df = plot_df.copy()
                    plot_df["Date"] = mdates.date2num(plot_df["Date"].dt.to_pydatetime())
                    
                    # Prepare OHLC data
                    ohlc_data = []
                    for i, row in plot_df.iterrows():
                        ohlc_data.append((
                            row["Date"],
                            row["open"],
                            row["high"],
                            row["low"],
                            row["close"]
                        ))
                    
                    # Plot candlestick
                    candlestick_ohlc(self.ax, ohlc_data, width=0.015 * (plot_df['Date'].iloc[-1] - plot_df['Date'].iloc[0]), 
                                    colorup='#2ecc71', colordown='#e74c3c', alpha=0.8)

                # Plot additional indicators
                if "BB_High" in plot_df and not plot_df["BB_High"].isnull().all():
                    self.ax.plot(plot_df["Date"], plot_df["BB_High"], label="BB High", color="red", linestyle="--", linewidth=0.8)
                if "BB_Low" in plot_df and not plot_df["BB_Low"].isnull().all():
                    self.ax.plot(plot_df["Date"], plot_df["BB_Low"], label="BB Low", color="green", linestyle="--", linewidth=0.8)
                if "EMA_50" in plot_df and not plot_df["EMA_50"].isnull().all():
                    self.ax.plot(plot_df["Date"], plot_df["EMA_50"], label="EMA 50", color="orange", linewidth=1.0)
                if "EMA_200" in plot_df and not plot_df["EMA_200"].isnull().all():
                    self.ax.plot(plot_df["Date"], plot_df["EMA_200"], label="EMA 200", color="purple", linewidth=1.0)

                # Plot Fibonacci levels
                fib_colors = plt.cm.viridis(np.linspace(0, 1, len(fib_levels)))  # Gradient colors
                for i, (level_name, price) in enumerate(fib_levels.items()):
                    if not np.isnan(price):
                        self.ax.axhline(price, linestyle=":", label=f"Fib {level_name}", color=fib_colors[i], alpha=0.7, linewidth=0.8)

                # Plot pivot point and support/resistance levels
                pp_val = levels.get(self.get_text("pivot_point_label"))
                if pp_val and not np.isnan(pp_val):
                    self.ax.axhline(pp_val, linestyle="-.", label=self.get_text("pivot_point_label"), color="white", linewidth=1.2)

                r1_val = levels.get(self.get_text("resistance_label"))
                if r1_val and not np.isnan(r1_val):
                    self.ax.axhline(r1_val, linestyle="--", label=f"R1: {round(r1_val, 5)}", color="#f1c40f", linewidth=0.9)  # Yellow for resistance

                s1_val = levels.get(self.get_text("support_label"))
                if s1_val and not np.isnan(s1_val):
                    self.ax.axhline(s1_val, linestyle="--", label=f"S1: {round(s1_val, 5)}", color="#3498db", linewidth=0.9)  # Blue for support

                # Configure chart appearance with improved clarity
                self.ax.set_title(f"{self.get_text('analyze_title')} {symbol} - {self.get_text('time_interval')}: {interval}", 
                                color="white", fontsize=16, pad=15)  # Increased font size and padding
                self.ax.set_xlabel(self.get_text("time_interval"), color="white", fontsize=12)
                self.ax.set_ylabel(self.get_text("current_price"), color="white", fontsize=12)
                
                # Set larger font for ticks
                self.ax.tick_params(axis='both', which='major', labelsize=10, colors='white')
                
                # Configure grid
                self.ax.grid(True, color='#555555', linestyle='--', linewidth=0.7, alpha=0.5)  # More visible grid
                
                if len(plot_df) > 0:  # Ensure there is data to plot
                    # Format x-axis as dates
                    self.ax.xaxis_date()
                    
                    # Auto-format dates
                    locator = mdates.AutoDateLocator()
                    formatter = mdates.AutoDateFormatter(locator)
                    self.ax.xaxis.set_major_locator(locator)
                    self.ax.xaxis.set_major_formatter(formatter)
                
                # Rotate x-axis labels for better readability
                plt.setp(self.ax.get_xticklabels(), rotation=30, ha="right")
                
                # Add legend with better styling
                self.ax.legend(loc="best", fontsize="small", facecolor="#2c3e50", edgecolor="white", labelcolor="white", framealpha=0.7)
                self.ax.set_facecolor("#34495e")  # Set chart area background color
                self.fig.patch.set_facecolor("#2c3e50")  # Set figure background color
                
                # Adjust layout for better fit
                self.fig.tight_layout(pad=2.0)
                
            # Update the chart
            self.canvas.draw()
        else:
            if self.ict_mode:
                self.text_output.insert(tk.END, "تحليل ICT لم يتغير بعد، يرجى الانتظار حتى انتهاء الفترة الزمنية المحددة.\n")
            else:
                self.text_output.insert(tk.END, "التحليل لم يتغير بعد، يرجى الانتظار حتى انتهاء الفترة الزمنية المحددة.\n")

    def plot_ict_levels(self, signals):
        """Plot ICT-specific levels on the chart with improved clarity"""
        # Prepare data for plotting
        plot_df = self.current_data.tail(100)
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()
        
        # Clear previous chart
        self.ax.clear()
        
        # Convert dates to numerical format
        plot_df = plot_df.copy()
        plot_df["Date"] = mdates.date2num(plot_df["Date"].dt.to_pydatetime())
        
        # Prepare OHLC data
        ohlc_data = []
        for i, row in plot_df.iterrows():
            ohlc_data.append((
                row["Date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"]
            ))
        
        # Plot candlestick chart
        candlestick_ohlc(self.ax, ohlc_data, 
                         width=0.015 * (plot_df['Date'].iloc[-1] - plot_df['Date'].iloc[0]), 
                         colorup='#2ecc71', colordown='#e74c3c', alpha=0.8)
        
        # Plot liquidity levels
        liquidity_levels = signals.get("liquidity_levels", [])
        for level in liquidity_levels:
            self.ax.axhline(level, color='#9b59b6', linestyle='--', alpha=0.7, 
                           label=f"{self.get_text('liquidity_levels')} {round(level, 5)}")
        
        # Plot fair value gaps
        fvg = signals.get("fair_value_gaps", [])
        for gap in fvg:
            color = '#2ecc71' if gap['type'] == 'Bullish' else '#e74c3c'
            self.ax.axhline(gap['price'], color=color, linestyle='-', alpha=0.5, 
                           label=f"{gap['type']} FVG: {round(gap['price'], 5)}")
        
        # Plot entry points
        entry_points = signals.get("entry_points", [])
        for i, point in enumerate(entry_points):
            self.ax.axhline(point, color='#f1c40f', linestyle='-.', linewidth=2, 
                           label=f"{self.get_text('optimal_entry')} #{i+1}")
        
        # Plot take profit levels
        take_profit = signals.get("take_profit", [])
        for i, profit in enumerate(take_profit):
            self.ax.axhline(profit, color='#2ecc71', linestyle=':', 
                           label=f"{self.get_text('take_profit')} #{i+1}")
        
        # Plot stop loss
        stop_loss = signals.get("stop_loss", None)
        if stop_loss:
            self.ax.axhline(stop_loss, color='#e74c3c', linestyle='-', linewidth=2, 
                           label=self.get_text('stop_loss'))
        
        # Configure chart appearance with improved clarity
        self.ax.set_title(f"{self.get_text('ict_title')} - {symbol} ({interval})", 
                         color="white", fontsize=16, pad=15)  # Increased font size and padding
        self.ax.set_xlabel(self.get_text("time_interval"), color="white", fontsize=12)
        self.ax.set_ylabel(self.get_text("current_price"), color="white", fontsize=12)
        
        # Set larger font for ticks
        self.ax.tick_params(axis='both', which='major', labelsize=10, colors='white')
        
        # Configure grid
        self.ax.grid(True, color='#555555', linestyle='--', linewidth=0.7, alpha=0.5)  # More visible grid
        
        # Format x-axis as dates
        self.ax.xaxis_date()
        
        # Auto-format dates
        locator = mdates.AutoDateLocator()
        formatter = mdates.AutoDateFormatter(locator)
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)
        
        # Rotate x-axis labels for better readability
        plt.setp(self.ax.get_xticklabels(), rotation=30, ha="right")
        
        # Add legend with better styling
        self.ax.legend(loc="best", fontsize="small", facecolor="#2c3e50", edgecolor="white", labelcolor="white", framealpha=0.7)
        self.ax.set_facecolor("#34495e")
        self.fig.patch.set_facecolor("#2c3e50")
        
        # Adjust layout for better fit
        self.fig.tight_layout(pad=2.0)
        
        # Update the chart
        self.canvas.draw()

    def wrap_text(self, text):
        """Wrap text to fit the text output width"""
        wrapped_lines = []
        max_width = 80  # Maximum characters per line
        
        for paragraph in text.split('\n'):
            if paragraph.strip() == "":
                wrapped_lines.append("")
                continue
                
            # Wrap each paragraph individually
            wrapper = textwrap.TextWrapper(width=max_width, break_long_words=True)
            wrapped_paragraph = wrapper.fill(paragraph)
            wrapped_lines.extend(wrapped_paragraph.split('\n'))
        
        return '\n'.join(wrapped_lines)

    def open_contact_page(self):
        """Open contact information dialog"""
        messagebox.showinfo("Contact Us", self.get_text("contact_message"))

    def open_educational_page(self):
        """Open educational section information"""
        messagebox.showinfo("Educational Section", self.get_text("education_message"))

    def share_whatsapp(self):
        """Share analysis results via WhatsApp"""
        if self.current_data is None:
            messagebox.showwarning(self.get_text("share_unavailable_title"), self.get_text("share_no_data_message"))
            return
        
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()
        message = f"*{self.get_text('analysis_for')} {symbol} ({interval})*\n\n"
        
        # Get the text from the output area
        analysis_text = self.text_output.get(1.0, tk.END).strip()
        message += analysis_text.replace("**", "*")  # Formatting for WhatsApp
        
        # Encode the message for URL
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/?text={encoded_message}"
        
        webbrowser.open(whatsapp_url)
        messagebox.showinfo(self.get_text("share_success_title"), self.get_text("whatsapp_share_success"))

    def share_telegram(self):
        """Share analysis results via Telegram"""
        if self.current_data is None:
            messagebox.showwarning(self.get_text("share_unavailable_title"), self.get_text("share_no_data_message"))
            return
        
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()
        message = f"*{self.get_text('analysis_for')} {symbol} ({interval})*\n\n"
        
        # Get the text from the output area
        analysis_text = self.text_output.get(1.0, tk.END).strip()
        message += analysis_text.replace("**", "*")  # Formatting for Telegram
        
        # Encode the message for URL
        encoded_message = urllib.parse.quote(message)
        telegram_url = f"https://t.me/share/url?url=&text={encoded_message}"
        
        webbrowser.open(telegram_url)
        messagebox.showinfo(self.get_text("share_success_title"), self.get_text("telegram_share_success"))

    def share_twitter(self):
        """Share analysis results via Twitter"""
        if self.current_data is None:
            messagebox.showwarning(self.get_text("share_unavailable_title"), self.get_text("share_no_data_message"))
            return
        
        symbol = self.symbol_var.get()
        interval = self.interval_var.get()
        message = f"{self.get_text('analysis_for')} {symbol} ({interval}):\n"
        
        # Get the recommendation from the output area
        analysis_text = self.text_output.get(1.0, tk.END).strip()
        recommendation_line = analysis_text.split('\n')[0]  # First line is recommendation
        
        # Truncate to fit Twitter character limit
        if len(recommendation_line) > 200:
            recommendation_line = recommendation_line[:197] + "..."
        
        message += recommendation_line
        message += f"\n\n{self.get_text('telegram_share_message')}"
        
        # Encode the message for URL
        encoded_message = urllib.parse.quote(message)
        twitter_url = f"https://twitter.com/intent/tweet?text={encoded_message}"
        
        webbrowser.open(twitter_url)
        messagebox.showinfo(self.get_text("share_success_title"), self.get_text("twitter_share_success"))

if __name__ == "__main__":
    app = MoneyMakerApp()
    app.mainloop()
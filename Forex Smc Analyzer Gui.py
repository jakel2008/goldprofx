import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
import pandas as pd
import ta
import matplotlib.pyplot as plt

API_KEY = "079cdb64bbc8415abcf8f7be7e389349"
BASE_URL = "https://api.twelvedata.com/time_series"

symbols_list = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "XAU/USD", "XAG/USD", "BTC/USD", "ETH/USD",
    "EUR/JPY", "GBP/JPY", "AUD/JPY", "EUR/GBP", "CHF/JPY", "CAD/JPY",
    "NZD/JPY", "AUD/NZD", "EUR/CAD", "GBP/CAD", "EUR/AUD", "GBP/AUD"
]

intervals_list = ["1min", "5min", "15min", "30min", "1h", "4h", "1day"]

def fetch_data(symbol, interval="1h", outputsize=100):
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": API_KEY,
        "format": "JSON"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "values" not in data:
        raise Exception(f"Error fetching data: {data.get('message', 'Unknown error')}")

    df = pd.DataFrame(data["values"])
    df = df.rename(columns={"datetime": "Date", "open": "Open", "high": "High",
                            "low": "Low", "close": "Close"})
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df

def analyze(df):
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    boll = ta.volatility.BollingerBands(df["Close"])
    df["BB_High"] = boll.bollinger_hband()
    df["BB_Low"] = boll.bollinger_lband()
    return df

def detect_signals(df):
    signals = []
    entry_price = df.iloc[-1]["Close"]
    pivot = df.iloc[-2]["Close"]

    last = df.iloc[-1]
    signals.append(f"📈 Current Price: {round(entry_price, 5)}")
    signals.append(f"📉 RSI: {round(last['RSI'], 2)}")
    signals.append(f"📊 MACD: {round(last['MACD'], 5)} | Signal: {round(last['MACD_Signal'], 5)}")

    if last["RSI"] < 30 and last["MACD"] > last["MACD_Signal"]:
        signals.append("🔼 Buy Signal (RSI < 30 & MACD crossover)")
    if last["RSI"] > 70 and last["MACD"] < last["MACD_Signal"]:
        signals.append("🔽 Sell Signal (RSI > 70 & MACD crossover)")
    if last["Close"] < last["BB_Low"]:
        signals.append("📉 Price below BB → Possible Bounce")
    if last["Close"] > last["BB_High"]:
        signals.append("📈 Price above BB → Possible Reversal")

    if last["Close"] > df["Close"].rolling(3).mean().iloc[-1]:
        signals.append("📊 SMC: Structure forming higher highs")
    if last["Close"] < df["Close"].rolling(3).mean().iloc[-1]:
        signals.append("📉 SMC: Structure forming lower lows")
    if df["High"].iloc[-2] > df["High"].iloc[-3] and df["High"].iloc[-1] < df["High"].iloc[-2]:
        signals.append("🔄 QM Pattern detected")
    if df["Close"].iloc[-1] > df["Open"].iloc[-1] and df["Close"].iloc[-1] > df["Close"].mean():
        signals.append("🧠 ICT: Liquidity sweep + bullish close")

    recommendation = "✅ Buy" if any("Buy" in s or "SMC: Structure forming higher" in s or "ICT" in s for s in signals) \
        else "❌ Sell" if any("Sell" in s or "SMC: Structure forming lower" in s for s in signals) else "🔍 Hold"

    if recommendation == "✅ Buy":
        tp1 = entry_price * 1.005
        tp2 = entry_price * 1.01
        tp3 = entry_price * 1.015
        sl = entry_price * 0.99
    elif recommendation == "❌ Sell":
        tp1 = entry_price * 0.995
        tp2 = entry_price * 0.99
        tp3 = entry_price * 0.985
        sl = entry_price * 1.01
    else:
        tp1 = entry_price * 1.002
        tp2 = entry_price * 1.004
        tp3 = entry_price * 1.006
        sl = entry_price * 0.998

    levels = {
        "Entry": round(entry_price, 5),
        "Pivot": round(pivot, 5),
        "TP1": round(tp1, 5),
        "TP2": round(tp2, 5),
        "TP3": round(tp3, 5),
        "Stop Loss": round(sl, 5)
    }

    signals.append(f"🎯 TP1: {levels['TP1']}")
    signals.append(f"🎯 TP2: {levels['TP2']}")
    signals.append(f"🎯 TP3: {levels['TP3']}")
    signals.append(f"🛑 Stop Loss: {levels['Stop Loss']}")

    signals.append(f"📌 Recommendation: {recommendation}")
    signals.append(f"📌 Entry: {levels['Entry']}, Pivot: {levels['Pivot']}")

    return signals, recommendation, levels

def display_signals_on_ui(text_widget, signals):
    text_widget.config(state='normal')
    text_widget.delete("1.0", tk.END)
    for signal in signals:
        text_widget.insert(tk.END, signal + "\n")
    text_widget.config(state='disabled')

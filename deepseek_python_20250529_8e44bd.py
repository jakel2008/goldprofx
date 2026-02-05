import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pandas as pd
import ta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

API_KEY = "079cdb64bbc8415abcf8f7be7e389349"
BASE_URL = "https://api.twelvedata.com/time_series"

symbols_list = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "USD/CAD", "NZD/USD",
    "XAU/USD", "XAG/USD", "BTC/USD", "ETH/USD"
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
                            "low": "Low", "close": "Close", "volume": "Volume"})
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = df[col].astype(float)
    if "Volume" in df.columns:
        df["Volume"] = pd.to_numeric(df["Volume"], errors='coerce').fillna(0)
    else:
        df["Volume"] = 0
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
    df["SMA50"] = ta.trend.SMAIndicator(df["Close"], window=50).sma_indicator()
    return df

def detect_signals_with_levels(df):
    signals = []
    last = df.iloc[-1]

    pivot = (last["High"] + last["Low"] + last["Close"]) / 3

    entry = last["Close"]
    atr = (df["High"] - df["Low"]).rolling(window=14).mean().iloc[-1]

    take_profit1 = entry + 1 * atr
    take_profit2 = entry + 2 * atr
    stop_loss = entry - 1 * atr

    recommendation = "🔍 Hold (No clear signal)"

    if last["RSI"] < 30 and last["MACD"] > last["MACD_Signal"]:
        recommendation = "🔼 Buy"
        signals.append("Buy Signal (RSI < 30 & MACD bullish crossover)")
    elif last["RSI"] > 70 and last["MACD"] < last["MACD_Signal"]:
        recommendation = "🔽 Sell"
        signals.append("Sell Signal (RSI > 70 & MACD bearish crossover)")
    else:
        signals.append("No strong buy/sell signal")

    if last["Close"] < last["BB_Low"]:
        signals.append("Price below lower Bollinger Band - Possible bounce")
    if last["Close"] > last["BB_High"]:
        signals.append("Price above upper Bollinger Band - Possible reversal")

    if last["Close"] > last["SMA50"]:
        signals.append("Price above SMA50 - Bullish trend")
    else:
        signals.append("Price below SMA50 - Bearish trend")

    return {
        "signals": signals,
        "recommendation": recommendation,
        "entry": entry,
        "pivot": pivot,
        "take_profit1": take_profit1,
        "take_profit2": take_profit2,
        "stop_loss": stop_loss,
        "last_close": last["Close"],
        "rsi": last["RSI"],
        "macd": last["MACD"],
        "macd_signal": last["MACD_Signal"],
    }

def analyze_ict(df):
    last = df.iloc[-1]
    atr = (df["High"] - df["Low"]).rolling(window=14).mean().iloc[-1]

    # تحليل هيكل السوق (سهل)
    if last["Close"] > df["Close"].rolling(window=50).mean().iloc[-1]:
        market_structure = "Bullish Structure (Higher Highs and Higher Lows)"
        direction = "Long"
    else:
        market_structure = "Bearish Structure (Lower Highs and Lower Lows)"
        direction = "Short"

    # نقاط الدعم والمقاومة المبسطة (اعتمادًا على متوسط المدى ATR)
    support = last["Low"] - 0.5 * atr
    resistance = last["High"] + 0.5 * atr

    # نقاط الدخول (حسب الاتجاه)
    if direction == "Long":
        entry = support + 0.1 * atr
        stop_loss = support - 0.5 * atr
        take_profit1 = last["Close"] + atr
        take_profit2 = last["Close"] + 2 * atr
    else:
        entry = resistance - 0.1 * atr
        stop_loss = resistance + 0.5 * atr
        take_profit1 = last["Close"] - atr
        take_profit2 = last["Close"] - 2 * atr

    analysis_text = (
        f"=== ICT Strategy Analysis ===\n"
        f"Market Structure: {market_structure}\n"
        f"Suggested Direction: {direction}\n\n"
        f"Support Level: {support:.5f}\n"
        f"Resistance Level: {resistance:.5f}\n\n"
        f"Entry Point: {entry:.5f}\n"
        f"Stop Loss: {stop_loss:.5f}\n"
        f"Take Profit 1: {take_profit1:.5f}\n"
        f"Take Profit 2: {take_profit2:.5f}\n"
    )
    return analysis_text

def plot_chart(df, symbol, interval):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["Date"], df["Close"], label="Price", color="blue")
    ax.plot(df["Date"], df["BB_High"], label="BB High", linestyle="--", color="green")
    ax.plot(df["Date"], df["BB_Low"], label="BB Low", linestyle="--", color="red")
    ax.set_title(f"{symbol} ({interval}) Price with Bollinger Bands")
    ax.legend()
    return fig

def run_analysis():
    symbol = symbol_var.get()
    interval = interval_var.get()
    try:
        for widget in chart_frame.winfo_children():
            widget.destroy()

        df = fetch_data(symbol, interval=interval)
        df = analyze(df)
        analysis = detect_signals_with_levels(df)

        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, f"📊 Analysis for {symbol} ({interval}):\n\n")

        result_text.insert(tk.END, f"Last Close Price: {analysis['last_close']:.5f}\n")
        result_text.insert(tk.END, f"RSI: {analysis['rsi']:.2f}\n")
        result_text.insert(tk.END, f"MACD: {analysis['macd']:.5f}\n")
        result_text.insert(tk.END, f"MACD Signal: {analysis['macd_signal']:.5f}\n\n")

        result_text.insert(tk.END, f"Recommendation: {analysis['recommendation']}\n\n")

        for signal in analysis["signals"]:
            result_text.insert(tk.END, f"- {signal}\n")

        result_text.insert(tk.END, "\nTrade Levels:\n")
        result_text.insert(tk.END, f"Entry Price: {analysis['entry']:.5f}\n")
        result_text.insert(tk.END, f"Pivot Point: {analysis['pivot']:.5f}\n")
        result_text.insert(tk.END, f"Take Profit 1: {analysis['take_profit1']:.5f}\n")
        result_text.insert(tk.END, f"Take Profit 2: {analysis['take_profit2']:.5f}\n")
        result_text.insert(tk.END, f"Stop Loss: {analysis['stop_loss']:.5f}\n")

        fig = plot_chart(df, symbol, interval)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def run_ict_analysis():
    symbol = symbol_var.get()
    interval = interval_var.get()
    try:
        df = fetch_data(symbol, interval=interval)
        df = analyze(df)

        ict_analysis_text = analyze_ict(df)

        # عرض نتائج ICT في نافذة منفصلة
        ict_window = tk.Toplevel(root)
        ict_window.title(f"ICT Analysis for {symbol} ({interval})")
        ict_window.geometry("400x300")
        ict_text = tk.Text(ict_window, font=("Consolas", 11), wrap="word", bg="#f9f9f9")
        ict_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ict_text.insert(tk.END, ict_analysis_text)
        ict_text.config(state=tk.DISABLED)
    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("Money Maker$")
root.geometry("980x640")
root.configure(bg="#f0f4f7")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#f0f4f7", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10, "bold"))

title_label = ttk.Label(root, text="💰 Money Maker$ - Forex Analyzer", font=("Segoe UI", 16, "bold"))
title_label.pack(pady=10)

input_frame = ttk.Frame(root)
input_frame.pack(pady=5)

ttk.Label(input_frame, text="Pair:").grid(row=0, column=0, padx=5)
symbol_var = tk.StringVar()
symbol_var.set(symbols_list[0])
symbol_menu = ttk.OptionMenu(input_frame, symbol_var, symbols_list[0], *symbols_list)
symbol_menu.grid(row=0, column=1, padx=5)

ttk.Label(input_frame, text="Interval:").grid(row=0, column=2, padx=5)
interval_var = tk.StringVar()
interval_var.set(intervals_list[4])  # الافتراضي: 1h
interval_menu = ttk.OptionMenu(input_frame, interval_var, intervals_list[4], *intervals_list)
interval_menu.grid(row=0, column=3, padx=5)

# أزرار التحليل
ttk.Button(input_frame, text="Analyze", command=run_analysis).grid(row=0, column=4, padx=10)
ttk.Button(input_frame, text="ICT Analysis", command=run_ict_analysis).grid(row=0, column=5, padx=10)

result_text = tk.Text(root, height=12, font=("Consolas", 10), wrap="word", bg="#ffffff")
result_text.pack(fill=tk.BOTH, padx=15, pady=10)

chart_frame = ttk.Frame(root)
chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()

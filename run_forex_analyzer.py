import requests
import statistics
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser
import urllib.parse
import threading
import time
from PIL import Image, ImageTk
import matplotlib.dates as mdates
from datetime import datetime

# إعدادات عامة
API_KEY = 'xuoK77rp1QKA5sEIyMzsBmWZGDWXUU28'

SYMBOLS = [
    'XAU/USD', 'XAG/USD', 'BTC/USD', 'ETH/USD', 
    'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF',
    'AUD/USD', 'USD/CAD', 'NZD/USD', 'XPT/USD'
]

CRYPTO_SYMBOLS = ['BTC/USD', 'ETH/USD', 'XRP/USD', 'LTC/USD']

INTERVALS = {
    '1 دقيقة': '1min',
    '5 دقائق': '5min',
    '15 دقيقة': '15min',
    '30 دقيقة': '30min',
    '1 ساعة': '60min',
    'يومي': '1day'
}

# ألوان التصميم
BG_COLOR = '#1e1e2e'
FG_COLOR = '#f5f5f5'
ACCENT_COLOR = '#3498db'
SECONDARY_COLOR = '#2c3e50'
BUTTON_COLOR = '#2980b9'
HIGHLIGHT_COLOR = '#e74c3c'
SUCCESS_COLOR = '#2ecc71'
CARD_COLOR = '#2d3436'

# تنسيق الرمز
def format_symbol(symbol):
    return symbol.replace('/', '')

# حساب RSI
def compute_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# توليد الإشارة الفنية
def calculate_signals(prices):
    if len(prices) < 20:
        return "بيانات غير كافية للتحليل"
    
    rsi = compute_rsi(prices)
    sma_short = statistics.mean(prices[-5:])
    sma_long = statistics.mean(prices[-20:])
    sma_50 = statistics.mean(prices[-50:]) if len(prices) >= 50 else sma_long
    
    # تحديد الإتجاه
    if sma_short > sma_long and sma_long > sma_50:
        direction = "شراء قوي"
        color = SUCCESS_COLOR
    elif sma_short > sma_long:
        direction = "شراء"
        color = SUCCESS_COLOR
    elif sma_short < sma_long and sma_long < sma_50:
        direction = "بيع قوي"
        color = HIGHLIGHT_COLOR
    else:
        direction = "بيع"
        color = HIGHLIGHT_COLOR
    
    rsi_signal = "تشبع شراء" if rsi > 70 else "تشبع بيع" if rsi < 30 else "عادي"
    entry = prices[-1]
    sl = entry * 0.98 if "شراء" in direction else entry * 1.02
    tp = entry * 1.03 if "شراء" in direction else entry * 0.97
    
    volatility = (max(prices[-10:]) - min(prices[-10:])) / entry * 100
    volatility_text = f"التقلب: {volatility:.2f}%"
    
    return (
        f"📊 {direction}\n"
        f"📈 RSI: {rsi:.1f} ({rsi_signal})\n"
        f"🔵 الدخول: {entry:.4f}\n"
        f"🔴 وقف الخسارة: {sl:.4f}\n"
        f"🟢 جني الأرباح: {tp:.4f}\n"
        f"🌪️ {volatility_text}"
    ), color

# جلب البيانات من Alpha Vantage
def fetch_data(symbol, interval, frame, update_callback):
    symbol_fmt = format_symbol(symbol)
    is_crypto = symbol in CRYPTO_SYMBOLS

    try:
        if is_crypto:
            url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={symbol_fmt}&market=USD&apikey={API_KEY}"
        else:
            if interval in ['1min', '5min', '15min', '30min', '60min']:
                url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={symbol[:3]}&to_symbol={symbol[4:]}&interval={interval}&apikey={API_KEY}"
            else:
                url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={symbol[:3]}&to_symbol={symbol[4:]}&apikey={API_KEY}"

        response = requests.get(url)
        data = response.json()

        if "Note" in data:
            raise Exception("تم تجاوز الحد اليومي لعدد الطلبات.")
        if "Error Message" in data:
            raise Exception("رمز غير صحيح أو مشكلة في الاتصال.")

        key = "Time Series (Digital Currency Daily)" if is_crypto else (
            "Time Series FX (Daily)" if interval == '1day' else f"Time Series FX ({interval})"
        )

        timeseries = data.get(key, {})
        if not timeseries:
            raise Exception("لا توجد بيانات متاحة.")

        sorted_times = sorted(timeseries.keys(), reverse=True)
        prices = [float(timeseries[time]['4. close']) for time in sorted_times]
        timestamps = [datetime.strptime(time, '%Y-%m-%d %H:%M:%S' if ' ' in time else '%Y-%m-%d') 
                      for time in sorted_times]

        # إرجاع البيانات للتحديث في الواجهة
        update_callback(symbol, prices, timestamps, interval, frame)

    except Exception as e:
        update_callback(symbol, None, None, interval, frame, str(e))

# تحديث الواجهة ببيانات جديدة
def update_gui(symbol, prices, timestamps, interval, frame, error=None):
    if error:
        # عرض خطأ
        error_frame = tk.Frame(frame, bg=HIGHLIGHT_COLOR, bd=2, relief='groove')
        error_frame.pack(fill='x', padx=10, pady=5, ipady=5)
        tk.Label(
            error_frame, 
            text=f"⚠️ خطأ في {symbol}: {error}", 
            fg=FG_COLOR, 
            bg=HIGHLIGHT_COLOR, 
            font=('Arial', 9, 'bold')
        ).pack(padx=5, pady=3)
        return

    # إنشاء بطاقة للرمز
    container = tk.Frame(frame, bg=CARD_COLOR, bd=2, relief='groove')
    container.pack(fill='x', padx=10, pady=5, ipady=5)

    # عنوان البطاقة
    header = tk.Frame(container, bg=SECONDARY_COLOR)
    header.pack(fill='x', padx=5, pady=2)
    
    # أيقونة حسب نوع الأصل
    icon = "🪙" if symbol in ['XAU/USD', 'XAG/USD', 'XPT/USD'] else (
        "💱" if symbol in CRYPTO_SYMBOLS else "💵"
    )
    
    tk.Label(
        header, 
        text=f"{icon}  {symbol} • {interval}", 
        font=('Arial', 12, 'bold'), 
        fg=FG_COLOR, 
        bg=SECONDARY_COLOR
    ).pack(side='left', padx=5)

    # الرسم البياني
    fig, ax = plt.subplots(figsize=(6, 2.5), facecolor=CARD_COLOR)
    ax.plot(timestamps[-30:], prices[-30:], color=ACCENT_COLOR, linewidth=1.5)
    
    # تنسيق الرسم البياني
    ax.set_facecolor(CARD_COLOR)
    ax.grid(color='#3d3d3d', linestyle='--')
    ax.set_title('آخر 30 نقطة', fontsize=9, color=FG_COLOR)
    ax.tick_params(colors=FG_COLOR)
    ax.spines['bottom'].set_color(FG_COLOR)
    ax.spines['top'].set_color(FG_COLOR) 
    ax.spines['right'].set_color(FG_COLOR)
    ax.spines['left'].set_color(FG_COLOR)
    
    # تنسيق التواريخ
    if interval == '1day':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    plt.tight_layout()

    chart_canvas = FigureCanvasTkAgg(fig, master=container)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill='x', padx=5, pady=5)
    plt.close(fig)

    # الإشارات الفنية
    signals, signal_color = calculate_signals(prices)
    signal_frame = tk.Frame(container, bg=CARD_COLOR)
    signal_frame.pack(fill='x', padx=10, pady=5)
    
    tk.Label(
        signal_frame, 
        text=signals, 
        justify='right', 
        font=('Arial', 10, 'bold'), 
        fg=FG_COLOR, 
        bg=signal_color,
        padx=10,
        pady=5
    ).pack(fill='x')

    # أزرار المشاركة والإجراءات
    action_frame = tk.Frame(container, bg=CARD_COLOR)
    action_frame.pack(fill='x', padx=10, pady=10)

    def share_action(platform):
        base_urls = {
            'whatsapp': 'https://wa.me/?text=',
            'telegram': 'https://t.me/share/url?url=',
            'twitter': 'https://twitter.com/intent/tweet?text='
        }
        msg = f"تحليل {symbol} ({interval}):\n{signals}"
        webbrowser.open(base_urls[platform] + urllib.parse.quote(msg))

    def show_details():
        messagebox.showinfo(
            f"تفاصيل {symbol}", 
            f"آخر سعر: {prices[-1]:.4f}\n"
            f"أعلى سعر (30 نقطة): {max(prices[-30:]):.4f}\n"
            f"أقل سعر (30 نقطة): {min(prices[-30:]):.4f}\n"
            f"متوسط السعر (30 نقطة): {statistics.mean(prices[-30:]):.4f}"
        )

    # أزرار المشاركة
    share_frame = tk.Frame(action_frame, bg=CARD_COLOR)
    share_frame.pack(side='left', fill='x', expand=True)
    
    tk.Button(
        share_frame, 
        text="واتساب", 
        command=lambda: share_action('whatsapp'), 
        bg='#25D366', 
        fg='white',
        relief='flat',
        font=('Arial', 9, 'bold')
    ).pack(side='left', padx=3, ipadx=5)

    tk.Button(
        share_frame, 
        text="تيليجرام", 
        command=lambda: share_action('telegram'), 
        bg='#0088CC', 
        fg='white',
        relief='flat',
        font=('Arial', 9, 'bold')
    ).pack(side='left', padx=3, ipadx=5)

    tk.Button(
        share_frame, 
        text="تويتر", 
        command=lambda: share_action('twitter'), 
        bg='#1DA1F2', 
        fg='white',
        relief='flat',
        font=('Arial', 9, 'bold')
    ).pack(side='left', padx=3, ipadx=5)

    # أزرار الإجراءات
    action_btn_frame = tk.Frame(action_frame, bg=CARD_COLOR)
    action_btn_frame.pack(side='right', fill='x', expand=True)
    
    tk.Button(
        action_btn_frame, 
        text="تفاصيل", 
        command=show_details,
        bg=SECONDARY_COLOR, 
        fg=FG_COLOR,
        relief='flat',
        font=('Arial', 9, 'bold')
    ).pack(side='right', padx=3, ipadx=10)

    tk.Button(
        action_btn_frame, 
        text="تحديث", 
        command=lambda: refresh_symbol(symbol, interval, frame),
        bg=BUTTON_COLOR, 
        fg=FG_COLOR,
        relief='flat',
        font=('Arial', 9, 'bold')
    ).pack(side='right', padx=3, ipadx=10)

# تحديث رمز واحد
def refresh_symbol(symbol, interval, frame):
    # إيجاد البطاقة القديمة وحذفها
    for widget in frame.winfo_children():
        if hasattr(widget, 'symbol') and widget.symbol == symbol:
            widget.destroy()
            break
    
    # إنشاء بطاقة جديدة
    card_frame = tk.Frame(frame, bg=CARD_COLOR)
    card_frame.pack(fill='x', padx=10, pady=5)
    card_frame.symbol = symbol
    
    # شاشة تحميل
    loading_label = tk.Label(
        card_frame, 
        text=f"جاري تحديث {symbol}...", 
        font=('Arial', 10, 'bold'), 
        fg=ACCENT_COLOR, 
        bg=CARD_COLOR
    )
    loading_label.pack(pady=20)
    
    # بدء جلب البيانات في مسار منفصل
    threading.Thread(
        target=fetch_data, 
        args=(symbol, interval, card_frame, 
             lambda s, p, t, i, f, e=None: update_in_frame(card_frame, s, p, t, i, f, e, loading_label)),
        daemon=True
    ).start()

# تحديث الواجهة في المسار الرئيسي
def update_in_frame(frame, symbol, prices, timestamps, interval, parent_frame, error, loading_label):
    loading_label.destroy()
    if error:
        error_frame = tk.Frame(frame, bg=HIGHLIGHT_COLOR, bd=2, relief='groove')
        error_frame.pack(fill='x', padx=10, pady=5, ipady=5)
        tk.Label(
            error_frame, 
            text=f"⚠️ خطأ في {symbol}: {error}", 
            fg=FG_COLOR, 
            bg=HIGHLIGHT_COLOR, 
            font=('Arial', 9, 'bold')
        ).pack(padx=5, pady=3)
    else:
        update_gui(symbol, prices, timestamps, interval, frame)

# تحديث كل البيانات
def refresh_data(container, interval):
    # مسح المحتوى الحالي
    for widget in container.winfo_children():
        widget.destroy()
    
    # إضافة شاشة تحميل
    loading_frame = tk.Frame(container, bg=BG_COLOR)
    loading_frame.pack(fill='both', expand=True)
    
    tk.Label(
        loading_frame, 
        text="جاري تحديث البيانات...", 
        font=('Arial', 14, 'bold'), 
        fg=ACCENT_COLOR, 
        bg=BG_COLOR
    ).pack(pady=20)
    
    # إنشاء بطاقات تحميل لكل رمز
    for symbol in SYMBOLS:
        card_frame = tk.Frame(container, bg=CARD_COLOR)
        card_frame.pack(fill='x', padx=10, pady=5)
        card_frame.symbol = symbol
        
        loading_label = tk.Label(
            card_frame, 
            text=f"جاري تحميل {symbol}...", 
            font=('Arial', 10, 'bold'), 
            fg=ACCENT_COLOR, 
            bg=CARD_COLOR
        )
        loading_label.pack(pady=20)
        
        # بدء جلب البيانات في مسار منفصل
        threading.Thread(
            target=fetch_data, 
            args=(symbol, interval, card_frame, 
                 lambda s, p, t, i, f, e=None: update_in_frame(card_frame, s, p, t, i, f, e, loading_label)),
            daemon=True
        ).start()

# تشغيل الواجهة
def run_app():
    root = tk.Tk()
    root.title("📈 المحلل الذكي للأسواق المالية")
    root.geometry("1000x700")
    root.configure(bg=BG_COLOR)
    root.iconbitmap('icon.ico')  # يمكنك إضافة أيقونة إذا رغبت

    # شريط العنوان
    header_frame = tk.Frame(root, bg=SECONDARY_COLOR, padx=15, pady=10)
    header_frame.pack(fill='x')
    
    title_label = tk.Label(
        header_frame, 
        text="📊 المحلل الذكي للأسواق المالية", 
        font=('Arial', 16, 'bold'), 
        fg=FG_COLOR, 
        bg=SECONDARY_COLOR
    )
    title_label.pack(side='left')
    
    # شريط التحكم
    control_frame = tk.Frame(root, bg=BG_COLOR, padx=10, pady=15)
    control_frame.pack(fill='x')
    
    tk.Label(
        control_frame, 
        text="الفاصل الزمني:", 
        font=('Arial', 10, 'bold'), 
        fg=FG_COLOR, 
        bg=BG_COLOR
    ).pack(side='left', padx=(10, 5))

    interval_var = tk.StringVar(value='1day')
    interval_menu = ttk.Combobox(
        control_frame, 
        textvariable=interval_var, 
        values=list(INTERVALS.keys()), 
        width=12, 
        state='readonly',
        font=('Arial', 10)
    )
    interval_menu.pack(side='left', padx=5)
    interval_menu.current(5)

    refresh_btn = tk.Button(
        control_frame, 
        text="تحديث الكل", 
        command=lambda: refresh_data(scroll_frame, INTERVALS[interval_var.get()]), 
        bg=BUTTON_COLOR, 
        fg=FG_COLOR,
        relief='flat',
        font=('Arial', 10, 'bold'),
        padx=15
    )
    refresh_btn.pack(side='left', padx=10)
    
    # معلومات التطبيق
    info_label = tk.Label(
        control_frame, 
        text="تطبيق المحلل الذكي - تقديم تحليلات فورية للأسواق المالية", 
        font=('Arial', 9), 
        fg='#95a5a6', 
        bg=BG_COLOR
    )
    info_label.pack(side='right', padx=10)

    # منطقة البيانات الرئيسية مع التمرير
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    canvas = tk.Canvas(main_frame, bg=BG_COLOR, highlightthickness=0)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=BG_COLOR)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # جلب البيانات الأولي
    refresh_data(scroll_frame, INTERVALS[interval_var.get()])
    
    # تحديث تلقائي كل 5 دقائق
    def auto_refresh():
        refresh_data(scroll_frame, INTERVALS[interval_var.get()])
        root.after(300000, auto_refresh)  # 300000 مللي ثانية = 5 دقائق
    
    root.after(300000, auto_refresh)
    
    root.mainloop()

if __name__ == '__main__':
    run_app()
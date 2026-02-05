import tkinter as tk
from tkinter import ttk, messagebox
import requests, webbrowser, urllib.parse
import pandas as pd
import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ترجمة النصوص الثابتة (واجهات وعناصر) باللغتين
UI_TEXT = {
    "en": {
        "title": "Forex Analyzer",
        "api_label": "API Key:",
        "pair_label": "Currency Pair:",
        "interval_label": "Timeframe:",
        "fetch_button": "Fetch Data",
        "chart_type_label": "Chart Type:",
        "line_chart": "Line",
        "candlestick_chart": "Candlestick",
        "ict_mode": "ICT Mode",
        "language": "العربية",  # show button to switch to Arabic
        "share_whatsapp": "Share via WhatsApp",
        "share_telegram": "Share via Telegram",
        "share_twitter": "Share via Twitter",
        "error_no_api": "Please enter API Key.",
        "error_fetch": "Error fetching data. Check API key and internet.",
    },
    "ar": {
        "title": "محلل الفوركس",
        "api_label": "مفتاح API:",
        "pair_label": "زوج العملة:",
        "interval_label": "الإطار الزمني:",
        "fetch_button": "جلب البيانات",
        "chart_type_label": "نوع الرسم:",
        "line_chart": "خطّي",
        "candlestick_chart": "شموع",
        "ict_mode": "وضع ICT",
        "language": "English",  # show button to switch to English
        "share_whatsapp": "مشاركة واتساب",
        "share_telegram": "مشاركة تيليجرام",
        "share_twitter": "مشاركة تويتر",
        "error_no_api": "يرجى إدخال مفتاح API.",
        "error_fetch": "خطأ في جلب البيانات. تحقق من المفتاح والاتصال.",
    }
}

# الفئة الرئيسية للتطبيق
class ForexAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # الإعدادات الأساسية للنافذة
        self.language = "ar"  # لغة الواجهة الافتراضية عربية
        self.title(UI_TEXT[self.language]["title"])
        self.geometry("1200x800")
        self.configure(bg="#2b2b2b")
        
        # متغيرات الحالة
        self.api_key = tk.StringVar()
        self.selected_pair = tk.StringVar()
        self.selected_interval = tk.StringVar(value="1h")  # الافتراضي 1 ساعة
        self.chart_type = tk.StringVar(value="candle")
        self.ict_mode = tk.BooleanVar(value=False)
        
        # البيانات والتحليل
        self.df = None  # DataFrame للبيانات
        self.analysis_text = ""  # النص التحليلي المولد
        
        # إنشاء الواجهة
        self.create_widgets()
        
    def create_widgets(self):
        # إطار علوي لعناصر التحكم
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # حقل مفتاح API
        api_label = ttk.Label(top_frame, text=UI_TEXT[self.language]["api_label"])
        api_entry = ttk.Entry(top_frame, textvariable=self.api_key, width=20, show="*")
        api_label.pack(side=tk.LEFT, padx=5)
        api_entry.pack(side=tk.LEFT, padx=5)
        
        # قائمة اختيار زوج العملة
        pair_label = ttk.Label(top_frame, text=UI_TEXT[self.language]["pair_label"])
        pair_label.pack(side=tk.LEFT, padx=5)
        pair_combo = ttk.Combobox(top_frame, textvariable=self.selected_pair, width=10)
        pair_combo['values'] = ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "USD/CAD"]  # قائمة مبسطة
        pair_combo.pack(side=tk.LEFT, padx=5)
        pair_combo.current(0)
        
        # قائمة اختيار الفاصل الزمني
        interval_label = ttk.Label(top_frame, text=UI_TEXT[self.language]["interval_label"])
        interval_label.pack(side=tk.LEFT, padx=5)
        interval_combo = ttk.Combobox(top_frame, textvariable=self.selected_interval, width=5)
        interval_combo['values'] = ["1min","5min","15min","1h","4h","1day"]
        interval_combo.pack(side=tk.LEFT, padx=5)
        interval_combo.current(3)  # 1h كخيار افتراضي
        
        # زر جلب البيانات
        fetch_button = ttk.Button(top_frame, text=UI_TEXT[self.language]["fetch_button"], command=self.fetch_data)
        fetch_button.pack(side=tk.LEFT, padx=10)
        
        # نوع الرسم البياني (راديو)
        chart_label = ttk.Label(top_frame, text=UI_TEXT[self.language]["chart_type_label"])
        chart_label.pack(side=tk.LEFT, padx=(20,5))
        radio_line = ttk.Radiobutton(top_frame, text=UI_TEXT[self.language]["line_chart"], value="line",
                                     variable=self.chart_type, command=self.update_chart)
        radio_candle = ttk.Radiobutton(top_frame, text=UI_TEXT[self.language]["candlestick_chart"], value="candle",
                                       variable=self.chart_type, command=self.update_chart)
        radio_line.pack(side=tk.LEFT, padx=2)
        radio_candle.pack(side=tk.LEFT, padx=2)
        
        # وضع ICT (Checkbutton)
        ict_check = ttk.Checkbutton(top_frame, text=UI_TEXT[self.language]["ict_mode"], variable=self.ict_mode, command=self.update_analysis_text)
        ict_check.pack(side=tk.LEFT, padx=(20,5))
        
        # زر تغيير اللغة
        lang_button = ttk.Button(top_frame, text=UI_TEXT[self.language]["language"], command=self.toggle_language)
        lang_button.pack(side=tk.RIGHT, padx=5)
        
        # إطار الرسم البياني
        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # إطار النص التحليلي ومشاركة
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # نص التحليل (Label قابل لاحتواء أسطر متعددة)
        self.analysis_label = tk.Label(bottom_frame, text="", bg="#2b2b2b", fg="white",
                                       justify=tk.LEFT, anchor="nw", font=("Arial", 10), wraplength=1100)
        self.analysis_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # إطار أزرار المشاركة
        share_frame = ttk.Frame(bottom_frame)
        share_frame.pack(side=tk.RIGHT, padx=5)
        wa_button = ttk.Button(share_frame, text=UI_TEXT[self.language]["share_whatsapp"], command=self.share_whatsapp)
        tg_button = ttk.Button(share_frame, text=UI_TEXT[self.language]["share_telegram"], command=self.share_telegram)
        tw_button = ttk.Button(share_frame, text=UI_TEXT[self.language]["share_twitter"], command=self.share_twitter)
        wa_button.pack(fill=tk.X, pady=2)
        tg_button.pack(fill=tk.X, pady=2)
        tw_button.pack(fill=tk.X, pady=2)
        
        # ملاحظة: في التصميم الفعلي قد نستبدل نصوص أزرار المشاركة بأيقونات لشكليّة أجمل
        
    def fetch_data(self):
        """جلب البيانات من API وحساب المؤشرات وإظهار الرسم والتحليل."""
        api_key = self.api_key.get().strip()
        if not api_key:
            messagebox.showerror("Error", UI_TEXT[self.language]["error_no_api"])
            return
        symbol = self.selected_pair.get()
        interval = self.selected_interval.get()
        # بناء رابط API
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=500&apikey={api_key}"
        try:
            resp = requests.get(url)
            data = resp.json()
        except Exception as e:
            messagebox.showerror("Error", UI_TEXT[self.language]["error_fetch"])
            return
        if "values" not in data:
            # حصل خطأ من API (قد يكون المفتاح خاطئ أو رمز غير مدعوم)
            messagebox.showerror("Error", UI_TEXT[self.language]["error_fetch"] + f"\n{data.get('message','')}")
            return
        # معالجة البيانات في DataFrame
        records = data["values"]
        df = pd.DataFrame(records)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        df.set_index('datetime', inplace=True)
        # تحويل الأعمدة الرقمية من نص إلى float
        numeric_cols = ["open","high","low","close","volume"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df.dropna(inplace=True)
        self.df = df  # حفظ البيانات في المتغير العام
        
        # حساب المؤشرات الفنية الأساسية
        self.calculate_technical_indicators()
        # تحديث الرسم البياني
        self.update_chart()
        # تحديث النص التحليلي
        self.update_analysis_text()
        
    def calculate_technical_indicators(self):
        """حساب المؤشرات الفنية (RSI, MACD, EMAs, Bollinger Bands, Pivot)."""
        df = self.df
        if df is None: 
            return
        # RSI 14
        delta = df['close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        window = 14
        avg_gain = up.rolling(window).mean()
        avg_loss = down.rolling(window).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        # MACD (12,26) and Signal (9)
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD_line'] = df['EMA12'] - df['EMA26']
        df['Signal_line'] = df['MACD_line'].ewm(span=9, adjust=False).mean()
        df['MACD_hist'] = df['MACD_line'] - df['Signal_line']
        # EMA 50 and 200
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
        # Bollinger Bands (20, 2)
        df['MA20'] = df['close'].rolling(20).mean()
        df['BB_up'] = df['MA20'] + 2*df['close'].rolling(20).std()
        df['BB_down'] = df['MA20'] - 2*df['close'].rolling(20).std()
        # Pivot (based on previous period if available)
        if len(df) > 1:
            prev = df.iloc[-2]  # استخدام ما قبل آخر شمعه متاحة كفترة سابقة
            P = (prev['high'] + prev['low'] + prev['close']) / 3
            R1 = 2*P - prev['low']
            S1 = 2*P - prev['high']
            R2 = P + (prev['high'] - prev['low'])
            S2 = P - (prev['high'] - prev['low'])
            # حفظها في خصائص الكائن لاستخدامها في النص
            self.pivot_levels = {"P": P, "R1": R1, "S1": S1, "R2": R2, "S2": S2}
        else:
            self.pivot_levels = {}
        
    def update_chart(self):
        """تحديث الرسم البياني حسب نوع الرسم المحدد."""
        if self.df is None:
            return
        # رسم البيانات باستخدام mplfinance
        chart_type = self.chart_type.get()
        # اختيار أسلوب ألوان (داكن)
        style = mpf.make_mpf_style(base_mpf_style='nightclouds', 
                                   mavcolors=["#ffd700", "#ffa500"],  # ألوان المتوسطات
                                   facecolor='#2b2b2b', gridcolor="#444444")
        # تحديد نوع الرسم: line أو candle
        if chart_type == "line":
            fig, axlist = mpf.plot(self.df, type='line', style=style, returnfig=True)
        else:
            # رسم الشموع مع المتوسطات وحجم التداول (اختياري)
            fig, axlist = mpf.plot(self.df, type='candle', style=style, mav=(50, 200),
                                    volume=False, returnfig=True)
        # تضمين الشكل في واجهة Tkinter
        for widget in self.chart_frame.winfo_children():
            widget.destroy()  # إزالة أي رسم سابق
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # Note: We do not add interactive toolbar for simplicity
    
    def update_analysis_text(self):
        """تحديث النص التحليلي (تقليدي أو ICT بحسب الوضع)."""
        if self.df is None:
            return
        df = self.df
        # الحصول على أحدث قيم للمؤشرات
        latest = df.iloc[-1]
        rsi_val = latest.get('RSI', None)
        macd_val = latest.get('MACD_line', None)
        signal_val = latest.get('Signal_line', None)
        ema50 = latest.get('EMA50', None)
        ema200 = latest.get('EMA200', None)
        close_price = latest['close']
        
        # نص التحليل التقليدي
        analysis_lines = []
        # RSI
        if rsi_val is not None:
            rsi_line = f"RSI: {rsi_val:.1f}"
            # إضافة دلالة التشبع
            if rsi_val >= 70:
                rsi_line += " (Overbought)" if self.language == "en" else " (تشبع شرائي)"
            elif rsi_val <= 30:
                rsi_line += " (Oversold)" if self.language == "en" else " (تشبع بيعي)"
            analysis_lines.append(rsi_line)
        # MACD
        if macd_val is not None and signal_val is not None:
            if macd_val > signal_val:
                macd_status = "MACD bullish (above signal)" if self.language == "en" else "تقاطع MACD صعودي (الخط أعلى الإشارة)"
            else:
                macd_status = "MACD bearish (below signal)" if self.language == "en" else "تقاطع MACD هبوطي (الخط أدنى الإشارة)"
            analysis_lines.append(macd_status)
        # EMA trend
        if ema50 is not None and ema200 is not None:
            if ema50 > ema200:
                trend = "Uptrend (50 EMA > 200 EMA)" if self.language == "en" else "اتجاه صاعد (EMA50 أعلى من EMA200)"
            elif ema50 < ema200:
                trend = "Downtrend (50 EMA < 200 EMA)" if self.language == "en" else "اتجاه هابط (EMA50 أدنى من EMA200)"
            else:
                trend = "EMAs overlapping (no clear trend)" if self.language == "en" else "تقاطع المتوسطات (لا اتجاه واضح)"
            analysis_lines.append(trend)
        # Bollinger Bands
        bb_up = latest.get('BB_up', None)
        bb_down = latest.get('BB_down', None)
        if bb_up is not None and bb_down is not None:
            if close_price >= bb_up:
                bb_line = "Price at upper Bollinger Band (potential resistance)" if self.language == "en" else "السعر عند الحد العلوي لبولينجر (مقاومة محتملة)"
            elif close_price <= bb_down:
                bb_line = "Price at lower Bollinger Band (potential support)" if self.language == "en" else "السعر عند الحد السفلي لبولينجر (دعم محتمل)"
            else:
                bb_line = ""  # لا شيء مميز
            if bb_line:
                analysis_lines.append(bb_line)
        # Pivot
        if getattr(self, 'pivot_levels', None):
            P = self.pivot_levels.get("P")
            if P:
                if close_price > P:
                    pivot_line = f"Above pivot {P:.4f} (bullish bias)" if self.language == "en" else f"السعر أعلى المحور {P:.4f} (ميل صاعد)"
                else:
                    pivot_line = f"Below pivot {P:.4f} (bearish bias)" if self.language == "en" else f"السعر أدنى المحور {P:.4f} (ميل هابط)"
                analysis_lines.append(pivot_line)
        
        # إن كان وضع ICT فعّال، نضيف مزيد من التحليل المتقدم:
        if self.ict_mode.get():
            # Liquidity levels (آخر قمة وقاع بارزة)
            recent_high = df['high'].iloc[-10:].max()  # أعلى سعر في آخر 10 فترات
            recent_low = df['low'].iloc[-10:].min()    # أدنى سعر في آخر 10 فترات
            liq_line = ""
            if close_price < recent_high:
                # يوجد سيولة فوق القمة الأخيرة
                liq_line += (f"Liquidity above {recent_high:.4f}. " if self.language=="en" 
                             else f"سيولة متجمعة فوق {recent_high:.4f}. ")
            if close_price > recent_low:
                # يوجد سيولة تحت القاع الأخير
                liq_line += (f"Liquidity below {recent_low:.4f}." if self.language=="en" 
                             else f"سيولة متجمعة تحت {recent_low:.4f}.")
            if liq_line:
                analysis_lines.append(liq_line.strip())
            # Market Structure
            structure = "Neutral"
            # نجد قمم وقيعان محلية أخيرة
            highs = df['high'].values
            lows = df['low'].values
            local_highs_idx = [i for i in range(1,len(highs)-1) if highs[i]>highs[i-1] and highs[i]>highs[i+1]]
            local_lows_idx  = [i for i in range(1,len(lows)-1) if lows[i]<lows[i-1] and lows[i]<lows[i+1]]
            if local_highs_idx and local_lows_idx:
                last_high_idx = local_highs_idx[-1]
                prev_high_idx = local_highs_idx[-2] if len(local_highs_idx)>1 else local_highs_idx[-1]
                last_low_idx = local_lows_idx[-1]
                prev_low_idx = local_lows_idx[-2] if len(local_lows_idx)>1 else local_lows_idx[-1]
                # هيكل صاعد إذا قمم وقيعان مرتفعة
                if highs[last_high_idx] > highs[prev_high_idx] and lows[last_low_idx] > lows[prev_low_idx]:
                    structure = "Bullish" if self.language=="en" else "صاعد"
                elif highs[last_high_idx] < highs[prev_high_idx] and lows[last_low_idx] < lows[prev_low_idx]:
                    structure = "Bearish" if self.language=="en" else "هابط"
            struct_line = f"Market Structure: {structure}" if self.language=="en" else f"هيكل السوق: {structure}"
            analysis_lines.append(struct_line)
            # Fair Value Gap (آخر فجوة سعرية)
            gaps = []
            highs = df['high'].values
            lows = df['low'].values
            for i in range(2, len(df)):
                if lows[i] > highs[i-2]:
                    gaps.append(("up", highs[i-2], lows[i]))
                if highs[i] < lows[i-2]:
                    gaps.append(("down", lows[i-2], highs[i]))
            if gaps:
                gap_type, g1, g2 = gaps[-1]  # آخر فجوة
                if gap_type == "up":
                    gap_text = (f"Upward FVG from {g1:.4f} to {g2:.4f}" if self.language=="en"
                                else f"فجوة سعرية صاعدة بين {g1:.4f} و {g2:.4f}")
                else:
                    gap_text = (f"Downward FVG from {g2:.4f} to {g1:.4f}" if self.language=="en"
                                else f"فجوة سعرية هابطة بين {g2:.4f} و {g1:.4f}")
                analysis_lines.append(gap_text)
            # Optimal Trade Entry (باستخدام فيبوناتشي 62%-79%)
            # نحدد موجة كبرى (هنا نستخدم نطاق 30 فترة أخيرة مثلا)
            recent_high = df['high'].iloc[-30:].max()
            recent_low = df['low'].iloc[-30:].min()
            # إذا الترند صاعد (close قريب من أعلى مستوى) سنفترض الموجة صعود من recent_low إلى recent_high
            fib_top = recent_high
            fib_bottom = recent_low
            if close_price < (recent_low + recent_high)/2:
                # ربما الترند كان هابط فنقلب
                fib_top, fib_bottom = recent_low, recent_high
            ote_high = fib_bottom + 0.79*(fib_top - fib_bottom)
            ote_low = fib_bottom + 0.62*(fib_top - fib_bottom)
            ote_line = (f"OTE zone ~[{ote_low:.4f} - {ote_high:.4f}]" if self.language=="en"
                        else f"منطقة دخول مثالية OTE تقريبًا [{ote_low:.4f} - {ote_high:.4f}]")
            analysis_lines.append(ote_line)
            # Recommendation + TP/SL
            reco = ""
            tp = None
            sl = None
            if "صاعد" in structure or "Bullish" in structure:
                reco = "Buy" if self.language=="en" else "شراء"
                # SL عند آخر قاع، TP عند آخر قمة
                sl = recent_low
                tp = recent_high
            elif "هابط" in structure or "Bearish" in structure:
                reco = "Sell" if self.language=="en" else "بيع"
                sl = recent_high
                tp = recent_low
            else:
                reco = "Neutral" if self.language=="en" else "محايد"
            reco_line = f"Recommendation: {reco}" if self.language=="en" else f"التوصية: {reco}"
            if reco != "Neutral" and reco != "محايد":
                reco_line += (f" (TP ~{tp:.4f}, SL ~{sl:.4f})" if self.language=="en"
                              else f" (هدف تقريبًا {tp:.4f}, وقف {sl:.4f})")
            analysis_lines.append(reco_line)
            # Scenarios
            if reco in ["Buy", "شراء"]:
                base_scenario = (f"Base: price rises towards ~{tp:.4f}" if self.language=="en"
                                 else f"أساسي: ارتفاع السعر نحو {tp:.4f}")
                alt_scenario = (f"Alternate: falls below {sl:.4f}" if self.language=="en"
                                 else f"بديل: الهبوط دون {sl:.4f}")
            elif reco in ["Sell", "بيع"]:
                base_scenario = (f"Base: price drops towards ~{tp:.4f}" if self.language=="en"
                                 else f"أساسي: هبوط السعر نحو {tp:.4f}")
                alt_scenario = (f"Alternate: rises above {sl:.4f}" if self.language=="en"
                                 else f"بديل: الارتفاع فوق {sl:.4f}")
            else:
                base_scenario = (f"Base: range-bound movement" if self.language=="en" else f"أساسي: حركة عرضية")
                alt_scenario = (f"Alternate: breakout triggers trend" if self.language=="en" else f"بديل: كسر المستوى يؤدي لاتجاه جديد")
            scenario_line = base_scenario + (" / " + alt_scenario if alt_scenario else "")
            analysis_lines.append(scenario_line)
        
        # جمع كل الأسطر
        full_text = "\n".join(analysis_lines)
        # تحديث الـ Label النصي على الواجهة
        self.analysis_label.config(text=full_text)
        # محاذاة النص بحسب اللغة
        if self.language == "ar":
            self.analysis_label.config(justify=tk.RIGHT, anchor="ne")
        else:
            self.analysis_label.config(justify=tk.LEFT, anchor="nw")
        # حفظ النص الكامل لمشاركة المحتوى
        self.analysis_text = full_text
    
    def share_whatsapp(self):
        if not self.analysis_text:
            return
        text = urllib.parse.quote(self.analysis_text)
        url = f"https://wa.me/?text={text}"
        webbrowser.open(url)
        
    def share_telegram(self):
        if not self.analysis_text:
            return
        text = urllib.parse.quote(self.analysis_text)
        url = f"https://telegram.me/share/url?text={text}"
        webbrowser.open(url)
    
    def share_twitter(self):
        if not self.analysis_text:
            return
        text = urllib.parse.quote(self.analysis_text)
        url = f"https://twitter.com/intent/tweet?text={text}"
        webbrowser.open(url)
        
    def toggle_language(self):
        # تبديل اللغة
        self.language = "en" if self.language == "ar" else "ar"
        # تحديث عنوان النافذة
        self.title(UI_TEXT[self.language]["title"])
        # تحديث كل النصوص في الواجهة
        for child in self.winfo_children():
            self._update_widget_text(child)
        # إعادة تحديث النص التحليلي الحالي بلغة جديدة
        self.update_analysis_text()
        
    def _update_widget_text(self, widget):
        """تحديث النص لعنصر واجهة واحد بحسب اللغة الحالية (يعمل بشكل递归 على الأبناء)."""
        # تحقق من نوع العنصر لتحديد خاصية النص المناسبة
        if isinstance(widget, ttk.Label) or isinstance(widget, ttk.Button) or isinstance(widget, ttk.Checkbutton) or isinstance(widget, ttk.Radiobutton):
            text = widget.cget("text")
            # البحث عن النص المطابق في معجم اللغة الأخرى واستبداله
            # (نعكس البحث عبر القواميس)
            other_lang = "ar" if self.language == "en" else "en"
            for key, val in UI_TEXT[other_lang].items():
                if val == text:
                    # وجدنا المفتاح المقابل في اللغة الأخرى
                    new_text = UI_TEXT[self.language].get(key, text)
                    widget.config(text=new_text)
                    break
        # إعادة تسمية أزرار المشاركة واللغة بشكل خاص
        if isinstance(widget, ttk.Button):
            # زر اللغة
            if widget.cget("text") in ["English", "العربية"]:
                widget.config(text=UI_TEXT[self.language]["language"])
        # تابع تحديث الأبناء
        for child in widget.winfo_children():
            self._update_widget_text(child)


# تشغيل التطبيق
if __name__ == "__main__":
    app = ForexAnalyzerApp()
    app.mainloop()

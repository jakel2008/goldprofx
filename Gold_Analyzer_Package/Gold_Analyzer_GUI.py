import tkinter as tk
from tkinter import messagebox, ttk
import yfinance as yf
import pandas as pd
import ta
import datetime

class GoldAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gold Analyzer Pro")
        self.root.geometry("650x500")  # زيادة حجم النافذة
        self.root.resizable(False, False)

        # تنسيق الواجهة
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 12), padding=5)
        self.style.configure("TLabel", font=("Arial", 11))
        self.style.configure("Header.TLabel", font=("Arial", 14, "bold"), foreground="#2c3e50")

        # عناصر الواجهة
        self.label = ttk.Label(root, text="تحليل الذهب - Gold Analyzer Pro", style="Header.TLabel")
        self.label.pack(pady=20)

        self.analyze_btn = ttk.Button(root, text="ابدأ التحليل", command=self.analyze_gold)
        self.analyze_btn.pack(pady=15)

        self.output_text = tk.Text(root, height=16, width=75, font=("Courier", 10), bg="#f8f9fa", wrap=tk.WORD)
        self.output_text.pack(pady=10, padx=10)

    def analyze_gold(self):
        self.output_text.delete("1.0", tk.END)
        try:
            # الحصول على التواريخ
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=180)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # تحميل بيانات الذهب
            data = yf.download('GC=F', start=start_str, end=end_str, interval='1d')
            
            # التحقق من وجود بيانات
            if data.empty:
                raise ValueError("❗ لم يتم العثور على بيانات الرجاء التحقق من الاتصال بالإنترنت")

            # ترتيب البيانات وتنظيفها
            data = data.sort_index(ascending=True)
            close_prices = data['Close'].squeeze()  # تحويل إلى 1D array

            # حساب المؤشرات الفنية
            data['rsi'] = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()
            macd = ta.trend.MACD(close=close_prices, window_slow=26, window_fast=12)
            data['macd_diff'] = macd.macd_diff()
            data['ema20'] = ta.trend.EMAIndicator(close=close_prices, window=20).ema_indicator()
            data['ema50'] = ta.trend.EMAIndicator(close=close_prices, window=50).ema_indicator()

            # استخراج آخر قيمة
            last_row = data.iloc[-1]

            # بناء التقرير
            report = (
                f"آخر تحديث: {data.index[-1].strftime('%Y-%m-%d %H:%M')}\n"
                f"----------------------------------------\n"
                f"سعر الإغلاق: {last_row['Close']:.2f} دولار\n"
                f"RSI (14): {last_row['rsi']:.2f}\n"
                f"MACD: {last_row['macd_diff']:.4f}\n"
                f"EMA 20: {last_row['ema20']:.2f}\n"
                f"EMA 50: {last_row['ema50']:.2f}\n"
                f"----------------------------------------\n"
            )

            # تحديد الإشارة
            if last_row['rsi'] < 30 and last_row['ema20'] > last_row['ema50']:
                report += "\n📈 إشارة شراء قوية:\n- RSI أقل من 30 (تشبع بيع)\n- EMA 20 أعلى من EMA 50 (اتجاه صاعد)"
            elif last_row['rsi'] > 70 and last_row['ema20'] < last_row['ema50']:
                report += "\n📉 إشارة بيع قوية:\n- RSI أعلى من 70 (تشبع شراء)\n- EMA 20 أقل من EMA 50 (اتجاه هابط)"
            else:
                report += "\n🟡 لا توجد إشارة قوية:\n- الانتظار حتى ظهور إشارات أوضح"

            self.output_text.insert(tk.END, report)
            
        except Exception as e:
            messagebox.showerror("خطأ فني", f"حدث خطأ غير متوقع:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GoldAnalyzerApp(root)
    root.mainloop()
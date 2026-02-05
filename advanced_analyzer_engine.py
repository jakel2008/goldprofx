# -*- coding: utf-8 -*-
"""
Advanced Forex Analyzer Engine - Complete Analysis System
Based on original tkinter code with full indicators
"""
import pandas as pd
import numpy as np
import ta
from datetime import datetime

def analyze_with_indicators(df):
    """تحليل شامل مع جميع المؤشرات"""
    # التأكد من وجود الأعمدة الأساسية
    if 'Close' not in df.columns:
        raise ValueError(f"العمود 'Close' غير موجود. الأعمدة المتوفرة: {df.columns.tolist()}")
    
    if len(df) < 50:
        return df
    
    # Bollinger Bands
    if len(df) >= 20:
        bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
        df["BB_High"] = bb.bollinger_hband()
        df["BB_Low"] = bb.bollinger_lband()
        df["BB_Mid"] = bb.bollinger_mavg()
    
    # RSI
    if len(df) >= 14:
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    
    # MACD
    if len(df) >= 26:
        macd = ta.trend.MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9)
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Hist"] = macd.macd_diff()
    
    # EMAs
    if len(df) >= 50:
        df["EMA_50"] = ta.trend.ema_indicator(df["Close"], window=50)
    if len(df) >= 200:
        df["EMA_200"] = ta.trend.ema_indicator(df["Close"], window=200)
    
    # Stochastic
    if len(df) >= 14:
        stoch = ta.momentum.StochasticOscillator(
            high=df["High"], 
            low=df["Low"], 
            close=df["Close"], 
            window=14, 
            smooth_window=3
        )
        df['STOCH_K'] = stoch.stoch()
        df['STOCH_D'] = stoch.stoch_signal()
    
    # ATR
    if len(df) >= 14:
        df["ATR"] = ta.volatility.AverageTrueRange(
            high=df["High"], 
            low=df["Low"], 
            close=df["Close"], 
            window=14
        ).average_true_range()
    
    return df

def calculate_fibonacci_levels(df):
    """حساب مستويات فيبوناتشي"""
    if df.empty or len(df) < 10:
        return {}
    
    recent_df = df.tail(100)
    high = recent_df["High"].max()
    low = recent_df["Low"].min()
    diff = high - low
    
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
    """حساب نقاط الارتكاز"""
    if df.empty or len(df) < 2:
        return None, None, None, None, None
    
    df['DateOnly'] = pd.to_datetime(df['Date']).dt.date
    last_date = df.iloc[-1]["DateOnly"]
    prev_dates = df[df['DateOnly'] < last_date]['DateOnly'].unique()
    
    if len(prev_dates) == 0:
        # استخدام آخر 24 شمعة
        prev_day_df = df.tail(24)
    else:
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
    """حساب التقلبات"""
    if len(df) < 20:
        return 1.0
    
    returns = np.log(df['Close'] / df['Close'].shift(1)).dropna()
    volatility = returns.std() * np.sqrt(252) * 100
    
    return volatility

def calculate_tp_sl(recommendation, entry_price, atr_value, volatility):
    """حساب مستويات جني الربح ووقف الخسارة"""
    if volatility > 2.0:
        tp_multipliers = [1.0, 1.8, 2.5]
        sl_multiplier = 1.2
    elif volatility < 0.5:
        tp_multipliers = [0.8, 1.2, 1.8]
        sl_multiplier = 0.8
    else:
        tp_multipliers = [1.2, 1.8, 2.5]
        sl_multiplier = 1.0
    
    if "قوي" in recommendation:
        tp_multipliers = [x * 1.2 for x in tp_multipliers]
    elif "محتمل" in recommendation:
        tp_multipliers = [x * 0.8 for x in tp_multipliers]
    
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
    else:
        tp1 = entry_price + 0.5 * atr_value
        tp2 = entry_price + 1.0 * atr_value
        tp3 = entry_price + 1.5 * atr_value
        sl = entry_price - 0.5 * atr_value
    
    return tp1, tp2, tp3, sl

def detect_comprehensive_signals(df, symbol, interval):
    """كشف الإشارات الشامل مع جميع المؤشرات"""
    signals = []
    signals.append(f"📈 تحليل {symbol} ({interval})")
    signals.append("=" * 50)
    
    if df.empty or len(df) < 50:
        signals.append("⚠️ بيانات غير كافية للتحليل")
        return signals, "حياد", {}, {}

    entry_price = df.iloc[-1]["Close"]
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    pp, r1, r2, s1, s2 = calculate_pivot_point(df)
    fib_levels = calculate_fibonacci_levels(df)

    signals.append(f"📊 السعر الحالي: {round(entry_price, 5)}")
    
    # نظام النقاط المتقدم
    buy_score = 0
    sell_score = 0
    confidence_factors = []
    
    # 1. RSI Analysis
    if 'RSI' in df.columns and not np.isnan(last["RSI"]):
        rsi_value = last["RSI"]
        if rsi_value > 70:
            signals.append(f"📉 RSI: {round(rsi_value, 2)} (⬆️ شراء مفرط)")
            signals.append("⚡ إشارة: مؤشر القوة النسبية في منطقة الشراء المفرط")
            sell_score += 1
            confidence_factors.append("RSI في منطقة الشراء المفرط")
        elif rsi_value < 30:
            signals.append(f"📉 RSI: {round(rsi_value, 2)} (⬇️ بيع مفرط)")
            signals.append("⚡ إشارة: مؤشر القوة النسبية في منطقة البيع المفرط")
            buy_score += 1
            confidence_factors.append("RSI في منطقة البيع المفرط")
        else:
            signals.append(f"📉 RSI: {round(rsi_value, 2)} (⚖️ طبيعي)")
    
    # 2. MACD Analysis
    if 'MACD' in df.columns and not np.isnan(last["MACD"]):
        macd_diff = last['MACD'] - last['MACD_Signal']
        if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
            signals.append("📈 MACD: ⬆️ إيجابي")
            signals.append("⚡ إشارة: تقاطع MACD إيجابي (إشارة شراء)")
            buy_score += 2
            confidence_factors.append("تقاطع MACD إيجابي")
        elif last['MACD'] < last['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
            signals.append("📈 MACD: ⬇️ سلبي")
            signals.append("⚡ إشارة: تقاطع MACD سلبي (إشارة بيع)")
            sell_score += 2
            confidence_factors.append("تقاطع MACD سلبي")
        else:
            signals.append(f"📈 MACD: {round(macd_diff, 5)}")
    
    # 3. EMA Crossover
    if len(df) >= 200 and 'EMA_50' in df.columns and 'EMA_200' in df.columns:
        if last['EMA_50'] > last['EMA_200'] and prev['EMA_50'] <= prev['EMA_200']:
            signals.append("⚡ إشارة: تقاطع المتوسطات المتحركة (إشارة شراء)")
            buy_score += 2
            confidence_factors.append("تقاطع المتوسطات لصالح الشراء")
        elif last['EMA_50'] < last['EMA_200'] and prev['EMA_50'] >= prev['EMA_200']:
            signals.append("⚡ إشارة: تقاطع المتوسطات المتحركة (إشارة بيع)")
            sell_score += 2
            confidence_factors.append("تقاطع المتوسطات لصالح البيع")
    
    # 4. Bollinger Bands
    if "BB_Low" in df.columns and not pd.isna(last["BB_Low"]):
        if last['Close'] < last['BB_Low']:
            signals.append("⚡ إشارة: السعر تحت باند بولينجر السفلي (إشارة شراء)")
            buy_score += 1
            confidence_factors.append("السعر تحت باند بولينجر السفلي")
    if "BB_High" in df.columns and not pd.isna(last["BB_High"]):
        if last['Close'] > last['BB_High']:
            signals.append("⚡ إشارة: السعر فوق باند بولينجر العلوي (إشارة بيع)")
            sell_score += 1
            confidence_factors.append("السعر فوق باند بولينجر العلوي")
    
    # 5. Fibonacci Levels
    if fib_levels:
        for level, price in fib_levels.items():
            if abs(entry_price - price) < (entry_price * 0.001):
                if level in ["61.8%", "78.6%"]:
                    signals.append(f"⚡ إشارة: السعر قرب مستوى فيبوناتشي {level} (إشارة شراء)")
                    buy_score += 1
                    confidence_factors.append(f"قرب فيبوناتشي {level}")
                elif level in ["23.6%", "38.2%"]:
                    signals.append(f"⚡ إشارة: السعر قرب مستوى فيبوناتشي {level} (إشارة بيع)")
                    sell_score += 1
                    confidence_factors.append(f"قرب فيبوناتشي {level}")
    
    # 6. Pivot Points
    if r1 and entry_price > r1:
        signals.append("⚡ إشارة: السعر فوق نقطة الارتكاز (إشارة شراء)")
        buy_score += 1
        confidence_factors.append("فوق نقطة الارتكاز")
    if s1 and entry_price < s1:
        signals.append("⚡ إشارة: السعر تحت نقطة الارتكاز (إشارة بيع)")
        sell_score += 1
        confidence_factors.append("تحت نقطة الارتكاز")
    
    # 7. Stochastic
    if 'STOCH_K' in df.columns and 'STOCH_D' in df.columns:
        if last['STOCH_K'] < 20 and last['STOCH_D'] < 20:
            buy_score += 0.5
            confidence_factors.append("ستوكاستك في منطقة البيع المفرط")
        elif last['STOCH_K'] > 80 and last['STOCH_D'] > 80:
            sell_score += 0.5
            confidence_factors.append("ستوكاستك في منطقة الشراء المفرط")
    
    # 8. Price vs BB_Mid
    if "BB_Mid" in df.columns and not pd.isna(last["BB_Mid"]):
        if last['Close'] > last['BB_Mid']:
            buy_score += 0.5
        else:
            sell_score += 0.5
    
    # 9. Trend Direction
    if len(df) > 100:
        short_ma = df['Close'].tail(20).mean()
        long_ma = df['Close'].tail(50).mean()
        if short_ma > long_ma:
            buy_score += 0.5
            confidence_factors.append("اتجاه صاعد")
        else:
            sell_score += 0.5
            confidence_factors.append("اتجاه هابط")
    
    # تحديد التوصية
    if buy_score > sell_score:
        if buy_score >= 4:
            final_recommendation = "شراء قوي"
            confidence = "🔥 ثقة عالية"
        elif buy_score >= 2.5:
            final_recommendation = "شراء"
            confidence = "🟢 ثقة متوسطة"
        else:
            final_recommendation = "شراء محتمل"
            confidence = "🟡 ثقة منخفضة"
    elif sell_score > buy_score:
        if sell_score >= 4:
            final_recommendation = "بيع قوي"
            confidence = "🔥 ثقة عالية"
        elif sell_score >= 2.5:
            final_recommendation = "بيع"
            confidence = "🔴 ثقة متوسطة"
        else:
            final_recommendation = "بيع محتمل"
            confidence = "🟠 ثقة منخفضة"
    else:
        final_recommendation = "حياد"
        confidence = "⚪ انتظار"
    
    signals.append(f"\n🔰 مستوى الثقة: {confidence}")
    signals.append(f"📌 الإشارات المؤثرة: {', '.join(confidence_factors[:3]) if confidence_factors else 'لا توجد إشارات قوية'}")
    signals.append(f"📊 نقاط الشراء: {buy_score:.1f} | نقاط البيع: {sell_score:.1f}")
    
    # Detailed Indicator Analysis
    signals.append("\n" + "="*50)
    signals.append("📈 تحليل المؤشرات الفنية بالتفصيل")
    signals.append("="*50)
    
    # RSI Detailed
    if 'RSI' in df.columns and not np.isnan(last["RSI"]):
        rsi_val = round(last["RSI"], 2)
        signals.append(f"\n🔹 مؤشر القوة النسبية (RSI):")
        signals.append(f"   القيمة: {rsi_val}")
        if rsi_val > 70:
            signals.append(f"   التفسير: ⚠️ منطقة تشبع شرائي - احتمال انعكاس هبوطي")
            signals.append(f"   التوصية: حذر من الشراء، مراقبة إشارات البيع")
        elif rsi_val < 30:
            signals.append(f"   التفسير: ✅ منطقة تشبع بيعي - فرصة شراء محتملة")
            signals.append(f"   التوصية: مراقبة تأكيد الانعكاس الصعودي")
        else:
            signals.append(f"   التفسير: ⚖️ منطقة محايدة - السعر ضمن النطاق الطبيعي")
            signals.append(f"   التوصية: انتظار إشارات إضافية")
    
    # MACD Detailed
    if 'MACD' in df.columns and not np.isnan(last["MACD"]):
        macd_val = round(last['MACD'], 5)
        signal_val = round(last['MACD_Signal'], 5)
        histogram = round(macd_val - signal_val, 5)
        signals.append(f"\n🔹 MACD (تقارب وتباعد المتوسطات):")
        signals.append(f"   MACD: {macd_val} | Signal: {signal_val}")
        signals.append(f"   Histogram: {histogram}")
        if macd_val > signal_val:
            signals.append(f"   التفسير: 📈 زخم إيجابي - الاتجاه صاعد")
            signals.append(f"   التوصية: إشارة شراء نشطة، تابع الزخم")
        else:
            signals.append(f"   التفسير: 📉 زخم سلبي - الاتجاه هابط")
            signals.append(f"   التوصية: إشارة بيع نشطة، احذر الدخول شراء")
    
    # EMA Detailed
    if 'EMA_50' in df.columns and 'EMA_200' in df.columns:
        ema50 = round(last['EMA_50'], 5)
        ema200 = round(last['EMA_200'], 5)
        signals.append(f"\n🔹 المتوسطات المتحركة الأسية (EMA):")
        signals.append(f"   EMA 50: {ema50}")
        signals.append(f"   EMA 200: {ema200}")
        if ema50 > ema200:
            diff_percent = ((ema50 - ema200) / ema200) * 100
            signals.append(f"   التفسير: 🟢 الاتجاه العام صاعد ({diff_percent:.2f}%)")
            signals.append(f"   التوصية: الاتجاه العام إيجابي، فرص شراء متاحة")
        else:
            diff_percent = ((ema200 - ema50) / ema200) * 100
            signals.append(f"   التفسير: 🔴 الاتجاه العام هابط ({diff_percent:.2f}%)")
            signals.append(f"   التوصية: الاتجاه العام سلبي، احذر الشراء")
    
    # Bollinger Bands Detailed
    if "BB_Low" in df.columns and "BB_High" in df.columns:
        bb_low = round(last['BB_Low'], 5)
        bb_mid = round(last['BB_Mid'], 5)
        bb_high = round(last['BB_High'], 5)
        bb_width = round(((bb_high - bb_low) / bb_mid) * 100, 2)
        signals.append(f"\n🔹 نطاقات بولينجر (Bollinger Bands):")
        signals.append(f"   النطاق العلوي: {bb_high}")
        signals.append(f"   الخط الأوسط: {bb_mid}")
        signals.append(f"   النطاق السفلي: {bb_low}")
        signals.append(f"   عرض النطاق: {bb_width}%")
        
        if entry_price < bb_low:
            signals.append(f"   التفسير: ⚡ السعر خارج النطاق السفلي - تشبع بيعي")
            signals.append(f"   التوصية: فرصة شراء قوية، انتظر الارتداد للتأكيد")
        elif entry_price > bb_high:
            signals.append(f"   التفسير: ⚠️ السعر خارج النطاق العلوي - تشبع شرائي")
            signals.append(f"   التوصية: احذر الشراء، فرصة بيع محتملة")
        elif entry_price > bb_mid:
            signals.append(f"   التفسير: 📈 السعر فوق الوسط - ضغط شرائي")
            signals.append(f"   التوصية: الزخم إيجابي حالياً")
        else:
            signals.append(f"   التفسير: 📉 السعر تحت الوسط - ضغط بيعي")
            signals.append(f"   التوصية: الزخم سلبي حالياً")
        
        if bb_width > 3:
            signals.append(f"   ملاحظة: تقلبات عالية (نطاق واسع)")
        elif bb_width < 1:
            signals.append(f"   ملاحظة: توقع حركة قوية قريباً (نطاق ضيق)")
    
    # Stochastic Detailed
    if 'STOCH_K' in df.columns and 'STOCH_D' in df.columns:
        stoch_k = round(last['STOCH_K'], 2)
        stoch_d = round(last['STOCH_D'], 2)
        signals.append(f"\n🔹 مؤشر الستوكاستك:")
        signals.append(f"   %K: {stoch_k} | %D: {stoch_d}")
        if stoch_k > 80 and stoch_d > 80:
            signals.append(f"   التفسير: ⚠️ منطقة تشبع شرائي قصير المدى")
            signals.append(f"   التوصية: احتمال تصحيح هبوطي قريب")
        elif stoch_k < 20 and stoch_d < 20:
            signals.append(f"   التفسير: ✅ منطقة تشبع بيعي قصير المدى")
            signals.append(f"   التوصية: احتمال ارتداد صعودي قريب")
        else:
            signals.append(f"   التفسير: ⚖️ منطقة محايدة")
    
    # ATR Detailed
    if 'ATR' in df.columns and not np.isnan(last["ATR"]):
        atr_val = round(last["ATR"], 5)
        atr_percent = round((atr_val / entry_price) * 100, 2)
        signals.append(f"\n🔹 متوسط المدى الحقيقي (ATR):")
        signals.append(f"   القيمة: {atr_val} ({atr_percent}%)")
        if atr_percent > 1.5:
            signals.append(f"   التفسير: 🔥 تقلبات عالية جداً")
            signals.append(f"   التوصية: احذر، استخدم أحجام صغيرة ووقف خسارة واسع")
        elif atr_percent < 0.5:
            signals.append(f"   التفسير: 😴 سوق هادئ، تقلبات منخفضة")
            signals.append(f"   التوصية: انتظر كسر النطاق لحركة قوية")
        else:
            signals.append(f"   التفسير: ⚖️ تقلبات طبيعية")
            signals.append(f"   التوصية: ظروف تداول مناسبة")
    
    # Pivot Points & Support/Resistance
    signals.append("\n" + "="*50)
    signals.append("📍 المستويات المحورية والدعم والمقاومة")
    signals.append("="*50)
    
    if pp is not None:
        signals.append(f"\n🎯 نقطة الارتكاز (Pivot Point): {round(pp, 5)}")
        signals.append(f"\n🔴 مستويات المقاومة:")
        signals.append(f"   R1: {round(r1, 5)} - مقاومة أولى")
        signals.append(f"   R2: {round(r2, 5)} - مقاومة ثانية (قوية)")
        signals.append(f"\n🟢 مستويات الدعم:")
        signals.append(f"   S1: {round(s1, 5)} - دعم أول")
        signals.append(f"   S2: {round(s2, 5)} - دعم ثاني (قوي)")
        
        if entry_price > pp:
            signals.append(f"\n💡 السعر فوق المحور: الاتجاه قصير المدى صاعد")
            signals.append(f"   الهدف التالي: R1 ({round(r1, 5)})")
        else:
            signals.append(f"\n💡 السعر تحت المحور: الاتجاه قصير المدى هابط")
            signals.append(f"   الهدف التالي: S1 ({round(s1, 5)})")
    
    # Fibonacci Levels
    if fib_levels:
        signals.append("\n" + "="*50)
        signals.append("✨ مستويات فيبوناتشي - نقاط التحول المحتملة")
        signals.append("="*50)
        
        for level, price in sorted(fib_levels.items(), key=lambda x: x[1], reverse=True):
            distance = abs(entry_price - price)
            distance_percent = (distance / entry_price) * 100
            
            if distance_percent < 0.1:
                signals.append(f"\n⚡ {level}: {price:.5f} ← السعر الحالي هنا (قريب جداً!)")
                if level in ["61.8%", "78.6%"]:
                    signals.append(f"   💡 مستوى ارتداد قوي - فرصة شراء")
                elif level in ["23.6%", "38.2%"]:
                    signals.append(f"   💡 مستوى مقاومة - فرصة بيع")
            elif distance_percent < 0.5:
                signals.append(f"➡️ {level}: {price:.5f} (قريب - مراقبة)")
            else:
                signals.append(f"• {level}: {price:.5f}")
        
        # Fibonacci Strategy
        signals.append(f"\n💡 استراتيجية فيبوناتشي:")
        if entry_price < fib_levels.get("61.8%", 0):
            signals.append(f"   - السعر في منطقة الشراء (تحت 61.8%)")
            signals.append(f"   - انتظر الارتداد من 61.8% أو 78.6% للدخول شراء")
        elif entry_price > fib_levels.get("38.2%", 0):
            signals.append(f"   - السعر في منطقة البيع (فوق 38.2%)")
            signals.append(f"   - انتظر الارتداد من 38.2% أو 23.6% للدخول بيع")
    
    # Calculate TP/SL
    volatility = calculate_volatility(df)
    atr_value = last["ATR"] if "ATR" in df.columns and not np.isnan(last["ATR"]) else (df["High"].mean() - df["Low"].mean()) * 0.003
    tp1, tp2, tp3, sl = calculate_tp_sl(final_recommendation, entry_price, atr_value, volatility)
    
    # Volatility Analysis
    signals.append("\n" + "="*50)
    signals.append("📊 تحليل التقلبات وإدارة المخاطر")
    signals.append("="*50)
    
    volatility_status = ""
    risk_advice = ""
    if volatility > 2.0:
        volatility_status = "🟠 تقلبات عالية - سوق متحرك"
        risk_advice = "استخدم أحجام صغيرة (1-2% من الحساب) ووقف خسارة واسع"
    elif volatility < 0.5:
        volatility_status = "🟢 تقلبات منخفضة - سوق هادئ"
        risk_advice = "يمكنك زيادة الحجم قليلاً (2-3% من الحساب) مع وقف خسارة ضيق"
    else:
        volatility_status = "⚪ تقلب طبيعي - ظروف عادية"
        risk_advice = "استخدم حجم طبيعي (2% من الحساب) مع وقف خسارة معتدل"
    
    signals.append(f"\n📈 معدل التقلب: {volatility:.2f}%")
    signals.append(f"🎚️ الحالة: {volatility_status}")
    signals.append(f"💼 نصيحة إدارة المخاطر: {risk_advice}")
    
    # Trading Plan
    signals.append("\n" + "="*50)
    signals.append("🎯 خطة التداول المقترحة")
    signals.append("="*50)
    
    signals.append(f"\n📍 نقطة الدخول المثالية: {round(entry_price, 5)}")
    
    if final_recommendation in ["شراء قوي", "شراء", "شراء محتمل"]:
        signals.append(f"\n✅ استراتيجية الشراء:")
        signals.append(f"   1️⃣ الدخول الفوري: عند السعر الحالي {round(entry_price, 5)}")
        if s1:
            signals.append(f"   2️⃣ دخول تحسيني: انتظر الارتداد من الدعم S1 ({round(s1, 5)})")
        signals.append(f"\n🎯 أهداف جني الأرباح:")
        signals.append(f"   TP1: {round(tp1, 5)} - جني 30% من الصفقة")
        signals.append(f"   TP2: {round(tp2, 5)} - جني 40% من الصفقة")
        signals.append(f"   TP3: {round(tp3, 5)} - جني 30% المتبقي")
        signals.append(f"\n🛑 وقف الخسارة: {round(sl, 5)}")
        potential_loss = abs(entry_price - sl)
        potential_gain_tp1 = abs(tp1 - entry_price)
        risk_reward = round(potential_gain_tp1 / potential_loss, 2) if potential_loss > 0 else 0
        signals.append(f"⚖️ نسبة المخاطرة/العائد: 1:{risk_reward}")
    
    elif final_recommendation in ["بيع قوي", "بيع", "بيع محتمل"]:
        signals.append(f"\n🔻 استراتيجية البيع:")
        signals.append(f"   1️⃣ الدخول الفوري: عند السعر الحالي {round(entry_price, 5)}")
        if r1:
            signals.append(f"   2️⃣ دخول تحسيني: انتظر الارتداد من المقاومة R1 ({round(r1, 5)})")
        signals.append(f"\n🎯 أهداف جني الأرباح:")
        signals.append(f"   TP1: {round(tp1, 5)} - جني 30% من الصفقة")
        signals.append(f"   TP2: {round(tp2, 5)} - جني 40% من الصفقة")
        signals.append(f"   TP3: {round(tp3, 5)} - جني 30% المتبقي")
        signals.append(f"\n🛑 وقف الخسارة: {round(sl, 5)}")
        potential_loss = abs(entry_price - sl)
        potential_gain_tp1 = abs(entry_price - tp1)
        risk_reward = round(potential_gain_tp1 / potential_loss, 2) if potential_loss > 0 else 0
        signals.append(f"⚖️ نسبة المخاطرة/العائد: 1:{risk_reward}")
    
    else:  # حياد
        signals.append(f"\n⚪ وضع الانتظار:")
        signals.append(f"   - الإشارات متضاربة حالياً")
        signals.append(f"   - يُنصح بالانتظار حتى تتضح الصورة")
        signals.append(f"   - راقب كسر المقاومة {round(r1, 5)} للشراء")
        signals.append(f"   - راقب كسر الدعم {round(s1, 5)} للبيع")
    
    # Additional Recommendations
    signals.append("\n" + "="*50)
    signals.append("💡 توصيات إضافية ونصائح مهمة")
    signals.append("="*50)
    
    signals.append(f"\n🔔 أفضل وقت للتداول:")
    signals.append(f"   - جلسة لندن: 9:00 - 17:00 GMT")
    signals.append(f"   - جلسة نيويورك: 13:00 - 21:00 GMT")
    signals.append(f"   - أفضل فترة: تقاطع لندن ونيويورك (13:00 - 17:00)")
    
    signals.append(f"\n⚠️ احذر من:")
    signals.append(f"   - الأخبار الاقتصادية الهامة (NFP, FOMC, GDP)")
    signals.append(f"   - السبريد العالي في أوقات الافتتاح والإغلاق")
    signals.append(f"   - التداول ضد الاتجاه العام على الأطر الأكبر")
    
    signals.append(f"\n📊 تأكيدات إضافية مطلوبة:")
    signals.append(f"   - انتظر إغلاق الشمعة الحالية للتأكيد")
    signals.append(f"   - راقب حجم التداول (Volume) للتأكد من قوة الحركة")
    signals.append(f"   - تحقق من الأطر الزمنية الأكبر (4H, Daily)")
    
    signals.append(f"\n💰 إدارة رأس المال:")
    signals.append(f"   - لا تخاطر بأكثر من 2% من رأس المال في صفقة واحدة")
    signals.append(f"   - لا تفتح أكثر من 3 صفقات متزامنة")
    signals.append(f"   - استخدم ترالينج ستوب بعد تحقق TP1")
    signals.append(f"   - قم بتحريك وقف الخسارة للتعادل عند TP1")
    
    # Market Conditions Summary
    signals.append("\n" + "="*50)
    signals.append("📋 ملخص حالة السوق")
    signals.append("="*50)
    
    if buy_score > sell_score:
        dominant_trend = "🟢 صاعد (Bullish)"
        strength = "قوي" if buy_score >= 4 else "متوسط" if buy_score >= 2.5 else "ضعيف"
    elif sell_score > buy_score:
        dominant_trend = "🔴 هابط (Bearish)"
        strength = "قوي" if sell_score >= 4 else "متوسط" if sell_score >= 2.5 else "ضعيف"
    else:
        dominant_trend = "⚪ محايد (Neutral)"
        strength = "متساوي"
    
    signals.append(f"\n🎯 الاتجاه السائد: {dominant_trend}")
    signals.append(f"💪 قوة الاتجاه: {strength}")
    signals.append(f"🔰 مستوى الثقة: {confidence}")
    signals.append(f"📊 نقاط التقييم: شراء {buy_score:.1f} | بيع {sell_score:.1f}")
    signals.append(f"✅ التوصية النهائية: {final_recommendation}")
    
    signals.append(f"\n{'='*50}")
    signals.append(f"تم التحليل: {symbol} | الإطار الزمني: {interval}")
    signals.append(f"⏰ التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    signals.append(f"{'='*50}")
    
    levels = {
        "TP1": round(tp1, 5),
        "TP2": round(tp2, 5),
        "TP3": round(tp3, 5),
        "SL": round(sl, 5),
        "Entry Price": round(entry_price, 5),
        "Pivot Point": round(pp, 5) if pp else None,
        "Resistance 1": round(r1, 5) if r1 else None,
        "Resistance 2": round(r2, 5) if r2 else None,
        "Support 1": round(s1, 5) if s1 else None,
        "Support 2": round(s2, 5) if s2 else None,
        "Recommendation": final_recommendation,
        "Confidence": confidence
    }
    
    return signals, final_recommendation, levels, fib_levels

def perform_full_analysis(symbol, interval):
    """التحليل الكامل المتكامل"""
    from forex_analyzer import fetch_data, DataFetchError
    
    try:
        # Fetch data
        df = fetch_data(symbol, interval, outputsize=500)
        
        if len(df) < 50:
            return {
                'success': False,
                'error': 'بيانات غير كافية للتحليل. يلزم 50 شمعة على الأقل.'
            }
        
        # التأكد من وجود الأعمدة المطلوبة
        required_columns = ['Open', 'High', 'Low', 'Close', 'Date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                'success': False,
                'error': f'أعمدة مفقودة في البيانات: {", ".join(missing_columns)}. الأعمدة الموجودة: {", ".join(df.columns.tolist())}'
            }
        
        # Analyze with all indicators
        df = analyze_with_indicators(df)
        
        # Detect signals
        signals, recommendation, levels, fib_levels = detect_comprehensive_signals(df, symbol, interval)
        
        # Prepare chart data
        chart_df = df.tail(100)
        chart_data = {
            'dates': chart_df['Date'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
            'open': chart_df['Open'].tolist(),
            'high': chart_df['High'].tolist(),
            'low': chart_df['Low'].tolist(),
            'close': chart_df['Close'].tolist()
        }
        
        # Create detailed analysis text
        analysis_text = "\n".join(signals)
        
        return {
            'success': True,
            'signal': recommendation,
            'signals': signals,  # للتوافق مع الصفحة القديمة
            'signals_list': signals,  # للصفحة الجديدة
            'analysis_text': analysis_text,
            'entry_point': levels.get('Entry Price'),
            'take_profit1': levels.get('TP1'),
            'take_profit2': levels.get('TP2'),
            'take_profit3': levels.get('TP3'),
            'stop_loss': levels.get('SL'),
            'fibonacci_levels': fib_levels,
            'support': levels.get('Support 1'),
            'pivot': levels.get('Pivot Point'),
            'resistance': levels.get('Resistance 1'),
            'explanation': analysis_text,  # النص الكامل للشرح
            'chart_data': chart_data,
            'confidence': levels.get('Confidence', ''),
            'recommendation': recommendation
        }
        
    except DataFetchError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': f'خطأ في التحليل: {str(e)}'}

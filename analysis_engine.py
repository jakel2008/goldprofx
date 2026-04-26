"""
محرك التحليل الشامل
Comprehensive Analysis Engine
يستخدم جميع الاستراتيجيات المبرمجة لتحليل الأزواج
"""

import yfinance as yf
import pandas as pd
import ta
import numpy as np
from datetime import datetime
import json
from pathlib import Path
from recommendations_engine import ALL_AVAILABLE_PAIRS


class AnalysisEngine:
    """محرك التحليل الشامل - يحلل باستخدام جميع الاستراتيجيات"""
    
    def __init__(self, output_dir="analysis"):
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        # الاستراتيجيات المتاحة
        self.strategies = {
            'ict_smc': self.analyze_ict_smc,
            'rsi_macd': self.analyze_rsi_macd,
            'ema_crossover': self.analyze_ema_crossover,
            'bollinger_bands': self.analyze_bollinger_bands,
            'stochastic': self.analyze_stochastic,
            'fibonacci': self.analyze_fibonacci,
            'ichimoku': self.analyze_ichimoku,
            'pivot_points': self.analyze_pivot_points,
            'quant_statistical': self.analyze_quantitative_statistical,
            'digital_structure': self.analyze_digital_structure,
            'wolfwave': self.analyze_wolfwave,
            'astral_cycles': self.analyze_astral_cycles,
            'wyckoff': self.analyze_wyckoff,
        }
    
    def fetch_data(self, symbol, ticker, timeframe='1h', period='30d'):
        """جلب بيانات الزوج"""
        try:
            df = yf.download(ticker, interval=timeframe, period=period, progress=False)
            
            if df is None or df.empty:
                return None
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            column_mapping = {
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume'
            }
            df = df.rename(columns=column_mapping)
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].squeeze(), errors='coerce')
            
            df = df.dropna()
            return df.reset_index()
            
        except Exception as e:
            print(f"❌ خطأ في جلب بيانات {symbol}: {e}")
            return None
    
    def analyze_ict_smc(self, df):
        """استراتيجية ICT Smart Money Concepts"""
        if df is None or len(df) < 50:
            return {'signal': 'hold', 'confidence': 0, 'details': 'بيانات غير كافية'}
        
        # حساب Order Blocks
        high = df['high']
        low = df['low']
        close = df['close']
        
        # البحث عن Bullish Order Block
        bullish_ob = None
        for i in range(len(df) - 5, max(0, len(df) - 20), -1):
            if (close.iloc[i] < close.iloc[i-1] and 
                close.iloc[i+1] > close.iloc[i] and
                close.iloc[i+2] > close.iloc[i+1]):
                bullish_ob = {
                    'level': float(low.iloc[i]),
                    'strength': 'strong' if close.iloc[i+2] > close.iloc[i-1] else 'medium'
                }
                break
        
        # البحث عن Bearish Order Block
        bearish_ob = None
        for i in range(len(df) - 5, max(0, len(df) - 20), -1):
            if (close.iloc[i] > close.iloc[i-1] and 
                close.iloc[i+1] < close.iloc[i] and
                close.iloc[i+2] < close.iloc[i+1]):
                bearish_ob = {
                    'level': float(high.iloc[i]),
                    'strength': 'strong' if close.iloc[i+2] < close.iloc[i-1] else 'medium'
                }
                break
        
        current_price = float(close.iloc[-1])
        
        # تحديد الإشارة
        if bullish_ob and current_price <= bullish_ob['level'] * 1.002:
            signal = 'buy'
            confidence = 80 if bullish_ob['strength'] == 'strong' else 60
        elif bearish_ob and current_price >= bearish_ob['level'] * 0.998:
            signal = 'sell'
            confidence = 80 if bearish_ob['strength'] == 'strong' else 60
        else:
            signal = 'hold'
            confidence = 30
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'bullish_order_block': bullish_ob,
                'bearish_order_block': bearish_ob,
                'current_price': current_price
            }
        }
    
    def analyze_rsi_macd(self, df):
        """استراتيجية RSI + MACD"""
        if df is None or len(df) < 26:
            return {'signal': 'hold', 'confidence': 0}
        
        # حساب المؤشرات
        rsi = ta.momentum.rsi(df['close'], window=14)
        macd = ta.trend.MACD(df['close'])
        
        rsi_value = float(rsi.iloc[-1])
        macd_value = float(macd.macd().iloc[-1])
        macd_signal = float(macd.macd_signal().iloc[-1])
        macd_hist = macd_value - macd_signal
        
        # تحديد الإشارة
        if rsi_value < 30 and macd_hist > 0:
            signal = 'buy'
            confidence = 90 if rsi_value < 25 else 70
        elif rsi_value > 70 and macd_hist < 0:
            signal = 'sell'
            confidence = 90 if rsi_value > 75 else 70
        elif rsi_value < 40 and macd_hist > 0:
            signal = 'buy'
            confidence = 50
        elif rsi_value > 60 and macd_hist < 0:
            signal = 'sell'
            confidence = 50
        else:
            signal = 'hold'
            confidence = 30
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'rsi': round(rsi_value, 2),
                'macd': round(macd_value, 4),
                'macd_signal': round(macd_signal, 4),
                'macd_histogram': round(macd_hist, 4)
            }
        }
    
    def analyze_ema_crossover(self, df):
        """استراتيجية تقاطع المتوسطات المتحركة"""
        if df is None or len(df) < 50:
            return {'signal': 'hold', 'confidence': 0}
        
        # حساب EMAs
        ema_20 = ta.trend.ema_indicator(df['close'], window=20)
        ema_50 = ta.trend.ema_indicator(df['close'], window=50)
        
        ema_20_curr = float(ema_20.iloc[-1])
        ema_20_prev = float(ema_20.iloc[-2])
        ema_50_curr = float(ema_50.iloc[-1])
        ema_50_prev = float(ema_50.iloc[-2])
        
        # تقاطع صعودي
        if ema_20_prev < ema_50_prev and ema_20_curr > ema_50_curr:
            signal = 'buy'
            confidence = 85
        # تقاطع هبوطي
        elif ema_20_prev > ema_50_prev and ema_20_curr < ema_50_curr:
            signal = 'sell'
            confidence = 85
        # اتجاه صعودي قوي
        elif ema_20_curr > ema_50_curr and (ema_20_curr - ema_50_curr) > (ema_20_prev - ema_50_prev):
            signal = 'buy'
            confidence = 60
        # اتجاه هبوطي قوي
        elif ema_20_curr < ema_50_curr and (ema_50_curr - ema_20_curr) > (ema_50_prev - ema_20_prev):
            signal = 'sell'
            confidence = 60
        else:
            signal = 'hold'
            confidence = 30
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'ema_20': round(ema_20_curr, 5),
                'ema_50': round(ema_50_curr, 5),
                'distance': round(abs(ema_20_curr - ema_50_curr), 5)
            }
        }
    
    def analyze_bollinger_bands(self, df):
        """استراتيجية Bollinger Bands"""
        if df is None or len(df) < 20:
            return {'signal': 'hold', 'confidence': 0}
        
        # حساب Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        
        upper = float(bb.bollinger_hband().iloc[-1])
        lower = float(bb.bollinger_lband().iloc[-1])
        middle = float(bb.bollinger_mavg().iloc[-1])
        current = float(df['close'].iloc[-1])
        
        # النسبة من النطاق
        band_width = upper - lower
        position = (current - lower) / band_width if band_width > 0 else 0.5
        
        # تحديد الإشارة
        if position < 0.1:  # قريب من الحد السفلي
            signal = 'buy'
            confidence = 80
        elif position > 0.9:  # قريب من الحد العلوي
            signal = 'sell'
            confidence = 80
        elif position < 0.3:
            signal = 'buy'
            confidence = 50
        elif position > 0.7:
            signal = 'sell'
            confidence = 50
        else:
            signal = 'hold'
            confidence = 30
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'upper_band': round(upper, 5),
                'middle_band': round(middle, 5),
                'lower_band': round(lower, 5),
                'current_price': round(current, 5),
                'position_pct': round(position * 100, 1)
            }
        }
    
    def analyze_stochastic(self, df):
        """استراتيجية Stochastic Oscillator"""
        if df is None or len(df) < 14:
            return {'signal': 'hold', 'confidence': 0}
        
        # حساب Stochastic
        stoch = ta.momentum.StochasticOscillator(
            df['high'], df['low'], df['close'], 
            window=14, smooth_window=3
        )
        
        k = float(stoch.stoch().iloc[-1])
        d = float(stoch.stoch_signal().iloc[-1])
        
        # تحديد الإشارة
        if k < 20 and k > d:
            signal = 'buy'
            confidence = 85
        elif k > 80 and k < d:
            signal = 'sell'
            confidence = 85
        elif k < 30:
            signal = 'buy'
            confidence = 50
        elif k > 70:
            signal = 'sell'
            confidence = 50
        else:
            signal = 'hold'
            confidence = 30
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'stoch_k': round(k, 2),
                'stoch_d': round(d, 2)
            }
        }
    
    def analyze_fibonacci(self, df):
        """تحليل مستويات فيبوناتشي"""
        if df is None or len(df) < 30:
            return {'signal': 'hold', 'confidence': 0}
        
        # إيجاد أعلى وأدنى نقطة في آخر 30 شمعة
        high_30 = float(df['high'].tail(30).max())
        low_30 = float(df['low'].tail(30).min())
        current = float(df['close'].iloc[-1])
        
        # حساب مستويات فيبوناتشي
        diff = high_30 - low_30
        levels = {
            '0.0': high_30,
            '0.236': high_30 - (diff * 0.236),
            '0.382': high_30 - (diff * 0.382),
            '0.5': high_30 - (diff * 0.5),
            '0.618': high_30 - (diff * 0.618),
            '0.786': high_30 - (diff * 0.786),
            '1.0': low_30
        }
        
        # تحديد القرب من المستويات
        tolerance = diff * 0.02  # 2% من المدى
        
        signal = 'hold'
        confidence = 30
        
        # شراء عند مستويات الدعم
        if abs(current - levels['0.618']) < tolerance or abs(current - levels['0.786']) < tolerance:
            signal = 'buy'
            confidence = 75
        elif abs(current - levels['0.5']) < tolerance:
            signal = 'buy'
            confidence = 60
        # بيع عند مستويات المقاومة
        elif abs(current - levels['0.236']) < tolerance or abs(current - levels['0.382']) < tolerance:
            signal = 'sell'
            confidence = 75
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'fib_levels': {k: round(v, 5) for k, v in levels.items()},
                'current_price': round(current, 5)
            }
        }
    
    def analyze_ichimoku(self, df):
        """استراتيجية Ichimoku Cloud"""
        if df is None or len(df) < 52:
            return {'signal': 'hold', 'confidence': 0}
        
        # حساب Ichimoku
        ichimoku = ta.trend.IchimokuIndicator(df['high'], df['low'], window1=9, window2=26, window3=52)
        
        tenkan = float(ichimoku.ichimoku_conversion_line().iloc[-1])
        kijun = float(ichimoku.ichimoku_base_line().iloc[-1])
        senkou_a = float(ichimoku.ichimoku_a().iloc[-1])
        senkou_b = float(ichimoku.ichimoku_b().iloc[-1])
        current = float(df['close'].iloc[-1])
        
        # تحديد الإشارة
        if current > senkou_a and current > senkou_b and tenkan > kijun:
            signal = 'buy'
            confidence = 85
        elif current < senkou_a and current < senkou_b and tenkan < kijun:
            signal = 'sell'
            confidence = 85
        elif tenkan > kijun:
            signal = 'buy'
            confidence = 50
        elif tenkan < kijun:
            signal = 'sell'
            confidence = 50
        else:
            signal = 'hold'
            confidence = 30
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'tenkan_sen': round(tenkan, 5),
                'kijun_sen': round(kijun, 5),
                'senkou_span_a': round(senkou_a, 5),
                'senkou_span_b': round(senkou_b, 5),
                'current_price': round(current, 5)
            }
        }
    
    def analyze_pivot_points(self, df):
        """تحليل نقاط البايفوت"""
        if df is None or len(df) < 1:
            return {'signal': 'hold', 'confidence': 0}
        
        # حساب نقاط البايفوت من اليوم السابق
        high = float(df['high'].iloc[-1])
        low = float(df['low'].iloc[-1])
        close = float(df['close'].iloc[-1])
        
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        current = close
        
        # تحديد الإشارة بناءً على الموقع
        if current < s1 and current > s2:
            signal = 'buy'
            confidence = 70
        elif current < s2:
            signal = 'buy'
            confidence = 85
        elif current > r1 and current < r2:
            signal = 'sell'
            confidence = 70
        elif current > r2:
            signal = 'sell'
            confidence = 85
        else:
            signal = 'hold'
            confidence = 40
        
        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'pivot': round(pivot, 5),
                'resistance_1': round(r1, 5),
                'resistance_2': round(r2, 5),
                'resistance_3': round(r3, 5),
                'support_1': round(s1, 5),
                'support_2': round(s2, 5),
                'support_3': round(s3, 5),
                'current_price': round(current, 5)
            }
        }

    def analyze_quantitative_statistical(self, df):
        """المدرسة الكمية والإحصائية"""
        if df is None or len(df) < 60:
            return {'signal': 'hold', 'confidence': 0, 'details': 'بيانات غير كافية'}

        close = df['close'].astype(float)
        returns = np.log(close / close.shift(1)).dropna()
        if len(returns) < 40:
            return {'signal': 'hold', 'confidence': 0, 'details': 'عوائد غير كافية'}

        rolling_mean = close.rolling(20).mean()
        rolling_std = close.rolling(20).std()
        mean_value = float(rolling_mean.iloc[-1])
        std_value = float(rolling_std.iloc[-1]) if not pd.isna(rolling_std.iloc[-1]) else 0.0
        current = float(close.iloc[-1])
        z_score = (current - mean_value) / std_value if std_value > 0 else 0.0

        recent_close = close.tail(20).reset_index(drop=True)
        x_axis = np.arange(len(recent_close), dtype=float)
        slope = float(np.polyfit(x_axis, recent_close, 1)[0]) if len(recent_close) >= 2 else 0.0
        correlation = float(np.corrcoef(x_axis, recent_close)[0, 1]) if len(recent_close) >= 2 else 0.0
        trend_fit = abs(correlation) if not np.isnan(correlation) else 0.0

        vol_short = float(returns.tail(10).std()) if len(returns) >= 10 else 0.0
        vol_long = float(returns.tail(30).std()) if len(returns) >= 30 else 0.0
        volatility_ratio = vol_short / vol_long if vol_long > 0 else 1.0
        momentum_10 = ((current / float(close.iloc[-11])) - 1.0) * 100 if len(close) > 10 else 0.0

        signal = 'hold'
        confidence = 30
        regime = 'neutral'

        if z_score <= -1.8:
            signal = 'buy'
            confidence = 84
            regime = 'mean_reversion_buy'
        elif z_score >= 1.8:
            signal = 'sell'
            confidence = 84
            regime = 'mean_reversion_sell'
        elif slope > 0 and trend_fit >= 0.65 and momentum_10 > 0 and volatility_ratio <= 1.35:
            signal = 'buy'
            confidence = 72
            regime = 'trend_following_buy'
        elif slope < 0 and trend_fit >= 0.65 and momentum_10 < 0 and volatility_ratio <= 1.35:
            signal = 'sell'
            confidence = 72
            regime = 'trend_following_sell'

        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'regime': regime,
                'z_score_20': round(z_score, 3),
                'trend_slope_20': round(slope, 6),
                'trend_fit': round(trend_fit, 3),
                'momentum_10_pct': round(momentum_10, 3),
                'volatility_ratio': round(volatility_ratio, 3),
            }
        }

    def analyze_digital_structure(self, df):
        """المدرسة الرقمية عبر ترميز بنية الشموع والزخم"""
        if df is None or len(df) < 20:
            return {'signal': 'hold', 'confidence': 0, 'details': 'بيانات غير كافية'}

        recent = df.tail(8).copy()
        direction_bits = [1 if close_value > open_value else 0 for open_value, close_value in zip(recent['open'], recent['close'])]
        binary_bias = sum(1 if bit == 1 else -1 for bit in direction_bits)

        max_run = 1
        current_run = 1
        for index in range(1, len(direction_bits)):
            if direction_bits[index] == direction_bits[index - 1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        compression_ratio = max_run / len(direction_bits) if direction_bits else 0.0

        range_high = float(df['high'].tail(14).max())
        range_low = float(df['low'].tail(14).min())
        current = float(df['close'].iloc[-1])
        range_span = range_high - range_low
        close_location_value = ((current - range_low) / range_span) if range_span > 0 else 0.5

        signal = 'hold'
        confidence = 30

        if binary_bias >= 4 and compression_ratio >= 0.5 and close_location_value > 0.65:
            signal = 'buy'
            confidence = 74
        elif binary_bias <= -4 and compression_ratio >= 0.5 and close_location_value < 0.35:
            signal = 'sell'
            confidence = 74
        elif binary_bias >= 2 and close_location_value > 0.58:
            signal = 'buy'
            confidence = 55
        elif binary_bias <= -2 and close_location_value < 0.42:
            signal = 'sell'
            confidence = 55

        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'direction_bits': ''.join(str(bit) for bit in direction_bits),
                'binary_bias': binary_bias,
                'compression_ratio': round(compression_ratio, 3),
                'close_location_value': round(close_location_value, 3),
            }
        }

    def _extract_alternating_pivots(self, df, lookback=60, window=2):
        """استخراج آخر 5 قمم/قيعان متناوبة لاكتشاف النماذج الموجية."""
        sample = df.tail(lookback).reset_index(drop=True)
        pivots = []

        for index in range(window, len(sample) - window):
            high_slice = sample['high'].iloc[index - window:index + window + 1]
            low_slice = sample['low'].iloc[index - window:index + window + 1]

            high_value = float(sample['high'].iloc[index])
            low_value = float(sample['low'].iloc[index])

            if high_value == float(high_slice.max()):
                pivots.append({'idx': index, 'type': 'high', 'price': high_value})
            if low_value == float(low_slice.min()):
                pivots.append({'idx': index, 'type': 'low', 'price': low_value})

        pivots.sort(key=lambda item: item['idx'])
        filtered = []
        for pivot in pivots:
            if not filtered:
                filtered.append(pivot)
                continue

            previous = filtered[-1]
            if previous['idx'] == pivot['idx']:
                if pivot['type'] == 'high' and previous['type'] == 'low':
                    filtered[-1] = pivot
                continue

            if previous['type'] == pivot['type']:
                if pivot['type'] == 'high' and pivot['price'] >= previous['price']:
                    filtered[-1] = pivot
                elif pivot['type'] == 'low' and pivot['price'] <= previous['price']:
                    filtered[-1] = pivot
                continue

            filtered.append(pivot)

        return filtered[-5:] if len(filtered) >= 5 else []

    def analyze_wolfwave(self, df):
        """مدرسة Wolfwave / Wolfe Wave بشكل هندسي مبسط"""
        if df is None or len(df) < 40:
            return {'signal': 'hold', 'confidence': 0, 'details': 'بيانات غير كافية'}

        pivots = self._extract_alternating_pivots(df)
        if len(pivots) < 5:
            return {'signal': 'hold', 'confidence': 25, 'details': 'لا توجد نقاط موجية كافية'}

        p1, p2, p3, p4, p5 = pivots
        sequence = [point['type'] for point in pivots]
        signal = 'hold'
        confidence = 30
        pattern = 'none'

        denominator = max(1, p3['idx'] - p1['idx'])
        slope_13 = (p3['price'] - p1['price']) / denominator
        projected_p5 = p1['price'] + slope_13 * (p5['idx'] - p1['idx'])
        alignment_error = abs(p5['price'] - projected_p5) / max(abs(projected_p5), 1e-9)

        if sequence == ['low', 'high', 'low', 'high', 'low']:
            if p3['price'] < p1['price'] and p4['price'] < p2['price'] and p5['price'] <= p3['price'] * 1.01 and alignment_error <= 0.03:
                signal = 'buy'
                confidence = 78
                pattern = 'bullish_wolfwave'
        elif sequence == ['high', 'low', 'high', 'low', 'high']:
            if p3['price'] > p1['price'] and p4['price'] > p2['price'] and p5['price'] >= p3['price'] * 0.99 and alignment_error <= 0.03:
                signal = 'sell'
                confidence = 78
                pattern = 'bearish_wolfwave'

        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'pattern': pattern,
                'pivot_sequence': sequence,
                'alignment_error': round(alignment_error, 4),
                'pivots': [{
                    'type': point['type'],
                    'index': point['idx'],
                    'price': round(point['price'], 5)
                } for point in pivots],
            }
        }

    def _extract_analysis_timestamp(self, df):
        """استخراج آخر وقت من إطار البيانات إن وجد."""
        for column in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[column]):
                return pd.to_datetime(df[column].iloc[-1]).to_pydatetime()

        datetime_columns = [column for column in df.columns if 'date' in str(column).lower() or 'time' in str(column).lower()]
        for column in datetime_columns:
            try:
                return pd.to_datetime(df[column].iloc[-1]).to_pydatetime()
            except Exception:
                continue

        return datetime.utcnow()

    def analyze_astral_cycles(self, df):
        """المدرسة الفلكية الزمنية كعامل دوري مساعد منخفض الوزن"""
        if df is None or len(df) < 30:
            return {'signal': 'hold', 'confidence': 0, 'details': 'بيانات غير كافية'}

        timestamp = self._extract_analysis_timestamp(df)
        current = float(df['close'].iloc[-1])
        range_high = float(df['high'].tail(20).max())
        range_low = float(df['low'].tail(20).min())
        range_span = range_high - range_low
        range_position = ((current - range_low) / range_span) if range_span > 0 else 0.5

        lunar_origin = datetime(2000, 1, 6)
        lunar_days = (timestamp - lunar_origin).total_seconds() / 86400.0
        lunar_phase = (lunar_days % 29.53058867) / 29.53058867
        day_of_year = timestamp.timetuple().tm_yday
        solar_phase = day_of_year / 365.2425

        signal = 'hold'
        confidence = 25
        cycle_state = 'neutral'

        if (lunar_phase <= 0.12 or lunar_phase >= 0.88) and range_position < 0.30:
            signal = 'buy'
            confidence = 58
            cycle_state = 'new_moon_reversal_window'
        elif 0.38 <= lunar_phase <= 0.62 and range_position > 0.70:
            signal = 'sell'
            confidence = 58
            cycle_state = 'full_moon_reversal_window'
        elif timestamp.weekday() in (1, 2) and range_position < 0.40:
            signal = 'buy'
            confidence = 42
            cycle_state = 'midweek_recovery_bias'
        elif timestamp.weekday() in (3, 4) and range_position > 0.60:
            signal = 'sell'
            confidence = 42
            cycle_state = 'lateweek_distribution_bias'

        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'cycle_state': cycle_state,
                'timestamp': timestamp.isoformat(),
                'lunar_phase_pct': round(lunar_phase * 100, 2),
                'solar_phase_pct': round(solar_phase * 100, 2),
                'range_position_pct': round(range_position * 100, 2),
            }
        }

    def analyze_wyckoff(self, df):
        """نظرية وايكوف: التجميع/التصريف والـ Spring / Upthrust"""
        if df is None or len(df) < 40:
            return {'signal': 'hold', 'confidence': 0, 'details': 'بيانات غير كافية'}

        recent = df.tail(40).copy()
        current_close = float(recent['close'].iloc[-1])
        current_high = float(recent['high'].iloc[-1])
        current_low = float(recent['low'].iloc[-1])
        current_open = float(recent['open'].iloc[-1])

        volume_series = pd.to_numeric(recent['volume'], errors='coerce').fillna(0.0)
        avg_volume = float(volume_series.tail(20).mean()) if len(volume_series) >= 20 else 0.0
        current_volume = float(volume_series.iloc[-1])

        range_high = float(recent['high'].max())
        range_low = float(recent['low'].min())
        range_span = range_high - range_low
        range_position = ((current_close - range_low) / range_span) if range_span > 0 else 0.5

        prior_high = float(recent['high'].iloc[-15:-1].max()) if len(recent) >= 16 else range_high
        prior_low = float(recent['low'].iloc[-15:-1].min()) if len(recent) >= 16 else range_low
        candle_span = max(current_high - current_low, 1e-9)
        close_location = (current_close - current_low) / candle_span

        spring = current_low < prior_low and current_close > prior_low and close_location > 0.60 and current_volume > avg_volume * 1.10
        upthrust = current_high > prior_high and current_close < prior_high and close_location < 0.40 and current_volume > avg_volume * 1.10
        accumulation = range_position < 0.35 and current_close > current_open and current_volume <= max(avg_volume * 1.05, current_volume)
        distribution = range_position > 0.65 and current_close < current_open and current_volume <= max(avg_volume * 1.05, current_volume)

        signal = 'hold'
        confidence = 30
        structure = 'neutral'

        if spring:
            signal = 'buy'
            confidence = 86
            structure = 'spring'
        elif upthrust:
            signal = 'sell'
            confidence = 86
            structure = 'upthrust'
        elif accumulation:
            signal = 'buy'
            confidence = 64
            structure = 'accumulation'
        elif distribution:
            signal = 'sell'
            confidence = 64
            structure = 'distribution'

        return {
            'signal': signal,
            'confidence': confidence,
            'details': {
                'structure': structure,
                'range_position_pct': round(range_position * 100, 2),
                'close_location_pct': round(close_location * 100, 2),
                'current_volume': round(current_volume, 2),
                'average_volume_20': round(avg_volume, 2),
                'spring': spring,
                'upthrust': upthrust,
            }
        }
    
    def analyze_symbol(self, symbol, ticker, timeframe='1h'):
        """تحليل شامل لزوج معين باستخدام جميع الاستراتيجيات"""
        print(f"\n{'='*60}")
        print(f"📊 تحليل شامل: {symbol} | {timeframe}")
        print(f"{'='*60}")
        
        # جلب البيانات
        df = self.fetch_data(symbol, ticker, timeframe)
        if df is None:
            return None
        
        # تحليل باستخدام جميع الاستراتيجيات
        results = {}
        for strategy_name, strategy_func in self.strategies.items():
            print(f"  🔍 {strategy_name}...", end=" ")
            try:
                result = strategy_func(df)
                results[strategy_name] = result
                print(f"{result['signal'].upper()} ({result['confidence']}%)")
            except Exception as e:
                print(f"❌ خطأ: {e}")
                results[strategy_name] = {'signal': 'hold', 'confidence': 0, 'error': str(e)}
        
        # تجميع النتائج
        buy_votes = sum(1 for r in results.values() if r['signal'] == 'buy')
        sell_votes = sum(1 for r in results.values() if r['signal'] == 'sell')
        total_votes = len(results)
        
        # الإجماع
        if buy_votes > sell_votes and buy_votes / total_votes >= 0.5:
            consensus = 'buy'
            consensus_strength = (buy_votes / total_votes) * 100
        elif sell_votes > buy_votes and sell_votes / total_votes >= 0.5:
            consensus = 'sell'
            consensus_strength = (sell_votes / total_votes) * 100
        else:
            consensus = 'hold'
            consensus_strength = 30
        
        # حساب متوسط الثقة
        avg_confidence = sum(r['confidence'] for r in results.values()) / len(results)
        
        analysis = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'current_price': float(df['close'].iloc[-1]),
            'strategies_results': results,
            'consensus': {
                'signal': consensus,
                'strength': round(consensus_strength, 1),
                'buy_votes': buy_votes,
                'sell_votes': sell_votes,
                'total_strategies': total_votes
            },
            'average_confidence': round(avg_confidence, 1)
        }
        
        # حفظ التحليل
        self.save_analysis(analysis)
        
        return analysis
    
    def save_analysis(self, analysis):
        """حفظ التحليل"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.output_dir / f"analysis_{analysis['symbol']}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 تم حفظ التحليل: {filename}")
    
    def print_analysis_summary(self, analysis):
        """طباعة ملخص التحليل"""
        print(f"\n{'='*60}")
        print(f"📊 ملخص التحليل: {analysis['symbol']}")
        print(f"{'='*60}")
        print(f"💵 السعر الحالي: {analysis['current_price']}")
        print(f"\n🎯 الإجماع: {analysis['consensus']['signal'].upper()}")
        print(f"💪 القوة: {analysis['consensus']['strength']}%")
        print(f"📊 التصويت: {analysis['consensus']['buy_votes']} شراء | {analysis['consensus']['sell_votes']} بيع")
        print(f"⭐ متوسط الثقة: {analysis['average_confidence']}%")
        
        print(f"\n📋 نتائج الاستراتيجيات:")
        for strategy, result in analysis['strategies_results'].items():
            emoji = "📈" if result['signal'] == 'buy' else "📉" if result['signal'] == 'sell' else "➡️"
            print(f"  {emoji} {strategy}: {result['signal'].upper()} ({result['confidence']}%)")
        
        print(f"{'='*60}\n")


def interactive_analysis():
    """وضع التحليل التفاعلي"""
    engine = AnalysisEngine()
    
    print("\n" + "="*60)
    print("🔍 محرك التحليل الشامل")
    print("="*60 + "\n")
    
    # عرض الفئات
    print("📂 الفئات المتاحة:")
    categories = list(ALL_AVAILABLE_PAIRS.keys())
    for i, category in enumerate(categories, 1):
        pairs_count = len(ALL_AVAILABLE_PAIRS[category])
        print(f"  {i}. {category}: {pairs_count} زوج")
    
    print("\n0. إدخال رمز مخصص")
    print("\nاختر الفئة:")
    choice = input("> ").strip()
    
    try:
        choice_num = int(choice)
        if choice_num == 0:
            # إدخال مخصص
            print("\nأدخل رمز الزوج (مثال: EURUSD):")
            symbol = input("> ").strip().upper()
            print("أدخل رمز Yahoo Finance (مثال: EURUSD=X):")
            ticker = input("> ").strip()
        else:
            # اختيار من الفئة
            category = categories[choice_num - 1]
            pairs = ALL_AVAILABLE_PAIRS[category]
            
            print(f"\n📊 أزواج {category}:")
            pairs_list = list(pairs.items())
            for i, (symbol, ticker) in enumerate(pairs_list, 1):
                print(f"  {i}. {symbol}")
            
            print("\nاختر الزوج:")
            pair_choice = int(input("> ").strip())
            symbol, ticker = pairs_list[pair_choice - 1]
    except:
        print("❌ إدخال غير صحيح")
        return
    
    # اختيار الإطار الزمني
    print("\n⏰ الإطار الزمني:")
    print("  1. 5 دقائق (5m)")
    print("  2. 15 دقيقة (15m)")
    print("  3. 1 ساعة (1h)")
    print("  4. 4 ساعات (4h)")
    print("  5. يومي (1d)")
    
    timeframes = ['5m', '15m', '1h', '4h', '1d']
    tf_choice = input("> ").strip()
    try:
        timeframe = timeframes[int(tf_choice) - 1]
    except:
        timeframe = '1h'
    
    # تشغيل التحليل
    print(f"\n🚀 جاري تحليل {symbol} على إطار {timeframe}...")
    analysis = engine.analyze_symbol(symbol, ticker, timeframe)
    
    if analysis:
        engine.print_analysis_summary(analysis)
    else:
        print("❌ فشل التحليل")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # تحليل زوج محدد من command line
        symbol = sys.argv[1]
        timeframe = sys.argv[2] if len(sys.argv) > 2 else '1h'
        
        # البحث عن الزوج
        all_pairs = {}
        for category in ALL_AVAILABLE_PAIRS.values():
            all_pairs.update(category)
        
        if symbol.upper() in all_pairs:
            engine = AnalysisEngine()
            ticker = all_pairs[symbol.upper()]
            analysis = engine.analyze_symbol(symbol.upper(), ticker, timeframe)
            if analysis:
                engine.print_analysis_summary(analysis)
        else:
            print(f"❌ الزوج {symbol} غير موجود")
    else:
        # الوضع التفاعلي
        interactive_analysis()

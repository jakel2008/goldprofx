# -*- coding: utf-8 -*-
"""
محرك التحليل المتقدم مع AI
Advanced Analysis Engine with AI-Enhanced Signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from ta import trend, momentum, volatility, volume
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

class AdvancedSignalEngine:
    """محرك إشارات متقدم مع تعلم آلي"""
    
    def __init__(self):
        self.min_quality_score = 75  # حد أدنى لجودة الإشارة
        self.confidence_threshold = 0.7  # عتبة الثقة
        
    def fetch_data(self, symbol, period='1mo', interval='1h'):
        """جلب البيانات مع معالجة الأخطاء"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return None
            
            # توحيد أسماء الأعمدة
            df.columns = [col.lower() for col in df.columns]
            return df
            
        except Exception as e:
            print(f"خطأ في جلب {symbol}: {e}")
            return None
    
    def calculate_advanced_indicators(self, df):
        """حساب مؤشرات فنية متقدمة"""
        try:
            # المتوسطات المتحركة
            df['ema_9'] = trend.EMAIndicator(df['close'], window=9).ema_indicator()
            df['ema_21'] = trend.EMAIndicator(df['close'], window=21).ema_indicator()
            df['ema_50'] = trend.EMAIndicator(df['close'], window=50).ema_indicator()
            df['ema_200'] = trend.EMAIndicator(df['close'], window=200).ema_indicator()
            
            # MACD متقدم
            macd = trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # RSI متعدد الفترات
            df['rsi_14'] = momentum.RSIIndicator(df['close'], window=14).rsi()
            df['rsi_7'] = momentum.RSIIndicator(df['close'], window=7).rsi()
            df['rsi_21'] = momentum.RSIIndicator(df['close'], window=21).rsi()
            
            # Stochastic RSI
            stoch_rsi = momentum.StochRSIIndicator(df['close'])
            df['stoch_rsi_k'] = stoch_rsi.stochrsi_k()
            df['stoch_rsi_d'] = stoch_rsi.stochrsi_d()
            
            # Bollinger Bands
            bollinger = volatility.BollingerBands(df['close'])
            df['bb_upper'] = bollinger.bollinger_hband()
            df['bb_middle'] = bollinger.bollinger_mavg()
            df['bb_lower'] = bollinger.bollinger_lband()
            df['bb_width'] = bollinger.bollinger_wband()
            
            # ATR متقدم
            df['atr'] = volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            
            # ADX (قوة الاتجاه)
            adx = trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Momentum
            df['momentum'] = df['close'].pct_change(periods=10) * 100
            
            # Support & Resistance
            df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
            df['support_1'] = 2 * df['pivot'] - df['high']
            df['resistance_1'] = 2 * df['pivot'] - df['low']
            
            return df
            
        except Exception as e:
            print(f"خطأ في حساب المؤشرات: {e}")
            return None
    
    def multi_timeframe_analysis(self, symbol):
        """تحليل متعدد الأطر الزمنية"""
        timeframes = {
            '15m': {'period': '5d', 'weight': 0.2},
            '1h': {'period': '1mo', 'weight': 0.3},
            '4h': {'period': '3mo', 'weight': 0.5}
        }
        
        signals = {}
        total_weight = 0
        weighted_score = 0
        
        for tf, config in timeframes.items():
            df = self.fetch_data(symbol, period=config['period'], interval=tf)
            if df is None:
                continue
                
            df = self.calculate_advanced_indicators(df)
            if df is None:
                continue
            
            # تحليل الإطار الزمني
            signal = self.analyze_timeframe(df, tf)
            if signal:
                signals[tf] = signal
                score = signal.get('score', 0)
                weighted_score += score * config['weight']
                total_weight += config['weight']
        
        if total_weight > 0:
            avg_score = weighted_score / total_weight
            return {'signals': signals, 'combined_score': avg_score}
        
        return None
    
    def analyze_timeframe(self, df, timeframe):
        """تحليل إطار زمني واحد"""
        if df is None or len(df) < 50:
            return None
        
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            score = 0
            signals = []
            direction = 'neutral'
            
            # 1. تحليل الاتجاه (30 نقطة)
            if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                score += 30
                signals.append("اتجاه صاعد قوي")
                direction = 'bullish'
            elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                score += 30
                signals.append("اتجاه هابط قوي")
                direction = 'bearish'
            
            # 2. قوة الاتجاه ADX (20 نقطة)
            if latest['adx'] > 25:
                score += 20
                signals.append(f"اتجاه قوي ADX={latest['adx']:.1f}")
            elif latest['adx'] > 20:
                score += 10
            
            # 3. MACD (15 نقطة)
            if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                score += 15
                signals.append("MACD صاعد (تقاطع)")
            elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                score += 15
                signals.append("MACD هابط (تقاطع)")
            
            # 4. RSI (15 نقطة)
            if 30 < latest['rsi_14'] < 40 and direction == 'bullish':
                score += 15
                signals.append("RSI oversold + اتجاه صاعد")
            elif 60 < latest['rsi_14'] < 70 and direction == 'bearish':
                score += 15
                signals.append("RSI overbought + اتجاه هابط")
            
            # 5. Bollinger Bands (10 نقطة)
            if latest['close'] < latest['bb_lower'] and direction == 'bullish':
                score += 10
                signals.append("السعر تحت BB السفلي")
            elif latest['close'] > latest['bb_upper'] and direction == 'bearish':
                score += 10
                signals.append("السعر فوق BB العلوي")
            
            # 6. حجم التداول (10 نقطة)
            if latest['volume_ratio'] > 1.5:
                score += 10
                signals.append("حجم تداول مرتفع")
            
            return {
                'timeframe': timeframe,
                'score': score,
                'direction': direction,
                'signals': signals,
                'price': latest['close'],
                'rsi': latest['rsi_14'],
                'adx': latest['adx'],
                'atr': latest['atr']
            }
            
        except Exception as e:
            print(f"خطأ في تحليل {timeframe}: {e}")
            return None
    
    def calculate_smart_levels(self, df, direction):
        """حساب مستويات ذكية للدخول والخروج"""
        try:
            latest = df.iloc[-1]
            atr = latest['atr']
            close = latest['close']
            
            if direction == 'buy':
                # دخول: عند الدعم أو السعر الحالي
                entry = min(close, latest['support_1'])
                
                # SL: تحت الدعم بـ 1.5 ATR
                stop_loss = entry - (atr * 1.5)
                
                # TPs: بنسب فيبوناتشي
                tp1 = entry + (atr * 2.0)   # 1:1.33 R:R
                tp2 = entry + (atr * 3.5)   # 1:2.33 R:R
                tp3 = entry + (atr * 5.0)   # 1:3.33 R:R
                
            else:  # sell
                # دخول: عند المقاومة أو السعر الحالي
                entry = max(close, latest['resistance_1'])
                
                # SL: فوق المقاومة بـ 1.5 ATR
                stop_loss = entry + (atr * 1.5)
                
                # TPs: بنسب فيبوناتشي
                tp1 = entry - (atr * 2.0)
                tp2 = entry - (atr * 3.5)
                tp3 = entry - (atr * 5.0)
            
            # حساب R:R Ratio
            risk = abs(entry - stop_loss)
            reward = abs(entry - tp1)
            rr_ratio = reward / risk if risk > 0 else 0
            
            return {
                'entry': entry,
                'stop_loss': stop_loss,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'rr_ratio': rr_ratio,
                'risk_pips': risk,
                'reward_pips': reward
            }
            
        except Exception as e:
            print(f"خطأ في حساب المستويات: {e}")
            return None
    
    def generate_signal(self, symbol, yf_symbol):
        """إنشاء إشارة متقدمة"""
        try:
            # تحليل متعدد الأطر
            mtf_analysis = self.multi_timeframe_analysis(yf_symbol)
            if not mtf_analysis:
                return None
            
            combined_score = mtf_analysis['combined_score']
            
            # فلترة: رفض الإشارات الضعيفة
            if combined_score < self.min_quality_score:
                return None
            
            # تحديد الاتجاه
            signals = mtf_analysis['signals']
            directions = [s['direction'] for s in signals.values()]
            
            if directions.count('bullish') > directions.count('bearish'):
                direction = 'buy'
            elif directions.count('bearish') > directions.count('bullish'):
                direction = 'sell'
            else:
                return None  # لا إجماع
            
            # جلب آخر بيانات للمستويات
            df = self.fetch_data(yf_symbol, period='1mo', interval='1h')
            df = self.calculate_advanced_indicators(df)
            
            if df is None:
                return None
            
            # حساب المستويات
            levels = self.calculate_smart_levels(df, direction)
            if not levels or levels['rr_ratio'] < 1.5:
                return None  # R:R غير مقبول
            
            # بناء الإشارة النهائية
            signal = {
                'symbol': symbol,
                'yf_symbol': yf_symbol,
                'direction': direction,
                'quality_score': int(combined_score),
                'confidence': min(combined_score / 100, 1.0),
                'entry': levels['entry'],
                'stop_loss': levels['stop_loss'],
                'tp1': levels['tp1'],
                'tp2': levels['tp2'],
                'tp3': levels['tp3'],
                'rr_ratio': levels['rr_ratio'],
                'timeframes': signals,
                'timestamp': datetime.now()
            }
            
            return signal
            
        except Exception as e:
            print(f"خطأ في إنشاء إشارة {symbol}: {e}")
            return None
    
    def format_signal_message(self, signal):
        """تنسيق رسالة الإشارة"""
        direction_emoji = "🔼" if signal['direction'] == 'buy' else "🔽"
        direction_text = "شراء" if signal['direction'] == 'buy' else "بيع"
        
        # حساب نسب الأهداف
        entry = signal['entry']
        tp1_pct = abs((signal['tp1'] - entry) / entry * 100)
        tp2_pct = abs((signal['tp2'] - entry) / entry * 100)
        tp3_pct = abs((signal['tp3'] - entry) / entry * 100)
        
        message = f"""
{'='*50}
🚨 <b>إشارة تداول متقدمة</b> 🚨
{'='*50}

📊 <b>الزوج:</b> {signal['symbol']}
💎 <b>جودة الإشارة:</b> {signal['quality_score']}/100
🎯 <b>مستوى الثقة:</b> {signal['confidence']*100:.0f}%

{direction_emoji} <b>الاتجاه: {direction_text}</b> {direction_emoji}

{'─'*50}
<b>📍 خطة التداول المحسّنة:</b>

🟢 <b>نقطة الدخول:</b> {signal['entry']:.5f}

🔴 <b>وقف الخسارة:</b> {signal['stop_loss']:.5f}

💚 <b>أهداف الربح (مُحسّنة):</b>
   🎯 TP1: {signal['tp1']:.5f} (+{tp1_pct:.2f}%)
   🎯 TP2: {signal['tp2']:.5f} (+{tp2_pct:.2f}%)
   🎯 TP3: {signal['tp3']:.5f} (+{tp3_pct:.2f}%)

⚖️ <b>R:R Ratio:</b> 1:{signal['rr_ratio']:.2f}

{'─'*50}
<b>📈 التحليل متعدد الأطر:</b>
"""
        
        for tf, data in signal['timeframes'].items():
            message += f"\n   {tf}: {data['score']}/100 - {data['direction']}"
        
        message += f"\n\n{'─'*50}"
        message += f"\n💡 <b>نصيحة:</b> أغلق 30% عند TP1 وانقل SL للتعادل"
        message += f"\n🕐 <b>الوقت:</b> {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        message += f"\n{'='*50}"
        
        return message


if __name__ == "__main__":
    print("🧠 محرك التحليل المتقدم بالذكاء الاصطناعي")
    print("=" * 60)
    
    engine = AdvancedSignalEngine()
    
    # اختبار على البتكوين
    signal = engine.generate_signal('BTCUSD', 'BTC-USD')
    
    if signal:
        print("\n✅ تم إنشاء إشارة:")
        print(engine.format_signal_message(signal))
    else:
        print("\n❌ لا توجد إشارة قوية حالياً")

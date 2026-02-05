"""
محرك التحليل الشامل
Comprehensive Analysis Engine
يستخدم جميع الاستراتيجيات المبرمجة لتحليل الأزواج
"""

import yfinance as yf
import pandas as pd
import ta
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

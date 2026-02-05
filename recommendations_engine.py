"""
محرك التوصيات المتقدم
Advanced Recommendations Engine
يركز على أفضل نقاط الدخول ووقف الخسارة وأهداف الربح
"""

import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import json
from pathlib import Path

# قائمة شاملة لجميع الأزواج والأصول المتاحة
ALL_AVAILABLE_PAIRS = {
    # أزواج الفوركس الرئيسية
    'forex_major': {
        'EURUSD': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'USDJPY': 'USDJPY=X',
        'USDCHF': 'USDCHF=X',
        'AUDUSD': 'AUDUSD=X',
        'USDCAD': 'USDCAD=X',
        'NZDUSD': 'NZDUSD=X',
    },
    
    # أزواج الفوركس الثانوية
    'forex_minor': {
        'EURGBP': 'EURGBP=X',
        'EURJPY': 'EURJPY=X',
        'GBPJPY': 'GBPJPY=X',
        'EURCHF': 'EURCHF=X',
        'AUDJPY': 'AUDJPY=X',
        'GBPAUD': 'GBPAUD=X',
        'EURAUD': 'EURAUD=X',
        'GBPCAD': 'GBPCAD=X',
    },
    
    # المعادن الثمينة
    'metals': {
        'XAUUSD': 'GC=F',      # الذهب
        'XAGUSD': 'SI=F',      # الفضة
        'XPTUSD': 'PL=F',      # البلاتين
        'XPDUSD': 'PA=F',      # البلاديوم
    },
    
    # الطاقة
    'energy': {
        'WTIUSD': 'CL=F',      # النفط الخام WTI
        'BRENTUSD': 'BZ=F',    # النفط برنت
        'NATURALGAS': 'NG=F',  # الغاز الطبيعي
        'HEATING': 'HO=F',     # زيت التدفئة
        'GASOLINE': 'RB=F',    # البنزين
    },
    
    # المؤشرات الأمريكية
    'indices_us': {
        'SPX500': '^GSPC',     # S&P 500
        'NASDAQ': '^IXIC',     # NASDAQ
        'DOW30': '^DJI',       # Dow Jones
        'RUSSELL': '^RUT',     # Russell 2000
        'VIX': '^VIX',         # مؤشر التقلب
    },
    
    # المؤشرات الأوروبية
    'indices_europe': {
        'DAX': '^GDAXI',       # DAX ألمانيا
        'FTSE': '^FTSE',       # FTSE UK
        'CAC40': '^FCHI',      # CAC فرنسا
        'IBEX': '^IBEX',       # IBEX إسبانيا
        'STOXX50': '^STOXX50E', # Euro Stoxx 50
    },
    
    # المؤشرات الآسيوية
    'indices_asia': {
        'NIKKEI': '^N225',     # Nikkei 225
        'HANGSENG': '^HSI',    # Hang Seng
        'SHANGHAI': '000001.SS', # Shanghai
        'KOSPI': '^KS11',      # KOSPI Korea
        'ASX200': '^AXJO',     # ASX Australia
    },
    
    # العملات الرقمية
    'crypto': {
        'BTCUSD': 'BTC-USD',
        'ETHUSD': 'ETH-USD',
        'BNBUSD': 'BNB-USD',
        'XRPUSD': 'XRP-USD',
        'ADAUSD': 'ADA-USD',
        'SOLUSD': 'SOL-USD',
    },
}


class RecommendationsEngine:
    """محرك التوصيات - يركز على أفضل نقاط الدخول والخروج"""
    
    def __init__(self, output_dir="recommendations"):
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.user_preferences_file = Path(__file__).parent / "user_preferences.json"
        self.load_user_preferences()
    
    def load_user_preferences(self):
        """تحميل تفضيلات المستخدم"""
        if self.user_preferences_file.exists():
            with open(self.user_preferences_file, 'r', encoding='utf-8') as f:
                self.preferences = json.load(f)
        else:
            # إعدادات افتراضية
            self.preferences = {
                'selected_pairs': [],  # فارغ = جميع الأزواج
                'categories': ['forex_major', 'metals', 'crypto'],  # الفئات المختارة
                'timeframes': ['1h', '4h', '1d'],
                'min_quality_score': 70,
                'risk_per_trade': 2.0,  # نسبة المخاطرة
            }
            self.save_user_preferences()
    
    def save_user_preferences(self):
        """حفظ تفضيلات المستخدم"""
        with open(self.user_preferences_file, 'w', encoding='utf-8') as f:
            json.dump(self.preferences, indent=2, ensure_ascii=False, fp=f)
    
    def get_all_pairs_list(self):
        """الحصول على قائمة بجميع الأزواج المتاحة"""
        all_pairs = {}
        for category, pairs in ALL_AVAILABLE_PAIRS.items():
            all_pairs.update(pairs)
        return all_pairs
    
    def get_selected_pairs(self):
        """الحصول على الأزواج المختارة من المستخدم"""
        if self.preferences['selected_pairs']:
            # المستخدم حدد أزواج معينة
            all_pairs = self.get_all_pairs_list()
            return {k: v for k, v in all_pairs.items() 
                   if k in self.preferences['selected_pairs']}
        else:
            # استخدام الفئات المختارة
            selected = {}
            for category in self.preferences['categories']:
                if category in ALL_AVAILABLE_PAIRS:
                    selected.update(ALL_AVAILABLE_PAIRS[category])
            return selected
    
    def fetch_data(self, symbol, ticker, timeframe='1h', period='7d'):
        """جلب بيانات الزوج"""
        try:
            df = yf.download(ticker, interval=timeframe, period=period, progress=False)
            
            if df is None or df.empty:
                return None
            
            # تحويل MultiIndex إلى columns عادية
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            
            # تسمية الأعمدة
            column_mapping = {
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume'
            }
            df = df.rename(columns=column_mapping)
            
            # تحويل إلى numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].squeeze(), errors='coerce')
            
            df = df.dropna()
            return df.reset_index()
            
        except Exception as e:
            print(f"❌ خطأ في جلب بيانات {symbol}: {e}")
            return None
    
    def find_optimal_entry(self, df, signal_type):
        """إيجاد أفضل نقطة دخول بناءً على مستويات الدعم والمقاومة"""
        if df is None or len(df) < 20:
            return None
        
        current_price = float(df['close'].iloc[-1])
        high_prices = df['high'].tail(20)
        low_prices = df['low'].tail(20)
        
        # حساب مستويات الدعم والمقاومة
        resistance_levels = []
        support_levels = []
        
        for i in range(1, len(high_prices) - 1):
            # مستويات المقاومة
            if high_prices.iloc[i] > high_prices.iloc[i-1] and high_prices.iloc[i] > high_prices.iloc[i+1]:
                resistance_levels.append(float(high_prices.iloc[i]))
            
            # مستويات الدعم
            if low_prices.iloc[i] < low_prices.iloc[i-1] and low_prices.iloc[i] < low_prices.iloc[i+1]:
                support_levels.append(float(low_prices.iloc[i]))
        
        if signal_type == 'buy':
            # للشراء: أفضل دخول عند الدعم
            if support_levels:
                nearest_support = min(support_levels, key=lambda x: abs(x - current_price))
                if nearest_support < current_price:
                    entry = nearest_support
                else:
                    entry = current_price * 0.998  # 0.2% أقل
            else:
                entry = current_price * 0.998
        else:  # sell
            # للبيع: أفضل دخول عند المقاومة
            if resistance_levels:
                nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price))
                if nearest_resistance > current_price:
                    entry = nearest_resistance
                else:
                    entry = current_price * 1.002  # 0.2% أعلى
            else:
                entry = current_price * 1.002
        
        return {
            'entry': entry,
            'current_price': current_price,
            'support_levels': support_levels[:3],
            'resistance_levels': resistance_levels[:3]
        }
    
    def calculate_optimal_sl_tp(self, df, entry, signal_type, symbol):
        """حساب أفضل وقف خسارة وأهداف ربح بناءً على ATR و Risk/Reward"""
        if df is None or len(df) < 14:
            return None
        
        # حساب ATR (Average True Range)
        atr = ta.volatility.average_true_range(
            df['high'], df['low'], df['close'], window=14
        ).iloc[-1]
        
        # تحديد pip_multiplier حسب نوع الأصل
        if symbol in ['XAUUSD', 'XAGUSD', 'XPTUSD', 'XPDUSD']:
            pip_multiplier = 0.1  # المعادن
        elif symbol in ['BTCUSD', 'ETHUSD']:
            pip_multiplier = 1.0  # العملات الرقمية
        elif 'JPY' in symbol:
            pip_multiplier = 0.01
        else:
            pip_multiplier = 0.0001
        
        # حساب وقف الخسارة بناءً على ATR
        atr_multiplier = 1.5
        sl_distance = atr * atr_multiplier
        
        # حساب أهداف الربح بنسب Risk/Reward مختلفة
        if signal_type == 'buy':
            stop_loss = entry - sl_distance
            take_profit_1 = entry + (sl_distance * 2)    # R:R 1:2
            take_profit_2 = entry + (sl_distance * 3)    # R:R 1:3
            take_profit_3 = entry + (sl_distance * 4)    # R:R 1:4
        else:  # sell
            stop_loss = entry + sl_distance
            take_profit_1 = entry - (sl_distance * 2)
            take_profit_2 = entry - (sl_distance * 3)
            take_profit_3 = entry - (sl_distance * 4)
        
        return {
            'stop_loss': stop_loss,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'take_profit_3': take_profit_3,
            'atr': atr,
            'risk_reward_ratios': [2, 3, 4]
        }
    
    def generate_recommendation(self, symbol, ticker, timeframe='1h'):
        """توليد توصية لزوج معين"""
        print(f"🔍 تحليل {symbol} على إطار {timeframe}...")
        
        # جلب البيانات
        df = self.fetch_data(symbol, ticker, timeframe)
        if df is None:
            return None
        
        # حساب المؤشرات الأساسية
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        # تحديد الإشارة
        rsi = float(df['rsi'].iloc[-1])
        macd_value = float(df['macd'].iloc[-1])
        macd_signal = float(df['macd_signal'].iloc[-1])
        
        signal = None
        if rsi < 35 and macd_value > macd_signal:
            signal = 'buy'
        elif rsi > 65 and macd_value < macd_signal:
            signal = 'sell'
        
        if not signal:
            return None
        
        # إيجاد أفضل نقطة دخول
        entry_data = self.find_optimal_entry(df, signal)
        if not entry_data:
            return None
        
        # حساب أفضل SL و TP
        sl_tp_data = self.calculate_optimal_sl_tp(
            df, entry_data['entry'], signal, symbol
        )
        if not sl_tp_data:
            return None
        
        # تجميع التوصية
        recommendation = {
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': signal,
            'entry': round(entry_data['entry'], 5),
            'current_price': round(entry_data['current_price'], 5),
            'stop_loss': round(sl_tp_data['stop_loss'], 5),
            'take_profit_1': round(sl_tp_data['take_profit_1'], 5),
            'take_profit_2': round(sl_tp_data['take_profit_2'], 5),
            'take_profit_3': round(sl_tp_data['take_profit_3'], 5),
            'risk_reward': sl_tp_data['risk_reward_ratios'],
            'atr': round(sl_tp_data['atr'], 5),
            'rsi': round(rsi, 2),
            'support_levels': [round(x, 5) for x in entry_data['support_levels']],
            'resistance_levels': [round(x, 5) for x in entry_data['resistance_levels']],
            'timestamp': datetime.now().isoformat(),
            'quality_score': self.calculate_quality_score(rsi, signal, sl_tp_data)
        }
        
        return recommendation
    
    def format_recommendation_message(self, recommendation):
        """تنسيق رسالة التوصية بالشكل الجديد"""
        symbol = recommendation['symbol']
        signal = recommendation['signal']
        direction_text = 'شراء' if signal == 'buy' else 'بيع'
        
        message = f"""
📊 *تحليل {symbol}*
━━━━━━━━━━━━━━━━━━
✅ التوصية: *{direction_text}*
📈 قوة الإشارة: {recommendation.get('quality_score', 85)}%
💎 نقطة دخول مثالية: `{recommendation['entry']:.5f}`
🛡️ SL محسوب بـ ATR: `{recommendation['stop_loss']:.5f}`

🎯 *أهداف الربح:*
   1️⃣ الهدف الأول: `{recommendation['take_profit_1']:.5f}` (R:R 1:2)
   2️⃣ الهدف الثاني: `{recommendation['take_profit_2']:.5f}` (R:R 1:3)
   3️⃣ الهدف الثالث: `{recommendation['take_profit_3']:.5f}` (R:R 1:5)

🔬 RSI: {recommendation['rsi']:.2f}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        return message
    
    def calculate_quality_score(self, rsi, signal, sl_tp_data):
        """حساب درجة جودة التوصية"""
        score = 50  # نقطة البداية
        
        # قوة RSI (25 نقطة)
        if signal == 'buy' and rsi < 25:
            score += 25
        elif signal == 'buy' and rsi < 30:
            score += 20
        elif signal == 'sell' and rsi > 75:
            score += 25
        elif signal == 'sell' and rsi > 70:
            score += 20
        
        # نسبة Risk/Reward (25 نقطة)
        if max(sl_tp_data['risk_reward_ratios']) >= 4:
            score += 25
        elif max(sl_tp_data['risk_reward_ratios']) >= 3:
            score += 20
        
        return min(score, 100)
    
    def scan_all_pairs(self):
        """فحص جميع الأزواج المختارة وتوليد التوصيات"""
        selected_pairs = self.get_selected_pairs()
        timeframes = self.preferences['timeframes']
        min_quality = self.preferences['min_quality_score']
        
        recommendations = []
        
        print(f"\n{'='*60}")
        print(f"🔍 فحص {len(selected_pairs)} زوج على {len(timeframes)} إطار زمني")
        print(f"{'='*60}\n")
        
        for symbol, ticker in selected_pairs.items():
            for timeframe in timeframes:
                rec = self.generate_recommendation(symbol, ticker, timeframe)
                
                if rec and rec['quality_score'] >= min_quality:
                    recommendations.append(rec)
                    print(f"✅ {symbol} ({timeframe}): {rec['signal'].upper()} - جودة {rec['quality_score']}")
        
        # حفظ التوصيات
        if recommendations:
            self.save_recommendations(recommendations)
        
        print(f"\n{'='*60}")
        print(f"✅ تم إيجاد {len(recommendations)} توصية")
        print(f"{'='*60}\n")
        
        return recommendations
    
    def save_recommendations(self, recommendations):
        """حفظ التوصيات"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.output_dir / f"recommendations_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)
        
        print(f"💾 تم حفظ التوصيات: {filename}")


def setup_user_preferences():
    """إعداد تفضيلات المستخدم بشكل تفاعلي"""
    print("\n" + "="*60)
    print("⚙️  إعداد تفضيلات التوصيات")
    print("="*60 + "\n")
    
    engine = RecommendationsEngine()
    
    # عرض الفئات المتاحة
    print("📂 الفئات المتاحة:")
    for i, (category, pairs) in enumerate(ALL_AVAILABLE_PAIRS.items(), 1):
        print(f"  {i}. {category}: {len(pairs)} زوج")
    
    print("\nاختر الفئات (أدخل الأرقام مفصولة بفاصلة، أو 'all' للجميع):")
    choice = input("> ").strip()
    
    if choice.lower() == 'all':
        engine.preferences['categories'] = list(ALL_AVAILABLE_PAIRS.keys())
        engine.preferences['selected_pairs'] = []
    else:
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            categories = list(ALL_AVAILABLE_PAIRS.keys())
            engine.preferences['categories'] = [categories[i-1] for i in indices if 0 < i <= len(categories)]
            engine.preferences['selected_pairs'] = []
        except:
            print("❌ إدخال غير صحيح، استخدام الإعدادات الافتراضية")
    
    # حد أدنى للجودة
    print("\n🎯 الحد الأدنى لجودة التوصيات (0-100، الافتراضي 70):")
    try:
        min_quality = int(input("> ").strip() or "70")
        engine.preferences['min_quality_score'] = max(0, min(100, min_quality))
    except:
        pass
    
    engine.save_user_preferences()
    print("\n✅ تم حفظ التفضيلات!")
    
    return engine


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        # وضع الإعداد التفاعلي
        engine = setup_user_preferences()
    else:
        # وضع التشغيل العادي
        engine = RecommendationsEngine()
    
    # تشغيل الفحص
    recommendations = engine.scan_all_pairs()
    
    # عرض ملخص
    if recommendations:
        print("\n📊 ملخص التوصيات:")
        for rec in recommendations:
            print(f"\n{'='*50}")
            print(f"📈 {rec['symbol']} | {rec['timeframe']}")
            print(f"   الإشارة: {rec['signal'].upper()}")
            print(f"   الدخول: {rec['entry']}")
            print(f"   وقف الخسارة: {rec['stop_loss']}")
            print(f"   الأهداف: {rec['take_profit_1']} / {rec['take_profit_2']} / {rec['take_profit_3']}")
            print(f"   الجودة: {rec['quality_score']}/100")

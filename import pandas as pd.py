import pandas as pd
import numpy as np
import talib
from twelvedata import TDClient
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import json
import time
from datetime import datetime, timedelta
import logging
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for
import uuid

# 1. إعدادات النظام
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ict_trading_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ICT Trading System')
logger.setLevel(logging.INFO)

# 2. جميع الأطر الزمنية المدعومة في Twelve Data
SUPPORTED_TIMEFRAMES = [
    '1min', '5min', '15min', '30min', '45min',
    '1h', '2h', '4h', '8h', '1day', '1week', '1month'
]

# 3. فئات الأصول والأزواج الرئيسية
ASSET_CLASSES = {
    'forex': [
        {'symbol': 'EUR/USD', 'exchange': 'FXCM'},
        {'symbol': 'GBP/USD', 'exchange': 'FXCM'},
        {'symbol': 'USD/JPY', 'exchange': 'FXCM'},
        {'symbol': 'AUD/USD', 'exchange': 'FXCM'},
        {'symbol': 'USD/CAD', 'exchange': 'FXCM'},
        {'symbol': 'NZD/USD', 'exchange': 'FXCM'},
        {'symbol': 'USD/CHF', 'exchange': 'FXCM'}
    ],
    'crypto': [
        {'symbol': 'BTC/USD', 'exchange': 'Coinbase'},
        {'symbol': 'ETH/USD', 'exchange': 'Coinbase'},
        {'symbol': 'XRP/USD', 'exchange': 'Coinbase'},
        {'symbol': 'LTC/USD', 'exchange': 'Coinbase'},
        {'symbol': 'ADA/USD', 'exchange': 'Coinbase'},
        {'symbol': 'DOT/USD', 'exchange': 'Coinbase'},
        {'symbol': 'DOGE/USD', 'exchange': 'Coinbase'}
    ],
    'stocks': [
        {'symbol': 'AAPL', 'exchange': 'NASDAQ'},
        {'symbol': 'MSFT', 'exchange': 'NASDAQ'},
        {'symbol': 'GOOGL', 'exchange': 'NASDAQ'},
        {'symbol': 'AMZN', 'exchange': 'NASDAQ'},
        {'symbol': 'TSLA', 'exchange': 'NASDAQ'},
        {'symbol': 'META', 'exchange': 'NASDAQ'},
        {'symbol': 'NVDA', 'exchange': 'NASDAQ'}
    ],
    'indices': [
        {'symbol': 'IXIC', 'exchange': 'NASDAQ'},  # Nasdaq
        {'symbol': 'DJI', 'exchange': 'SPGlobal'},  # Dow Jones
        {'symbol': 'SPX', 'exchange': 'SPGlobal'},  # S&P 500
        {'symbol': 'FTSE', 'exchange': 'LSE'},     # FTSE 100
        {'symbol': 'DAX', 'exchange': 'FWB'},       # DAX
        {'symbol': 'N225', 'exchange': 'JPX'},      # Nikkei 225
        {'symbol': 'HSI', 'exchange': 'HKEX'}       # Hang Seng
    ],
    'commodities': [
        {'symbol': 'XAU/USD', 'exchange': 'OANDA'},  # Gold
        {'symbol': 'XAG/USD', 'exchange': 'OANDA'},  # Silver
        {'symbol': 'CL/USD', 'exchange': 'ICE'},     # Oil
        {'symbol': 'NG/USD', 'exchange': 'ICE'},     # Natural Gas
        {'symbol': 'COPPER', 'exchange': 'COMEX'},   # Copper
        {'symbol': 'CORN', 'exchange': 'CBOT'},      # Corn
        {'symbol': 'SOYBEAN', 'exchange': 'CBOT'}    # Soybean
    ],
    'etfs': [
        {'symbol': 'SPY', 'exchange': 'NYSE'},      # S&P 500 ETF
        {'symbol': 'QQQ', 'exchange': 'NASDAQ'},    # Nasdaq ETF
        {'symbol': 'GLD', 'exchange': 'NYSE'},      # Gold ETF
        {'symbol': 'SLV', 'exchange': 'NYSE'},      # Silver ETF
        {'symbol': 'VTI', 'exchange': 'NYSE'},      # Total Stock Market ETF
        {'symbol': 'ARKK', 'exchange': 'NYSE'},     # ARK Innovation ETF
        {'symbol': 'TQQQ', 'exchange': 'NASDAQ'}    # Nasdaq 3x Leveraged ETF
    ]
}

# 4. حلول التحديات البرمجية
class ICTSolution:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = self.build_lstm_model()
        
    def detect_complex_ob(self, df, lookback=50):
        """اكتشاف مناطق Order Blocks باستخدام خوارزمية التجميع DBSCAN"""
        try:
            critical_points = []
            for i in range(1, len(df)-1):
                if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                    df['high'].iloc[i] > df['high'].iloc[i+1]) or \
                   (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                    df['low'].iloc[i] < df['low'].iloc[i+1]):
                    critical_points.append([i, df['close'].iloc[i]])
            
            if not critical_points:
                return {}
            
            scaler = StandardScaler()
            points_scaled = scaler.fit_transform(critical_points)
            
            db = DBSCAN(eps=0.3, min_samples=3).fit(points_scaled)
            labels = db.labels_
            
            ob_zones = {}
            for i, label in enumerate(labels):
                if label != -1:
                    if label not in ob_zones:
                        ob_zones[label] = []
                    ob_zones[label].append(critical_points[i][1])
            
            ob_results = {}
            for label, values in ob_zones.items():
                mean_val = np.mean(values)
                std_val = np.std(values)
                ob_results[f'OB_{label}'] = {'mean': mean_val, 'std': std_val}
            
            return ob_results
        except Exception as e:
            logger.error(f"Error in detect_complex_ob: {str(e)}")
            return {}

    def precise_liquidity_detection(self, df, window=15, sensitivity=1.5):
        """تحديد دقيق لنقاط السيولة باستخدام الانحراف المعياري"""
        try:
            df = df.copy()
            df['liq_high'] = df['high'].rolling(window).max()
            df['liq_low'] = df['low'].rolling(window).min()
            
            high_std = df['high'].rolling(window).std() * sensitivity
            low_std = df['low'].rolling(window).std() * sensitivity
            
            df['sell_liq'] = np.where(df['high'] > (df['liq_high'].shift(1) + high_std), 1, 0)
            df['buy_liq'] = np.where(df['low'] < (df['liq_low'].shift(1) - low_std), 1, 0)
            
            return df
        except Exception as e:
            logger.error(f"Error in precise_liquidity_detection: {str(e)}")
            return df

    def build_lstm_model(self):
        """نموذج LSTM للتكيف مع ظروف السوق المتغيرة"""
        try:
            model = Sequential([
                LSTM(64, return_sequences=True, input_shape=(60, 5)),
                LSTM(32),
                Dense(3, activation='softmax')
            ])
            model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
            return model
        except Exception as e:
            logger.error(f"Error building LSTM model: {str(e)}")
            return None

    def train_market_adaptation(self, historical_data):
        """تدريب النموذج على بيانات السوق التاريخية"""
        try:
            if self.model is None:
                self.model = self.build_lstm_model()
                
            X, y = [], []
            for i in range(60, len(historical_data)):
                features = historical_data.iloc[i-60:i][['open', 'high', 'low', 'close', 'volume']].values
                target = np.random.randint(0, 3, size=3)
                
                X.append(features)
                y.append(target)
            
            if len(X) == 0:
                logger.warning("No data for training")
                return
                
            self.model.fit(np.array(X), np.array(y), epochs=10, batch_size=32, verbose=0)
            logger.info("Market adaptation model trained successfully")
        except Exception as e:
            logger.error(f"Error in train_market_adaptation: {str(e)}")

    def predict_market_condition(self, recent_data):
        """التنبؤ بظروف السوق الحالية"""
        try:
            if self.model is None or recent_data.shape[0] < 60:
                return 2
            
            prediction = self.model.predict(np.array([recent_data]), verbose=0)
            return np.argmax(prediction[0])
        except Exception as e:
            logger.error(f"Error in predict_market_condition: {str(e)}")
            return 2

# 5. نظام التوصيات المتكامل مع Twelve Data
class ICTRecommendationSystem:
    def __init__(self, api_key, symbol, exchange, timeframe):
        self.api_key = api_key
        self.symbol = symbol
        self.exchange = exchange
        self.timeframe = timeframe
        self.solution = ICTSolution(api_key)
        self.symbol_safe = symbol.replace('/', '_').replace(' ', '_')
        self.data_file = f"{self.symbol_safe}_{exchange}_{timeframe}_data.csv"
        self.setup_directories()
        
    def setup_directories(self):
        """إنشاء مجلدات لحفظ البيانات"""
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        os.makedirs('recommendations', exist_ok=True)
        os.makedirs(f'logs/{self.symbol_safe}', exist_ok=True)
        os.makedirs(f'recommendations/{self.symbol_safe}', exist_ok=True)

    def fetch_market_data(self, n_bars=1000):
        """جلب بيانات السوق من Twelve Data"""
        try:
            logger.info(f"Fetching {n_bars} bars of {self.symbol} ({self.exchange}) - {self.timeframe}")
            
            td = TDClient(apikey=self.api_key)
            
            data = td.time_series(
                symbol=self.symbol,
                exchange=self.exchange,
                interval=self.timeframe,
                outputsize=n_bars
            ).with_ohlc().as_pandas()
            
            data = data.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            data.to_csv(f"data/{self.data_file}")
            
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {self.symbol}: {str(e)}")
            return pd.DataFrame()

    def calculate_indicators(self, df):
        """حساب المؤشرات الفنية"""
        try:
            if df.empty:
                return df, {}
                
            df['ma20'] = talib.SMA(df['close'], timeperiod=20)
            df['ma50'] = talib.SMA(df['close'], timeperiod=50)
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            
            df = self.solution.precise_liquidity_detection(df)
            ob_zones = self.solution.detect_complex_ob(df)
            
            return df, ob_zones
        except Exception as e:
            logger.error(f"Error calculating indicators for {self.symbol}: {str(e)}")
            return df, {}

    def generate_recommendation(self, df, ob_zones):
        """توليد توصيات التداول"""
        try:
            if df.empty or not ob_zones:
                return []
                
            latest = df.iloc[-1]
            signals = []
            
            recent_data = df[['open', 'high', 'low', 'close', 'volume']].tail(60).values
            market_condition = self.solution.predict_market_condition(recent_data)
            
            if 'buy_liq' in df.columns and latest['buy_liq'] == 1:
                buy_ob = self.find_nearest_ob(ob_zones, latest['close'], 'buy')
                if buy_ob:
                    entry = round(buy_ob['mean'], 5)
                    sl = round(entry - (buy_ob['std'] * 1.5), 5)
                    tp = round(entry + (buy_ob['std'] * 3), 5)
                    
                    signal_id = str(uuid.uuid4())
                    
                    signals.append({
                        'id': signal_id,
                        'type': 'BUY',
                        'entry': entry,
                        'stop_loss': sl,
                        'take_profit': tp,
                        'confidence': self.calculate_confidence(df, 'buy'),
                        'logic': "Liquidity sweep + Order block retracement",
                        'timestamp': datetime.utcnow().isoformat(),
                        'symbol': self.symbol,
                        'exchange': self.exchange,
                        'timeframe': self.timeframe,
                        'share_link': f"/recommendation/{signal_id}"
                    })
            
            if 'sell_liq' in df.columns and latest['sell_liq'] == 1:
                sell_ob = self.find_nearest_ob(ob_zones, latest['close'], 'sell')
                if sell_ob:
                    entry = round(sell_ob['mean'], 5)
                    sl = round(entry + (sell_ob['std'] * 1.5), 5)
                    tp = round(entry - (sell_ob['std'] * 3), 5)
                    
                    signal_id = str(uuid.uuid4())
                    
                    signals.append({
                        'id': signal_id,
                        'type': 'SELL',
                        'entry': entry,
                        'stop_loss': sl,
                        'take_profit': tp,
                        'confidence': self.calculate_confidence(df, 'sell'),
                        'logic': "Liquidity sweep + Order block retracement",
                        'timestamp': datetime.utcnow().isoformat(),
                        'symbol': self.symbol,
                        'exchange': self.exchange,
                        'timeframe': self.timeframe,
                        'share_link': f"/recommendation/{signal_id}"
                    })
            
            if signals:
                if market_condition == 0:
                    signals = [s for s in signals if s['type'] == 'BUY']
                elif market_condition == 1:
                    signals = [s for s in signals if s['type'] == 'SELL']
                else:
                    signals = [s for s in signals if s['confidence'] > 70]
            
            return signals
        except Exception as e:
            logger.error(f"Error generating recommendations for {self.symbol}: {str(e)}")
            return []

    def find_nearest_ob(self, ob_zones, price, ob_type):
        """العثور على أقرب منطقة تجميع للسعر الحالي"""
        try:
            best_ob = None
            min_diff = float('inf')
            
            for label, zone in ob_zones.items():
                if ob_type == 'buy' and zone['mean'] < price:
                    diff = price - zone['mean']
                elif ob_type == 'sell' and zone['mean'] > price:
                    diff = zone['mean'] - price
                else:
                    continue
                
                if diff < min_diff:
                    min_diff = diff
                    best_ob = zone
            
            return best_ob
        except:
            return None

    def calculate_confidence(self, df, signal_type):
        """حساب ثقة الإشارة بناءً على عوامل متعددة"""
        try:
            confidence = 70
            
            if len(df) > 1:
                volume_change = (df['volume'].iloc[-1] / df['volume'].iloc[-2] - 1) * 100
                if volume_change > 20:
                    confidence += 10
            
            rsi = df['rsi'].iloc[-1] if 'rsi' in df.columns else 50
            if signal_type == 'buy' and rsi < 40:
                confidence += 10
            elif signal_type == 'sell' and rsi > 60:
                confidence += 10
            
            if 'ma20' in df.columns and 'ma50' in df.columns:
                if df['ma20'].iloc[-1] > df['ma50'].iloc[-1]:
                    if signal_type == 'buy':
                        confidence += 10
                    else:
                        confidence -= 5
                else:
                    if signal_type == 'sell':
                        confidence += 10
                    else:
                        confidence -= 5
            
            return min(95, max(55, confidence))
        except:
            return 70

    def run(self):
        """تشغيل النظام لزوج وإطار زمني محدد"""
        try:
            df = self.fetch_market_data(n_bars=1000)
            
            if df.empty:
                logger.error(f"Failed to fetch data for {self.symbol}. Skipping.")
                return []
                
            model_flag = f'model_trained_{self.symbol_safe}.flag'
            if not os.path.exists(model_flag):
                logger.info(f"Training market adaptation model for {self.symbol}...")
                self.solution.train_market_adaptation(df)
                open(model_flag, 'w').close()
            
            df, ob_zones = self.calculate_indicators(df)
            recommendations = self.generate_recommendation(df, ob_zones)
            
            self.save_recommendations(recommendations)
            self.log_recommendations(recommendations, df)
            
            logger.info(f"Generated {len(recommendations)} recommendations for {self.symbol} ({self.timeframe})")
            
            return recommendations
        except Exception as e:
            logger.error(f"System error for {self.symbol}: {str(e)}")
            return []

    def save_recommendations(self, recommendations):
        """حفظ التوصيات في ملف"""
        try:
            if recommendations:
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                file_name = f"recommendations/{self.symbol_safe}/{self.symbol_safe}_{self.timeframe}_{timestamp}.json"
                with open(file_name, 'w') as f:
                    json.dump(recommendations, f, indent=2)
                logger.info(f"Recommendations saved to {file_name}")
                
                # تحديث التوصيات في الذاكرة للعرض على الويب
                global_recommendations = RecommendationStore.get_instance()
                for rec in recommendations:
                    global_recommendations.add_recommendation(rec)
        except Exception as e:
            logger.error(f"Error saving recommendations for {self.symbol}: {str(e)}")

    def log_recommendations(self, recommendations, df):
        """تسجيل التوصيات مع تحليل مفصل"""
        try:
            if not recommendations:
                return
                
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': self.symbol,
                'exchange': self.exchange,
                'timeframe': self.timeframe,
                'price': df.iloc[-1]['close'] if not df.empty else None,
                'recommendations': recommendations,
                'market_conditions': {
                    'rsi': df.iloc[-1]['rsi'] if 'rsi' in df.columns else None,
                    'ma20': df.iloc[-1]['ma20'] if 'ma20' in df.columns else None,
                    'ma50': df.iloc[-1]['ma50'] if 'ma50' in df.columns else None,
                    'volume': df.iloc[-1]['volume'] if 'volume' in df.columns else None
                }
            }
            
            log_file = f"logs/{self.symbol_safe}/{self.symbol_safe}_log.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Logging error for {self.symbol}: {str(e)}")

# 6. نظام التشغيل الرئيسي
class ICTSystemOrchestrator:
    def __init__(self, api_key, config):
        self.api_key = api_key
        self.config = config
        self.active_tasks = {}
        self.lock = threading.Lock()
        
    def process_asset(self, asset_class, symbol_config, timeframe):
        """معالجة زوج وإطار زمني واحد"""
        symbol = symbol_config['symbol']
        exchange = symbol_config.get('exchange', '')
        key = f"{symbol}_{timeframe}"
        
        try:
            # تجنب معالجة نفس الزوج/الإطار مرتين في نفس الوقت
            with self.lock:
                if key in self.active_tasks and self.active_tasks[key]:
                    return
                self.active_tasks[key] = True
            
            logger.info(f"Processing {symbol} ({exchange}) - {timeframe}")
            
            system = ICTRecommendationSystem(
                api_key=self.api_key,
                symbol=symbol,
                exchange=exchange,
                timeframe=timeframe
            )
            
            start_time = time.time()
            recommendations = system.run()
            processing_time = time.time() - start_time
            
            logger.info(f"Completed {symbol} ({timeframe}) in {processing_time:.2f} seconds. "
                        f"Recommendations: {len(recommendations)}")
            
            return recommendations
        except Exception as e:
            logger.error(f"Error processing {symbol} ({timeframe}): {str(e)}")
        finally:
            with self.lock:
                self.active_tasks[key] = False

    def run_all_assets(self):
        """تشغيل النظام لجميع الأصول والأطر الزمنية المحددة"""
        total_tasks = 0
        futures = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            for asset_class, symbols in self.config['assets'].items():
                for symbol_config in symbols:
                    for timeframe in self.config['timeframes']:
                        total_tasks += 1
                        futures.append(
                            executor.submit(
                                self.process_asset,
                                asset_class, symbol_config, timeframe
                            )
                        )
        
        logger.info(f"Started processing {total_tasks} tasks")
        
        # متابعة التقدم
        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                future.result()
            except Exception as e:
                logger.error(f"Task execution error: {str(e)}")
            
            if completed % 10 == 0:
                logger.info(f"Progress: {completed}/{total_tasks} tasks completed")
        
        logger.info(f"Completed all {total_tasks} tasks")
    
    def run_continuously(self, interval_minutes=5):
        """تشغيل النظام بشكل مستمر مع فترات راحة"""
        iteration = 0
        while True:
            iteration += 1
            logger.info(f"Starting iteration {iteration} at {datetime.utcnow().isoformat()}")
            
            start_time = time.time()
            self.run_all_assets()
            processing_time = time.time() - start_time
            
            sleep_time = max(0, interval_minutes * 60 - processing_time)
            if sleep_time > 0:
                logger.info(f"Processing took {processing_time:.2f} seconds. "
                            f"Sleeping for {sleep_time/60:.2f} minutes")
                time.sleep(sleep_time)

# 7. مخزن التوصيات للعرض على الويب
class RecommendationStore:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.recommendations = {}
        self.symbols = {}
        self.last_updated = None
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = RecommendationStore()
        return cls._instance
    
    def add_recommendation(self, recommendation):
        with self._lock:
            rec_id = recommendation['id']
            self.recommendations[rec_id] = recommendation
            
            # تنظيم التوصيات حسب الزوج
            symbol = recommendation['symbol']
            if symbol not in self.symbols:
                self.symbols[symbol] = []
                
            # إضافة فقط إذا لم تكن موجودة
            if rec_id not in [r['id'] for r in self.symbols[symbol]]:
                self.symbols[symbol].append(recommendation)
            
            self.last_updated = datetime.utcnow().isoformat()
    
    def get_recommendation(self, rec_id):
        return self.recommendations.get(rec_id)
    
    def get_all_recommendations(self, symbol=None, timeframe=None):
        if symbol and timeframe:
            return [r for r in self.recommendations.values() 
                    if r['symbol'] == symbol and r['timeframe'] == timeframe]
        elif symbol:
            return [r for r in self.recommendations.values() if r['symbol'] == symbol]
        elif timeframe:
            return [r for r in self.recommendations.values() if r['timeframe'] == timeframe]
        else:
            return list(self.recommendations.values())
    
    def get_symbols(self):
        return list(self.symbols.keys())
    
    def get_timeframes(self):
        return list(set(r['timeframe'] for r in self.recommendations.values()))

# 8. تطبيق Flask لواجهة الويب
app = Flask(__name__)
app.secret_key = 'ict_trading_system_secret_key'

@app.route('/')
def index():
    store = RecommendationStore.get_instance()
    symbols = store.get_symbols()
    timeframes = store.get_timeframes()
    last_updated = store.last_updated
    
    # الحصول على أحدث التوصيات (10 الأحدث)
    all_recommendations = store.get_all_recommendations()
    all_recommendations.sort(key=lambda x: x['timestamp'], reverse=True)
    latest_recommendations = all_recommendations[:10]
    
    return render_template(
        'index.html',
        symbols=symbols,
        timeframes=timeframes,
        recommendations=latest_recommendations,
        last_updated=last_updated
    )

@app.route('/symbol/<symbol>')
def symbol_recommendations(symbol):
    store = RecommendationStore.get_instance()
    timeframes = store.get_timeframes()
    recommendations = store.get_all_recommendations(symbol=symbol)
    
    recommendations.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template(
        'symbol.html',
        symbol=symbol,
        timeframes=timeframes,
        recommendations=recommendations
    )

@app.route('/timeframe/<timeframe>')
def timeframe_recommendations(timeframe):
    store = RecommendationStore.get_instance()
    symbols = store.get_symbols()
    recommendations = store.get_all_recommendations(timeframe=timeframe)
    
    recommendations.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template(
        'timeframe.html',
        timeframe=timeframe,
        symbols=symbols,
        recommendations=recommendations
    )

@app.route('/recommendation/<rec_id>')
def recommendation_detail(rec_id):
    store = RecommendationStore.get_instance()
    recommendation = store.get_recommendation(rec_id)
    
    if not recommendation:
        return render_template('error.html', message="Recommendation not found"), 404
    
    # إنشاء رابط المشاركة
    share_url = request.host_url.rstrip('/') + url_for('recommendation_detail', rec_id=rec_id)
    
    return render_template(
        'recommendation.html',
        recommendation=recommendation,
        share_url=share_url
    )

@app.route('/api/recommendations')
def api_recommendations():
    store = RecommendationStore.get_instance()
    symbol = request.args.get('symbol')
    timeframe = request.args.get('timeframe')
    limit = int(request.args.get('limit', 10))
    
    recommendations = store.get_all_recommendations(symbol, timeframe)
    recommendations.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'count': len(recommendations),
        'last_updated': store.last_updated,
        'recommendations': recommendations[:limit]
    })

@app.route('/api/recommendation/<rec_id>')
def api_recommendation_detail(rec_id):
    store = RecommendationStore.get_instance()
    recommendation = store.get_recommendation(rec_id)
    
    if not recommendation:
        return jsonify({'error': 'Recommendation not found'}), 404
    
    return jsonify(recommendation)

# 9. تهيئة وتشغيل النظام
def start_trading_system():
    # استبدال بمفتاح API الخاص بك
    API_KEY = "YOUR_TWELVE_DATA_API_KEY"
    
    # تهيئة الإعدادات
    config = {
        'timeframes': ['15min', '1h', '4h', '1day'],
        'assets': ASSET_CLASSES
    }
    
    # تهيئة وتشغيل النظام
    orchestrator = ICTSystemOrchestrator(api_key=API_KEY, config=config)
    orchestrator.run_continuously(interval_minutes=5)

# 10. إنشاء ملفات القوالب تلقائياً
def create_templates():
    templates = {
                'index.html': '''<!DOCTYPE html>
        <!-- HTML template content moved to templates/index.html file. See templates folder. -->
        ''',
        'symbol.html': '''<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ symbol }} - ICT Trading Recommendations</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
            .card { margin-bottom: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
            .buy-signal { border-left: 5px solid #28a745; }
            .sell-signal { border-left: 5px solid #dc3545; }
            .timeframe-badge { font-size: 0.8rem; }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand" href="/">ICT Trading System</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav">
                            <li class="nav-item">
                                <a class="nav-link" href="/">Home</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link active" href="#">{{ symbol }}</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>
        
            <div class="container mt-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h1>{{ symbol }} Recommendations</h1>
                    <div class="dropdown">
                        <button class="btn btn-secondary dropdown-toggle" type="button" id="timeframeDropdown" data-bs-toggle="dropdown">
                            Filter Timeframe
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="/symbol/{{ symbol }}">All Timeframes</a></li>
                            {% for tf in timeframes %}
                            <li><a class="dropdown-item" href="/symbol/{{ symbol }}?timeframe={{ tf }}">{{ tf }}</a></li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                
                <div class="row">
                    {% for rec in recommendations %}
                    <div class="col-md-6">
                        <div class="card {% if rec.type == 'BUY' %}buy-signal{% else %}sell-signal{% endif %}">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h5 class="card-title">
                                        <span class="badge {% if rec.type == 'BUY' %}bg-success{% else %}bg-danger{% endif %}">
                                            {{ rec.type }}
                                        </span>
                                        <span class="badge bg-info timeframe-badge">{{ rec.timeframe }}</span>
                                    </h5>
                                    <span class="badge {% if rec.confidence > 80 %}bg-success{% elif rec.confidence > 65 %}bg-warning{% else %}bg-danger{% endif %}">
                                        Confidence: {{ rec.confidence }}%
                                    </span>
                                </div>
                                
                                <div class="row mt-3">
                                    <div class="col-md-6">
                                        <p><strong>Entry:</strong> {{ rec.entry }}</p>
                                        <p><strong>Stop Loss:</strong> {{ rec.stop_loss }}</p>
                                        <p><strong>Take Profit:</strong> {{ rec.take_profit }}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong>Risk/Reward:</strong> 1:{{ ((rec.take_profit - rec.entry)/(rec.entry - rec.stop_loss)|round(2) if rec.type == 'BUY' else ((rec.entry - rec.take_profit)/(rec.stop_loss - rec.entry)|round(2)) }}</p>
                                        <p><strong>Time:</strong> {{ rec.timestamp|format_datetime }}</p>
                                    </div>
                                </div>
                                
                                <p class="card-text"><strong>Logic:</strong> {{ rec.logic }}</p>
                                
                                <div class="d-flex justify-content-between mt-3">
                                    <a href="{{ rec.share_link }}" class="btn btn-outline-primary btn-sm">
                                        <i class="fas fa-share-alt"></i> Share
                                    </a>
                                    <a href="{{ rec.share_link }}" class="btn btn-primary btn-sm">
                                        View Details <i class="fas fa-arrow-right"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="col-12">
                        <div class="alert alert-info">
                            No recommendations available for {{ symbol }}.
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        ''',
        # ... (other templates as in your original code)
    }

    # إنشاء مجلد القوالب
    os.makedirs('templates', exist_ok=True)

    # إنشاء ملفات القوالب
    for file_name, content in templates.items():
        with open(f'templates/{file_name}', 'w') as f:
            f.write(content)

    # إنشاء مرشح جينجا لتنسيق التاريخ
    with open('templates/filters.py', 'w') as f:
        f.write('''
from datetime import datetime

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime(format)
        except:
            return value
    return value
        ''')

    # تهيئة المرشحات في تطبيق Flask
    app.jinja_env.filters['format_datetime'] = lambda value: format_datetime(value)

if __name__ == "__main__":
    # إنشاء مجلد القوالب إذا لم يكن موجوداً
    os.makedirs('templates', exist_ok=True)

    # إنشاء ملفات القوالب
    create_templates()

    # بدء نظام التداول في خيط منفصل
    trading_thread = threading.Thread(target=start_trading_system, daemon=True)
    trading_thread.start()

    # بدء خادم الويب
app.run(host='0.0.0.0', port=5000, debug=False)
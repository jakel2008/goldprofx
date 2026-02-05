"""
تحليل شامل لجميع الأزواج - نسخة مباشرة
Comprehensive analysis for all pairs
"""

import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
import json
import os

# مجلد حفظ الإشارات
SIGNALS_DIR = "signals"
if not os.path.exists(SIGNALS_DIR):
    os.makedirs(SIGNALS_DIR)

# جميع الأزواج المتاحة
ALL_PAIRS = {
    # العملات الرئيسية (FOREX Major)
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'NZDUSD': 'NZDUSD=X',
    'USDCHF': 'USDCHF=X',

    # العملات الثانوية (FOREX Minor)
    'EURGBP': 'EURGBP=X',
    'EURJPY': 'EURJPY=X',
    'GBPJPY': 'GBPJPY=X',
    'EURCHF': 'EURCHF=X',
    'AUDJPY': 'AUDJPY=X',
    'GBPAUD': 'GBPAUD=X',
    'EURAUD': 'EURAUD=X',
    'GBPCAD': 'GBPCAD=X',

    # العملات الكروس الإضافية (FOREX Cross)
    'CADJPY': 'CADJPY=X',
    'CHFJPY': 'CHFJPY=X',
    'NZDJPY': 'NZDJPY=X',
    'AUDCAD': 'AUDCAD=X',
    'AUDCHF': 'AUDCHF=X',
    'AUDNZD': 'AUDNZD=X',
    'CADCHF': 'CADCHF=X',
    'EURNZD': 'EURNZD=X',
    'EURCAD': 'EURCAD=X',
    'GBPNZD': 'GBPNZD=X',
    'GBPCHF': 'GBPCHF=X',
    'NZDCAD': 'NZDCAD=X',
    'NZDCHF': 'NZDCHF=X',
    
    # المعادن الثمينة
    'XAUUSD': 'GC=F',
    'XAGUSD': 'SI=F',
    'XPTUSD': 'PL=F',
    'XPDUSD': 'PA=F',
    
    # المؤشرات الأمريكية
    'US30': '^DJI',
    'NAS100': '^IXIC',
    'SPX500': '^GSPC',
    'RUSSELL': '^RUT',
    'VIX': '^VIX',
    
    # العملات الرقمية
    'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD',
    'BNBUSD': 'BNB-USD',
    'XRPUSD': 'XRP-USD',
    'ADAUSD': 'ADA-USD',
    'SOLUSD': 'SOL-USD',
    'DOGEUSD': 'DOGE-USD',

    # الطاقة (النفط والغاز)
    'CRUDE': 'CL=F',
    'BRENT': 'BZ=F',
    'NATGAS': 'NG=F',
    'HEATING': 'HO=F',
    'GASOLINE': 'RB=F',
}

def calculate_quality_score(rsi, macd_signal, trend_strength, risk_reward):
    """حساب جودة الإشارة"""
    score = 0
    
    # RSI (20 نقطة)
    if 30 <= rsi <= 40 or 60 <= rsi <= 70:
        score += 20
    elif 40 < rsi < 60:
        score += 10
    
    # MACD (25 نقطة)
    if abs(macd_signal) > 0.5:
        score += 25
    elif abs(macd_signal) > 0.2:
        score += 15
    
    # قوة الترند (30 نقطة)
    if trend_strength > 0.7:
        score += 30
    elif trend_strength > 0.5:
        score += 20
    
    # نسبة المخاطرة للعائد (25 نقطة)
    if risk_reward >= 3:
        score += 25
    elif risk_reward >= 2:
        score += 15
    
    return min(score, 100)

def analyze_pair(pair, ticker):
    """تحليل زوج واحد"""
    try:
        print(f"🔍 تحليل {pair}...")
        
        # جلب البيانات
        try:
            data = yf.download(ticker, period='5d', interval='15m', progress=False)
        except Exception as e:
            # محاولة بفترة أطول إذا فشل التنزيل
            try:
                data = yf.download(ticker, period='60d', progress=False)
            except Exception as e2:
                print(f"  ❌ فشل جلب البيانات: {str(e2)}")
                return None
        
        if data.empty or len(data) < 20:
            print(f"  ⚠️  بيانات غير كافية")
            return None
        
        close_prices = data['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]
        close_prices = close_prices.squeeze()
        
        # تنقية البيانات
        close_prices = close_prices.dropna()
        if len(close_prices) < 20:
            print(f"  ⚠️  بيانات سعرية غير كافية بعد التنقية")
            return None
        
        # حساب المؤشرات
        data['RSI'] = ta.momentum.rsi(close_prices, window=14)
        
        macd = ta.trend.MACD(close_prices)
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()
        
        data['EMA_20'] = ta.trend.ema_indicator(close_prices, window=20)
        data['EMA_50'] = ta.trend.ema_indicator(close_prices, window=50)
        
        # آخر قيم
        current_price = float(close_prices.iloc[-1])
        rsi = float(data['RSI'].iloc[-1])
        macd_val = float(data['MACD'].iloc[-1])
        macd_signal = float(data['MACD_signal'].iloc[-1])
        ema_20 = float(data['EMA_20'].iloc[-1])
        ema_50 = float(data['EMA_50'].iloc[-1])
        
        # تحديد الإشارة
        signal = None
        if macd_val > macd_signal and rsi < 70 and current_price > ema_20:
            signal = 'buy'
            entry = current_price
            sl = current_price * 0.98
            tp1 = current_price * 1.015
            tp2 = current_price * 1.03
        elif macd_val < macd_signal and rsi > 30 and current_price < ema_20:
            signal = 'sell'
            entry = current_price
            sl = current_price * 1.02
            tp1 = current_price * 0.985
            tp2 = current_price * 0.97
        
        if not signal:
            print(f"  ℹ️  لا توجد إشارة واضحة")
            return None
        
        # حساب الجودة
        trend_strength = abs(ema_20 - ema_50) / current_price
        risk_reward = abs(tp1 - entry) / abs(entry - sl)
        quality_score = calculate_quality_score(rsi, macd_val - macd_signal, trend_strength, risk_reward)
        
        # حفظ الإشارة
        signal_data = {
            'pair': pair,
            'signal': signal,
            'entry': round(entry, 2 if current_price < 100 else 0),
            'sl': round(sl, 2 if current_price < 100 else 0),
            'tp1': round(tp1, 2 if current_price < 100 else 0),
            'tp2': round(tp2, 2 if current_price < 100 else 0),
            'quality_score': quality_score,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'rsi': round(rsi, 2),
            'current_price': round(current_price, 2 if current_price < 100 else 0)
        }
        
        # حفظ في ملف
        filename = f"{SIGNALS_DIR}/{pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(signal_data, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ {signal.upper()} | جودة: {quality_score}% | السعر: {current_price:.2f}")
        return signal_data
        
    except Exception as e:
        print(f"  ❌ خطأ: {str(e)}")
        return None

def main():
    print("\n" + "="*60)
    print("🚀 تحليل شامل لجميع الأزواج")
    print("="*60 + "\n")
    
    signals_found = []
    
    for pair, ticker in ALL_PAIRS.items():
        signal = analyze_pair(pair, ticker)
        if signal:
            signals_found.append(signal)
    
    print("\n" + "="*60)
    print(f"✅ انتهى التحليل - تم العثور على {len(signals_found)} إشارة")
    print("="*60 + "\n")
    
    if signals_found:
        print("📊 ملخص الإشارات:")
        for sig in signals_found:
            print(f"  • {sig['pair']}: {sig['signal'].upper()} - جودة {sig['quality_score']}%")

if __name__ == "__main__":
    main()

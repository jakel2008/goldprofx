"""
اختبار جلب الأسعار الحالية من Yahoo Finance
Test Current Price Fetching
"""

import yfinance as yf
from datetime import datetime

# خريطة الرموز
YF_SYMBOLS = {
    'XAUUSD': 'GC=F',
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'BTCUSD': 'BTC-USD'
}

print("=" * 60)
print("🔍 اختبار جلب الأسعار الحالية")
print("=" * 60)
print()

for symbol, yf_symbol in YF_SYMBOLS.items():
    try:
        print(f"📊 جاري جلب {symbol} ({yf_symbol})...")
        ticker = yf.Ticker(yf_symbol)
        
        # محاولة عدة طرق
        methods = [
            ('5m interval', lambda: ticker.history(period='1d', interval='5m')),
            ('1m interval', lambda: ticker.history(period='1d', interval='1m')),
            ('1d period', lambda: ticker.history(period='1d')),
            ('5d period', lambda: ticker.history(period='5d'))
        ]
        
        success = False
        for method_name, method_func in methods:
            try:
                hist = method_func()
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    print(f"   ✅ {symbol}: {price:.5f} (طريقة: {method_name})")
                    success = True
                    break
            except Exception as e:
                continue
        
        if not success:
            print(f"   ❌ {symbol}: فشل جلب السعر")
        
        print()
        
    except Exception as e:
        print(f"   ❌ خطأ في {symbol}: {e}")
        print()

print("=" * 60)
print("💡 ملاحظة: إذا فشل جلب بعض الأسعار،")
print("   قد تكون المشكلة في:")
print("   1. الاتصال بالإنترنت")
print("   2. Yahoo Finance API")
print("   3. رمز الزوج غير صحيح")
print("=" * 60)

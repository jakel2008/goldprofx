# -*- coding: utf-8 -*-
"""
فحص الأسعار الحالية من السوق
"""
import yfinance as yf
from datetime import datetime

print("📊 جلب الأسعار الحية من السوق...\n")

pairs_map = {
    'EURUSD=X': 'EURUSD',
    'GBPUSD=X': 'GBPUSD', 
    'GC=F': 'XAUUSD',
    'BTC-USD': 'BTCUSD',
    'USDJPY=X': 'USDJPY',
    'AUDUSD=X': 'AUDUSD'
}

current_prices = {}

for yahoo_symbol, display_name in pairs_map.items():
    try:
        ticker = yf.Ticker(yahoo_symbol)
        data = ticker.history(period='1d', interval='1m')
        
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            current_prices[display_name] = current_price
            print(f"✅ {display_name:10} : {current_price:>12.5f}")
        else:
            print(f"❌ {display_name:10} : لا توجد بيانات")
    except Exception as e:
        print(f"❌ {display_name:10} : خطأ - {e}")

print(f"\n📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"✅ تم جلب {len(current_prices)} سعر بنجاح")

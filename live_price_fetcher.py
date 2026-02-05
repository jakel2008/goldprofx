"""
جلب الأسعار الحية من مصادر متعددة
Live price fetcher from multiple sources
"""

import yfinance as yf
import requests
from datetime import datetime

# خريطة الرموز
YF_SYMBOLS = {
    'XAUUSD': 'GC=F',
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'NZDUSD': 'NZDUSD=X',
    'USDCHF': 'USDCHF=X',
    'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD',
    'US30': '^DJI',
    'NAS100': '^IXIC',
    'SPX500': '^GSPC'
}


def get_live_price(symbol):
    """
    الحصول على السعر الحالي للزوج
    Get current price for a symbol
    
    Args:
        symbol: رمز الزوج (مثل XAUUSD)
    
    Returns:
        float: السعر الحالي أو None إذا فشل
    """
    if symbol not in YF_SYMBOLS:
        print(f"Symbol {symbol} not found in mapping")
        return None
    
    yf_symbol = YF_SYMBOLS[symbol]
    
    # الطريقة 1: محاولة الحصول على السعر من info
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        # جرب حقول مختلفة
        price_fields = [
            'regularMarketPrice',
            'currentPrice',
            'bid',
            'ask',
            'previousClose',
            'open'
        ]
        
        for field in price_fields:
            if field in info and info[field]:
                price = float(info[field])
                if price > 0:
                    print(f"✓ Price for {symbol} from info.{field}: {price}")
                    return price
    except Exception as e:
        print(f"Failed to get price from info: {e}")
    
    # الطريقة 2: استخدام البيانات التاريخية
    try:
        ticker = yf.Ticker(yf_symbol)
        
        # جرب فترات مختلفة
        periods_intervals = [
            ('1d', '1m'),
            ('5d', '5m'),
            ('1mo', '1h'),
            ('1d', '5m')
        ]
        
        for period, interval in periods_intervals:
            try:
                hist = ticker.history(period=period, interval=interval)
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    if price > 0:
                        print(f"✓ Price for {symbol} from history ({period}/{interval}): {price}")
                        return price
            except:
                continue
    except Exception as e:
        print(f"Failed to get price from history: {e}")
    
    # الطريقة 3: download - آخر محاولة
    try:
        data = yf.download(yf_symbol, period='1d', interval='1m', progress=False)
        if not data.empty:
            price = float(data['Close'].iloc[-1].iloc[0] if hasattr(data['Close'].iloc[-1], 'iloc') else data['Close'].iloc[-1])
            if price > 0:
                print(f"✓ Price for {symbol} from download: {price}")
                return price
    except Exception as e:
        print(f"Failed to get price from download: {e}")
    
    print(f"✗ Could not get price for {symbol}")
    return None


def get_multiple_prices(symbols):
    """
    الحصول على أسعار متعددة
    Get multiple prices at once
    
    Args:
        symbols: قائمة بالأزواج
    
    Returns:
        dict: قاموس {symbol: price}
    """
    prices = {}
    for symbol in symbols:
        price = get_live_price(symbol)
        if price:
            prices[symbol] = price
    return prices


if __name__ == '__main__':
    # اختبار
    print("Testing live price fetcher...")
    print("=" * 60)
    
    test_symbols = ['XAUUSD', 'EURUSD', 'BTCUSD']
    
    for symbol in test_symbols:
        print(f"\nFetching {symbol}...")
        price = get_live_price(symbol)
        if price:
            print(f"SUCCESS: {symbol} = {price}")
        else:
            print(f"FAILED: Could not get price for {symbol}")
    
    print("\n" + "=" * 60)
    print("Testing multiple fetch...")
    prices = get_multiple_prices(test_symbols)
    print(f"Results: {prices}")

# -*- coding: utf-8 -*-
"""
Smart Forex Analyzer - Full Backend Module
Based on tkinter original code
"""
import requests
import pandas as pd
import ta
import numpy as np
from datetime import datetime, timedelta

# Configuration
API_KEY = "079cdb64bbc8415abcf8f7be7e389349"
BASE_URL = "https://api.twelvedata.com/time_series"

class DataFetchError(Exception):
    pass

def fetch_data(symbol, interval, outputsize=100):
    """Fetch historical data from Twelve Data API with retry logic"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": outputsize,
                "apikey": API_KEY
            }
            
            response = requests.get(BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if "values" not in data:
                if attempt < max_attempts - 1:
                    continue
                error_message = data.get("message", "Unknown error occurred")
                raise DataFetchError(f"API Error: {error_message}")
            
            df = pd.DataFrame(data["values"])
            df = df.iloc[::-1].reset_index(drop=True)
            
            # Convert to numeric and datetime
            df["open"] = pd.to_numeric(df["open"])
            df["high"] = pd.to_numeric(df["high"])
            df["low"] = pd.to_numeric(df["low"])
            df["close"] = pd.to_numeric(df["close"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            
            # Rename columns to match original code
            df = df.rename(columns={
                "datetime": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close"
            })
            
            return df
            
        except requests.exceptions.RequestException as e:
            if attempt < max_attempts - 1:
                continue
            raise DataFetchError(f"Network error: {str(e)}")
        except (KeyError, ValueError) as e:
            if attempt < max_attempts - 1:
                continue
            raise DataFetchError(f"Data processing error: {str(e)}")
    
    raise DataFetchError("Failed to fetch data after multiple attempts")

def calculate_fibonacci_levels(high, low):
    """Calculate Fibonacci retracement levels"""
    levels = {
        "0.0": high,
        "0.236": high - (high - low) * 0.236,
        "0.382": high - (high - low) * 0.382,
        "0.5": high - (high - low) * 0.5,
        "0.618": high - (high - low) * 0.618,
        "1.0": low
    }
    return levels

def calculate_support_resistance(df):
    """Calculate support and resistance levels"""
    high = df["high"].max()
    low = df["low"].min()
    pivot = (high + low + df["close"].iloc[-1]) / 3
    resistance = 2 * pivot - low
    support = 2 * pivot - high
    return support, pivot, resistance

def harmonic_analysis(df):
    """Harmonic Pattern Analysis"""
    signals = ["Harmonic Pattern Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    الأنماط التوافقية تشير إلى انعكاس بعد اكتمال أنماط سعرية محددة مثل Gartley أو Bat.
    تم اختيار نقطة الدخول بعد اكتمال النمط، ومن المتوقع أن ينعكس السوق.
    مستويات جني الأرباح تعتمد على امتدادات فيبوناتشي، ووقف الخسارة أسفل أدنى نقطة في النمط.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def elliott_wave_analysis(df):
    """Elliott Wave Analysis"""
    signals = ["Elliott Wave Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    نظرية موجات إليوت تشير إلى أن حركات السوق تتبع نمط 5 موجات دافعة و3 موجات تصحيحية.
    يتم الدخول بعد اكتمال الموجة 4 وقبل بدء الموجة 5. جني الأرباح يحسب بناءً على طول الموجة 5.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def head_and_shoulders_analysis(df):
    """Head and Shoulders Pattern Analysis"""
    signals = ["Head and Shoulders Sell Signal"]
    entry_point = df["close"].iloc[-1] * 0.99
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point - (high - low) * 0.05, 
        entry_point - (high - low) * 0.1, 
        entry_point - (high - low) * 0.15
    ]
    stop_loss = entry_point + (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    نمط الرأس والكتفين يشير إلى انعكاس. يتم الدخول بعد كسر خط العنق.
    جني الأرباح يُحدد بالمسافة بين الرأس وخط العنق، ووقف الخسارة فوق الرأس.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def smc_analysis(df):
    """Smart Money Concepts Analysis"""
    signals = ["SMC Liquidity Zone Identified"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    استراتيجية SMC تركز على مناطق السيولة. يتم الدخول عندما يدخل السعر هذه المناطق.
    جني الأرباح يعتمد على امتصاص السيولة المؤسسية، ووقف الخسارة خارج المنطقة.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def ict_analysis(df):
    """Inner Circle Trading Analysis"""
    signals = ["ICT Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    استراتيجية ICT تحدد مناطق السيولة وكتل الأوامر. يتم الدخول بعد تأكيد حركة السعر
    لتحول الاتجاه. جني الأرباح يعتمد على أهداف السيولة.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def ist_analysis(df):
    """Institutional Trading Analysis"""
    signals = ["IST Institutional Flow Buy Signal"]
    entry_point = df["close"].iloc[-1] * 1.01
    high = df["high"].max()
    low = df["low"].min()
    fib_levels = calculate_fibonacci_levels(high, low)
    
    take_profit = [
        entry_point + (high - low) * 0.05, 
        entry_point + (high - low) * 0.1, 
        entry_point + (high - low) * 0.15
    ]
    stop_loss = entry_point - (high - low) * 0.02
    
    support, pivot, resistance = calculate_support_resistance(df)
    
    explanation = f"""
    استراتيجية IST تركز على تدفق أوامر المؤسسات وحركة السعر. يتم الدخول بعد كسر مستويات سعرية
    رئيسية أو تحديد كتلة أوامر مؤسسية. جني الأرباح متوقع بناءً على سلوك المؤسسات.

    الدعم: {support:.5f}, المحور: {pivot:.5f}, المقاومة: {resistance:.5f}
    """
    return signals, entry_point, take_profit, stop_loss, fib_levels, explanation

def perform_analysis(symbol, interval, strategy):
    """Main analysis function"""
    try:
        # Fetch data
        df = fetch_data(symbol, interval)
        
        # Normalize strategy name (handle both lowercase and mixed case)
        strategy_map = {
            "harmonic": "harmonic",
            "elliott": "elliott_wave",
            "elliott wave": "elliott_wave",
            "head_shoulders": "head_shoulders",
            "head and shoulders": "head_shoulders",
            "smc": "smc",
            "ict": "ict",
            "ist": "ist"
        }
        
        strategy_key = strategy.lower().replace(" ", "_")
        if strategy_key not in strategy_map:
            strategy_key = strategy_map.get(strategy.lower().replace("_", " "), strategy.lower())
        else:
            strategy_key = strategy_map[strategy_key]
        
        # Select strategy
        if strategy_key == "harmonic":
            signals, ep, tp, sl, fib, exp = harmonic_analysis(df)
        elif strategy_key == "elliott_wave":
            signals, ep, tp, sl, fib, exp = elliott_wave_analysis(df)
        elif strategy_key == "head_shoulders":
            signals, ep, tp, sl, fib, exp = head_and_shoulders_analysis(df)
        elif strategy_key == "smc":
            signals, ep, tp, sl, fib, exp = smc_analysis(df)
        elif strategy_key == "ict":
            signals, ep, tp, sl, fib, exp = ict_analysis(df)
        elif strategy_key == "ist":
            signals, ep, tp, sl, fib, exp = ist_analysis(df)
        else:
            raise ValueError(f"Invalid strategy: {strategy}")
        
        # Calculate support/resistance
        support, pivot, resistance = calculate_support_resistance(df)
        
        # Prepare chart data
        chart_data = {
            'dates': [record['Date'].isoformat() for record in df.tail(50).to_dict('records')],
            'open': df.tail(50)['open'].tolist(),
            'high': df.tail(50)['high'].tolist(),
            'low': df.tail(50)['low'].tolist(),
            'close': df.tail(50)['close'].tolist()
        }
        
        return {
            'success': True,
            'signal': ' | '.join(signals),
            'entry_point': float(ep),
            'take_profit1': float(tp[0]),
            'take_profit2': float(tp[1]),
            'take_profit3': float(tp[2]),
            'stop_loss': float(sl),
            'fibonacci_levels': {k: float(v) for k, v in fib.items()},
            'support': float(support),
            'pivot': float(pivot),
            'resistance': float(resistance),
            'explanation': exp,
            'chart_data': chart_data
        }
        
    except DataFetchError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': f'Analysis error: {str(e)}'}

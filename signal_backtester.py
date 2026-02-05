# -*- coding: utf-8 -*-
"""
نظام Backtesting للإشارات
Signal Backtesting System
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json

class SignalBacktester:
    """نظام اختبار الإشارات على بيانات تاريخية"""
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.equity_curve = []
        
    def backtest_strategy(self, symbol, start_date, end_date):
        """اختبار الاستراتيجية على فترة زمنية"""
        try:
            # جلب البيانات التاريخية
            df = yf.download(symbol, start=start_date, end=end_date, interval='1h')
            
            if df.empty:
                return None
            
            # حساب المؤشرات
            df = self.calculate_indicators(df)
            
            # محاكاة التداول
            for i in range(50, len(df)):
                signal = self.generate_signal(df.iloc[:i])
                
                if signal:
                    result = self.execute_trade(df.iloc[i:], signal)
                    if result:
                        self.trades.append(result)
            
            # حساب الإحصائيات
            stats = self.calculate_statistics()
            
            return stats
            
        except Exception as e:
            print(f"خطأ في Backtesting: {e}")
            return None
    
    def calculate_indicators(self, df):
        """حساب المؤشرات المطلوبة"""
        # EMA
        df['ema_9'] = df['Close'].ewm(span=9).mean()
        df['ema_21'] = df['Close'].ewm(span=21).mean()
        df['ema_50'] = df['Close'].ewm(span=50).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        df['atr'] = ranges.max(axis=1).rolling(14).mean()
        
        return df
    
    def generate_signal(self, df):
        """توليد إشارة تداول"""
        if len(df) < 50:
            return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # شروط الشراء
        if (latest['ema_9'] > latest['ema_21'] > latest['ema_50'] and
            latest['rsi'] < 40 and
            latest['macd'] > latest['macd_signal'] and
            prev['macd'] <= prev['macd_signal']):
            
            return {
                'type': 'buy',
                'entry': latest['Close'],
                'sl': latest['Close'] - (latest['atr'] * 1.5),
                'tp1': latest['Close'] + (latest['atr'] * 2.0),
                'tp2': latest['Close'] + (latest['atr'] * 3.5),
                'tp3': latest['Close'] + (latest['atr'] * 5.0)
            }
        
        # شروط البيع
        elif (latest['ema_9'] < latest['ema_21'] < latest['ema_50'] and
              latest['rsi'] > 60 and
              latest['macd'] < latest['macd_signal'] and
              prev['macd'] >= prev['macd_signal']):
            
            return {
                'type': 'sell',
                'entry': latest['Close'],
                'sl': latest['Close'] + (latest['atr'] * 1.5),
                'tp1': latest['Close'] - (latest['atr'] * 2.0),
                'tp2': latest['Close'] - (latest['atr'] * 3.5),
                'tp3': latest['Close'] - (latest['atr'] * 5.0)
            }
        
        return None
    
    def execute_trade(self, future_data, signal):
        """محاكاة تنفيذ صفقة"""
        entry = signal['entry']
        sl = signal['sl']
        tp1 = signal['tp1']
        
        for i in range(len(future_data)):
            row = future_data.iloc[i]
            
            if signal['type'] == 'buy':
                # فحص SL
                if row['Low'] <= sl:
                    loss = sl - entry
                    return {
                        'type': 'buy',
                        'entry': entry,
                        'exit': sl,
                        'profit': loss,
                        'result': 'loss',
                        'bars': i
                    }
                
                # فحص TP1
                if row['High'] >= tp1:
                    profit = tp1 - entry
                    return {
                        'type': 'buy',
                        'entry': entry,
                        'exit': tp1,
                        'profit': profit,
                        'result': 'win',
                        'bars': i
                    }
            
            else:  # sell
                # فحص SL
                if row['High'] >= sl:
                    loss = entry - sl
                    return {
                        'type': 'sell',
                        'entry': entry,
                        'exit': sl,
                        'profit': loss,
                        'result': 'loss',
                        'bars': i
                    }
                
                # فحص TP1
                if row['Low'] <= tp1:
                    profit = entry - tp1
                    return {
                        'type': 'sell',
                        'entry': entry,
                        'exit': tp1,
                        'profit': profit,
                        'result': 'win',
                        'bars': i
                    }
        
        return None
    
    def calculate_statistics(self):
        """حساب إحصائيات الأداء"""
        if not self.trades:
            return None
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['result'] == 'win'])
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades) * 100
        
        total_profit = sum(t['profit'] for t in self.trades if t['result'] == 'win')
        total_loss = sum(abs(t['profit']) for t in self.trades if t['result'] == 'loss')
        
        net_profit = total_profit - total_loss
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        avg_win = total_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'net_profit': net_profit,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    
    def generate_report(self, stats):
        """إنشاء تقرير الأداء"""
        if not stats:
            return "لا توجد صفقات للتحليل"
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║              📊 تقرير Backtesting                        ║
╚══════════════════════════════════════════════════════════╝

📈 النتائج الإجمالية:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
إجمالي الصفقات: {stats['total_trades']}
✅ الصفقات الرابحة: {stats['winning_trades']}
❌ الصفقات الخاسرة: {stats['losing_trades']}

🎯 معدل النجاح: {stats['win_rate']:.2f}%

💰 الأرباح الإجمالية: ${stats['total_profit']:.2f}
💸 الخسائر الإجمالية: ${stats['total_loss']:.2f}
📊 صافي الربح: ${stats['net_profit']:.2f}

⚖️ عامل الربح: {stats['profit_factor']:.2f}

📈 متوسط الربح: ${stats['avg_win']:.2f}
📉 متوسط الخسارة: ${stats['avg_loss']:.2f}

{'='*60}
"""
        
        return report


if __name__ == "__main__":
    print("📊 نظام Backtesting")
    print("=" * 60)
    
    backtester = SignalBacktester()
    
    # اختبار على آخر 3 أشهر
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    stats = backtester.backtest_strategy(
        'BTC-USD',
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if stats:
        print(backtester.generate_report(stats))

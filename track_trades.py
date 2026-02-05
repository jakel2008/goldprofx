"""
نظام متابعة شامل للصفقات - يعرض النشط والمنتهي والرابح والخاسر
Complete Trade Tracking System
"""

import json
import os
from pathlib import Path
from datetime import datetime
import yfinance as yf
import pandas as pd

SIGNALS_DIR = "signals"
TRADES_TRACKER_FILE = "trades_tracker.json"

def get_current_price(pair):
    """الحصول على السعر الحالي"""
    ticker_map = {
        'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X', 'USDJPY': 'USDJPY=X',
        'AUDUSD': 'AUDUSD=X', 'USDCAD': 'USDCAD=X', 'NZDUSD': 'NZDUSD=X',
        'USDCHF': 'USDCHF=X', 'XAUUSD': 'GC=F', 'XAGUSD': 'SI=F',
        'US30': '^DJI', 'NAS100': '^IXIC', 'SPX500': '^GSPC',
        'BTCUSD': 'BTC-USD', 'ETHUSD': 'ETH-USD', 'BNBUSD': 'BNB-USD',
        'XRPUSD': 'XRP-USD', 'ADAUSD': 'ADA-USD', 'SOLUSD': 'SOL-USD'
    }
    
    ticker = ticker_map.get(pair)
    if not ticker:
        return None
    
    try:
        ticker_obj = yf.Ticker(ticker)
        fast_info = getattr(ticker_obj, "fast_info", None)
        if fast_info and fast_info.get("last_price"):
            return float(fast_info.get("last_price"))
    except:
        pass

    def _extract_close_value(data_frame):
        if data_frame is None or data_frame.empty:
            return None
        close_data = data_frame["Close"]
        if isinstance(close_data, pd.DataFrame):
            last_row = close_data.iloc[-1]
            if isinstance(last_row, pd.Series):
                return float(last_row.iloc[0])
            return float(last_row)
        if isinstance(close_data, pd.Series):
            last_val = close_data.iloc[-1]
            if isinstance(last_val, pd.Series):
                return float(last_val.iloc[0])
            return float(last_val)
        return None

    try:
        data = yf.download(ticker, period='1d', interval='1m', progress=False, auto_adjust=False)
        price = _extract_close_value(data)
        if price:
            return price
    except:
        pass

    try:
        data = yf.download(ticker, period='5d', interval='15m', progress=False, auto_adjust=False)
        price = _extract_close_value(data)
        if price:
            return price
    except:
        pass
    return None

def check_trade_status(signal):
    """فحص حالة الصفقة"""
    entry = signal['entry']
    current_price = get_current_price(signal['pair'])
    if not current_price:
        return 'active', 0, entry
    sl = signal['sl']
    tp1 = signal['tp1']
    tp2 = signal.get('tp2', tp1)
    signal_type = signal['signal']
    
    # حساب الربح/الخسارة بالنقاط
    if signal_type == 'buy':
        pips = current_price - entry
        
        # فحص وقف الخسارة
        if current_price <= sl:
            return 'loss', round((sl - entry) / entry * 100, 2), current_price
        
        # فحص الهدف الثاني
        if current_price >= tp2:
            return 'win_tp2', round((tp2 - entry) / entry * 100, 2), current_price
        
        # فحص الهدف الأول
        if current_price >= tp1:
            return 'win_tp1', round((tp1 - entry) / entry * 100, 2), current_price
        
        # لا يزال نشط
        profit_percent = round(pips / entry * 100, 2)
        return 'active', profit_percent, current_price
        
    else:  # sell
        pips = entry - current_price
        
        # فحص وقف الخسارة
        if current_price >= sl:
            return 'loss', round((entry - sl) / entry * 100, 2), current_price
        
        # فحص الهدف الثاني
        if current_price <= tp2:
            return 'win_tp2', round((entry - tp2) / entry * 100, 2), current_price
        
        # فحص الهدف الأول
        if current_price <= tp1:
            return 'win_tp1', round((entry - tp1) / entry * 100, 2), current_price
        
        # لا يزال نشط
        profit_percent = round(pips / entry * 100, 2)
        return 'active', profit_percent, current_price

def load_all_trades():
    """تحميل جميع الصفقات مع حالاتها"""
    trades = []
    
    if not os.path.exists(SIGNALS_DIR):
        return trades
    
    for file in Path(SIGNALS_DIR).glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                signal = json.load(f)
                
            status, profit_percent, current_price = check_trade_status(signal)
            
            trade = {
                'pair': signal['pair'],
                'signal': signal['signal'],
                'entry': signal['entry'],
                'sl': signal['sl'],
                'tp1': signal['tp1'],
                'tp2': signal.get('tp2', signal['tp1']),
                'current_price': current_price,
                'status': status,
                'profit_percent': profit_percent,
                'quality_score': signal.get('quality_score', 0),
                'timestamp': signal.get('timestamp', ''),
                'file': file.name
            }
            trades.append(trade)
        except Exception as e:
                print(f"Error reading {file.name}: {e}")
    return trades

def build_report(trades):
    """بناء تقرير الصفقات بدون طباعة"""
    active = [t for t in trades if t['status'] == 'active']
    winners = [t for t in trades if 'win' in t['status']]
    losers = [t for t in trades if t['status'] == 'loss']
    
    total_profit = sum(t['profit_percent'] for t in winners)
    total_loss = sum(t['profit_percent'] for t in losers)
    net_profit = total_profit + total_loss

    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_trades': len(trades),
            'active': len(active),
            'winners': len(winners),
            'losers': len(losers),
            'net_profit_percent': round(net_profit, 2)
        },
        'active_trades': [
            {
                'pair': t['pair'],
                'signal': t['signal'],
                'entry': t['entry'],
                'current_price': t['current_price'],
                'profit_percent': t['profit_percent']
            } for t in active
        ],
        'closed_trades': {
            'winners': [
                {
                    'pair': t['pair'],
                    'signal': t['signal'],
                    'profit_percent': t['profit_percent']
                } for t in winners
            ],
            'losers': [
                {
                    'pair': t['pair'],
                    'signal': t['signal'],
                    'profit_percent': t['profit_percent']
                } for t in losers
            ]
        }
    }
    return report, active, winners, losers, net_profit

def save_report(report):
    """حفظ تقرير الصفقات"""
    with open(TRADES_TRACKER_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

def generate_report(save_file=True):
    """إنشاء تقرير الصفقات (مفيد للـ API)"""
    trades = load_all_trades()
    report, _, _, _, _ = build_report(trades)
    if save_file:
        save_report(report)
    return report

def display_trades():
    """عرض جميع الصفقات مع حالاتها"""
    print("\n" + "="*80)
    print("Trade Tracking System")
    print("="*80 + "\n")
    
    trades = load_all_trades()
    if not trades:
        print("No trades found")
        return

    report, active, winners, losers, net_profit = build_report(trades)
    
    print(f"Total Trades: {len(trades)}")
    print(f"Active: {len(active)}")
    print(f"Winners: {len(winners)}")
    print(f"Losers: {len(losers)}")
    print(f"Net Profit: {net_profit:.2f}%")
    print("\n" + "="*80)
    
    if active:
        print("\nACTIVE TRADES:")
        print("-" * 80)
        for t in active:
            color = "+" if t['profit_percent'] > 0 else "-"
            print(f"{color} {t['pair']:8} | {t['signal'].upper():4} | "
                  f"دخول: {t['entry']:8.2f} | حالي: {t['current_price']:8.2f} | "
                  f"ربح: {t['profit_percent']:+.2f}% | جودة: {t['quality_score']}%")
    
    if winners:
        print("\nWINNING TRADES:")
        print("-" * 80)
        for t in winners:
            target = "TP2" if "tp2" in t['status'] else "TP1"
            print(f"WIN {t['pair']:8} | {t['signal'].upper():4} | "
                  f"دخول: {t['entry']:8.2f} | خروج: {t['current_price']:8.2f} | "
                  f"ربح: +{t['profit_percent']:.2f}% ({target})")
    
    if losers:
        print("\nLOSING TRADES:")
        print("-" * 80)
        for t in losers:
            print(f"LOSS {t['pair']:8} | {t['signal'].upper():4} | "
                  f"دخول: {t['entry']:8.2f} | وقف: {t['current_price']:8.2f} | "
                  f"خسارة: {t['profit_percent']:.2f}%")
    
    print("\n" + "="*80)
    save_report(report)

if __name__ == "__main__":
    display_trades()

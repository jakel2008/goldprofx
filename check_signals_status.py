# -*- coding: utf-8 -*-
"""
فحص وتقييم التوصيات المنشورة
يحدد: النشطة، المنتهية، الرابحة، الخاسرة
"""

import os
import json
import yfinance as yf
from datetime import datetime, timedelta

os.system('chcp 65001 > nul')

def get_current_price(symbol):
    """جلب السعر الحالي"""
    ticker_map = {
        'EURUSD': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'USDJPY': 'USDJPY=X',
        'AUDUSD': 'AUDUSD=X',
        'USDCAD': 'USDCAD=X',
        'NZDUSD': 'NZDUSD=X',
        'USDCHF': 'USDCHF=X',
        'XAUUSD': 'GC=F',
        'XAGUSD': 'SLV',
        'CRUDE': 'USO',
        'BRENT': 'BNO',
        'NATGAS': 'UNG',
        'SPX': '^GSPC',
        'DJI': '^DJI',
        'NDX': '^NDX',
        'RUT': '^RUT',
        'BTCUSD': 'BTC-USD',
        'ETHUSD': 'ETH-USD',
        'XRPUSD': 'XRP-USD',
        'ADAUSD': 'ADA-USD',
        'SOLUSD': 'SOL-USD',
        'DOGEUSD': 'DOGE-USD'
    }
    
    ticker = ticker_map.get(symbol, symbol)
    try:
        # محاولة جلب البيانات بفترات مختلفة
        for period in ['1d', '5d']:
            for interval in ['1m', '5m', '1h']:
                try:
                    data = yf.download(ticker, period=period, interval=interval, progress=False)
                    if not data.empty and len(data) > 0:
                        return float(data['Close'].iloc[-1])
                except:
                    continue
    except Exception as e:
        print(f"  [تحذير] خطأ في جلب {symbol}: {e}")
    return None

def check_signal_status(signal_file):
    """فحص حالة إشارة واحدة"""
    try:
        with open(signal_file, 'r', encoding='utf-8') as f:
            signal = json.load(f)
        
        symbol = signal.get('symbol', 'UNKNOWN')
        entry = signal.get('entry_price') or signal.get('entry')
        sl = signal.get('stop_loss') or signal.get('sl')
        
        # التعامل مع TP كقائمة أو قيمة واحدة
        tp_list = signal.get('take_profit', [])
        if not isinstance(tp_list, list):
            tp_list = [tp_list]
        
        if not tp_list:
            tp1 = signal.get('tp1')
            tp2 = signal.get('tp2')
            tp3 = signal.get('tp3')
            tp_list = [x for x in [tp1, tp2, tp3] if x]
        
        trade_type = signal.get('rec') or signal.get('trade_type', 'UNKNOWN')
        timestamp = signal.get('timestamp', 'UNKNOWN')
        
        if not entry or not sl or not tp_list:
            return None
        
        # تحديد اتجاه الصفقة
        is_buy = 'BUY' in str(trade_type).upper() or 'شراء' in str(trade_type)
        
        # جلب السعر الحالي
        current_price = get_current_price(symbol)
        
        if not current_price:
            return {
                'symbol': symbol,
                'status': '⚠️ لا يمكن جلب السعر',
                'entry': entry,
                'current': None,
                'timestamp': timestamp,
                'type': trade_type
            }
        
        # تحديد الحالة
        if is_buy:
            if current_price <= sl:
                status = '❌ خاسرة (وصل SL)'
                pnl = ((sl - entry) / entry) * 100
            elif current_price >= tp_list[0]:
                if len(tp_list) > 2 and current_price >= tp_list[2]:
                    status = '✅✅✅ رابحة (TP3)'
                    pnl = ((tp_list[2] - entry) / entry) * 100
                elif len(tp_list) > 1 and current_price >= tp_list[1]:
                    status = '✅✅ رابحة (TP2)'
                    pnl = ((tp_list[1] - entry) / entry) * 100
                else:
                    status = '✅ رابحة (TP1)'
                    pnl = ((tp_list[0] - entry) / entry) * 100
            else:
                status = '🔵 نشطة (شراء)'
                pnl = ((current_price - entry) / entry) * 100
        else:  # Sell
            if current_price >= sl:
                status = '❌ خاسرة (وصل SL)'
                pnl = ((entry - sl) / entry) * 100 * -1
            elif current_price <= tp_list[0]:
                if len(tp_list) > 2 and current_price <= tp_list[2]:
                    status = '✅✅✅ رابحة (TP3)'
                    pnl = ((entry - tp_list[2]) / entry) * 100
                elif len(tp_list) > 1 and current_price <= tp_list[1]:
                    status = '✅✅ رابحة (TP2)'
                    pnl = ((entry - tp_list[1]) / entry) * 100
                else:
                    status = '✅ رابحة (TP1)'
                    pnl = ((entry - tp_list[0]) / entry) * 100
            else:
                status = '🔵 نشطة (بيع)'
                pnl = ((entry - current_price) / entry) * 100
        
        return {
            'symbol': symbol,
            'status': status,
            'entry': entry,
            'current': current_price,
            'sl': sl,
            'tp': tp_list,
            'pnl': pnl,
            'timestamp': timestamp,
            'type': trade_type
        }
        
    except Exception as e:
        print(f"خطأ في فحص {signal_file}: {e}")
        return None

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           📊 مراجعة التوصيات المنشورة - تقرير شامل          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    signals_dir = "signals"
    
    if not os.path.exists(signals_dir):
        print("❌ مجلد الإشارات غير موجود!")
        return
    
    signal_files = [f for f in os.listdir(signals_dir) if f.endswith('.json')]
    
    if not signal_files:
        print("📭 لا توجد توصيات محفوظة")
        return
    
    print(f"🔍 جاري فحص {len(signal_files)} توصية...\n")
    
    results = {
        'winning': [],
        'losing': [],
        'active': [],
        'error': []
    }
    
    for signal_file in signal_files:
        file_path = os.path.join(signals_dir, signal_file)
        result = check_signal_status(file_path)
        
        if not result:
            continue
        
        if '✅' in result['status']:
            results['winning'].append(result)
        elif '❌' in result['status']:
            results['losing'].append(result)
        elif '🔵' in result['status']:
            results['active'].append(result)
        else:
            results['error'].append(result)
    
    # طباعة النتائج
    print(f"\n{'='*70}")
    print(f"📈 إحصائيات عامة:")
    print(f"{'='*70}")
    print(f"  إجمالي التوصيات: {len(signal_files)}")
    print(f"  ✅ رابحة: {len(results['winning'])}")
    print(f"  ❌ خاسرة: {len(results['losing'])}")
    print(f"  🔵 النشطة: {len(results['active'])}")
    print(f"  ⚠️  خطأ: {len(results['error'])}")
    
    if results['winning'] or results['losing']:
        total_trades = len(results['winning']) + len(results['losing'])
        win_rate = (len(results['winning']) / total_trades * 100) if total_trades > 0 else 0
        print(f"\n  🎯 نسبة النجاح: {win_rate:.1f}%")
    
    # التوصيات الرابحة
    if results['winning']:
        print(f"\n{'='*70}")
        print(f"✅ التوصيات الرابحة ({len(results['winning'])}):")
        print(f"{'='*70}")
        for r in results['winning']:
            print(f"\n  {r['symbol']:8s} | {r['status']}")
            print(f"    الدخول: {r['entry']:.5f} → الحالي: {r['current']:.5f}")
            print(f"    الربح: {r['pnl']:+.2f}%")
            print(f"    الوقت: {r['timestamp']}")
    
    # التوصيات الخاسرة
    if results['losing']:
        print(f"\n{'='*70}")
        print(f"❌ التوصيات الخاسرة ({len(results['losing'])}):")
        print(f"{'='*70}")
        for r in results['losing']:
            print(f"\n  {r['symbol']:8s} | {r['status']}")
            print(f"    الدخول: {r['entry']:.5f} → الحالي: {r['current']:.5f}")
            print(f"    الخسارة: {r['pnl']:+.2f}%")
            print(f"    الوقت: {r['timestamp']}")
    
    # التوصيات النشطة
    if results['active']:
        print(f"\n{'='*70}")
        print(f"🔵 التوصيات النشطة ({len(results['active'])}):")
        print(f"{'='*70}")
        for r in results['active']:
            print(f"\n  {r['symbol']:8s} | {r['status']}")
            print(f"    الدخول: {r['entry']:.5f} → الحالي: {r['current']:.5f}")
            print(f"    P/L: {r['pnl']:+.2f}%")
            print(f"    SL: {r['sl']:.5f} | TP1: {r['tp'][0]:.5f}")
            print(f"    الوقت: {r['timestamp']}")
    
    # التوصيات بخطأ
    if results['error']:
        print(f"\n{'='*70}")
        print(f"⚠️  توصيات لا يمكن فحصها ({len(results['error'])}):")
        print(f"{'='*70}")
        for r in results['error']:
            print(f"  {r['symbol']:8s} | {r['status']}")
    
    print(f"\n{'='*70}")
    print(f"✅ انتهى التقرير")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

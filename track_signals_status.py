# -*- coding: utf-8 -*-
"""
نظام تتبع حالة الصفقات - تحديد المنتهية والمستمرة
"""
import sqlite3
import yfinance as yf
from datetime import datetime

# خريطة رموز Yahoo Finance
# خريطة رموز Yahoo Finance - محدثة وشاملة
YF_SYMBOLS = {
    # FOREX Major
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'USDCAD': 'USDCAD=X',
    'NZDUSD': 'NZDUSD=X',
    'USDCHF': 'USDCHF=X',
    
    # FOREX Minor
    'EURGBP': 'EURGBP=X',
    'EURJPY': 'EURJPY=X',
    'GBPJPY': 'GBPJPY=X',
    'EURCHF': 'EURCHF=X',
    'AUDJPY': 'AUDJPY=X',
    'GBPAUD': 'GBPAUD=X',
    'EURAUD': 'EURAUD=X',
    'GBPCAD': 'GBPCAD=X',
    
    # FOREX Cross
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
    
    # Metals
    'XAUUSD': 'GC=F',
    'XAGUSD': 'SI=F',
    'XPTUSD': 'PL=F',
    'XPDUSD': 'PA=F',
    
    # US Indices
    'US30': '^DJI',
    'NAS100': '^IXIC',
    'SPX500': '^GSPC',
    'RUSSELL': '^RUT',
    'VIX': '^VIX',
    
    # Crypto
    'BTCUSD': 'BTC-USD',
    'ETHUSD': 'ETH-USD',
    'BNBUSD': 'BNB-USD',
    'XRPUSD': 'XRP-USD',
    'ADAUSD': 'ADA-USD',
    'SOLUSD': 'SOL-USD',
    'DOGEUSD': 'DOGE-USD',
    
    # Energy
    'CRUDE': 'CL=F',
    'BRENT': 'BZ=F',
    'NATGAS': 'NG=F',
    'HEATING': 'HO=F',
    'GASOLINE': 'RB=F',
}

def get_current_price(symbol):
    """جلب السعر الحالي من Yahoo Finance - محسّن"""
    try:
        yf_symbol = YF_SYMBOLS.get(symbol)
        if not yf_symbol:
            print(f"   ⚠️ رمز غير معروف: {symbol}")
            return None
        
        try:
            # محاولة بيانات المدة القصيرة أولاً
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period='1d')
            
            if data.empty:
                # محاولة فترة أطول
                data = ticker.history(period='5d')
            
            if data.empty:
                print(f"   ❌ لا توجد بيانات سعرية: {symbol}")
                return None
            
            price = float(data['Close'].iloc[-1])
            return price
        except Exception as e:
            print(f"   ❌ خطأ في جلب سعر {symbol}: {str(e)[:50]}")
            return None
    except Exception as e:
        print(f"   ❌ خطأ غير متوقع في {symbol}: {e}")
        return None

def check_trade_status(signal_id, symbol, signal_type, entry, sl, tp1, tp2, tp3, current_price):
    """فحص حالة الصفقة"""
    if current_price is None:
        return 'active', None, None
    
    # التحقق من وقف الخسارة
    if signal_type == 'buy':
        if current_price <= sl:
            return 'closed', 'loss', sl
        elif tp3 and current_price >= tp3:
            return 'closed', 'win', tp3
        elif tp2 and current_price >= tp2:
            return 'partial_win', 'win', tp2
        elif tp1 and current_price >= tp1:
            return 'partial_win', 'win', tp1
    else:  # sell
        if current_price >= sl:
            return 'closed', 'loss', sl
        elif tp3 and current_price <= tp3:
            return 'closed', 'win', tp3
        elif tp2 and current_price <= tp2:
            return 'partial_win', 'win', tp2
        elif tp1 and current_price <= tp1:
            return 'partial_win', 'win', tp1
    
    return 'active', None, None

def update_signals_status():
    """تحديث حالة جميع الصفقات"""
    print("🔄 بدء فحص وتحديث حالة الصفقات...\n")
    
    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    
    # التأكد من وجود الأعمدة المطلوبة
    c.execute("PRAGMA table_info(signals)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'result' not in columns:
        c.execute("ALTER TABLE signals ADD COLUMN result TEXT")
    if 'close_price' not in columns:
        c.execute("ALTER TABLE signals ADD COLUMN close_price REAL")
    if 'close_time' not in columns:
        c.execute("ALTER TABLE signals ADD COLUMN close_time TEXT")
    
    conn.commit()
    
    # جلب الإشارات النشطة
    c.execute('''
        SELECT id, signal_id, symbol, signal_type, entry_price, 
               stop_loss, take_profit_1, take_profit_2, take_profit_3,
               status, created_at
        FROM signals
        WHERE status IN ('active', 'partial_win') OR status IS NULL
        ORDER BY created_at DESC
    ''')
    
    signals = c.fetchall()
    
    print(f"📊 إجمالي الصفقات للفحص: {len(signals)}\n")
    print("=" * 90)
    
    active_count = 0
    closed_count = 0
    partial_win_count = 0
    
    for sig in signals:
        id, sig_id, symbol, sig_type, entry, sl, tp1, tp2, tp3, status, created = sig
        
        # جلب السعر الحالي
        current_price = get_current_price(symbol)
        
        if current_price is None:
            print(f"⚠️  {symbol:10} - لا يمكن جلب السعر")
            continue
        
        # فحص الحالة
        new_status, result, close_price = check_trade_status(
            sig_id, symbol, sig_type, entry, sl, tp1, tp2, tp3, current_price
        )
        
        # حساب الربح/الخسارة بالنقاط
        if sig_type == 'buy':
            pips = (current_price - entry) * 10000 if symbol in ['EURUSD', 'GBPUSD', 'AUDUSD'] else (current_price - entry)
        else:
            pips = (entry - current_price) * 10000 if symbol in ['EURUSD', 'GBPUSD', 'AUDUSD'] else (entry - current_price)
        
        # عرض الحالة
        direction = '🟢' if sig_type == 'buy' else '🔴'
        status_emoji = '✅' if new_status == 'closed' and result == 'win' else '❌' if new_status == 'closed' and result == 'loss' else '⏳' if new_status == 'active' else '🎯'
        
        print(f"{status_emoji} {direction} {symbol:10} | الدخول: {entry:>10.5f} | الحالي: {current_price:>10.5f} | النقاط: {pips:>8.1f}")
        
        # تحديث قاعدة البيانات
        if new_status != status:
            update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if new_status in ['closed', 'partial_win']:
                c.execute('''
                    UPDATE signals 
                    SET status = ?, result = ?, close_price = ?, close_time = ?
                    WHERE id = ?
                ''', (new_status, result, close_price, update_time, id))
            else:
                c.execute('''
                    UPDATE signals 
                    SET status = ?
                    WHERE id = ?
                ''', (new_status, id))
            
            conn.commit()
            print(f"  ↳ تم التحديث: {status or 'new'} → {new_status}")
        
        if new_status == 'active':
            active_count += 1
        elif new_status == 'closed':
            closed_count += 1
        elif new_status == 'partial_win':
            partial_win_count += 1
    
    print("=" * 90)
    print(f"\n📊 ملخص الحالة:")
    print(f"  ⏳ صفقات نشطة: {active_count}")
    print(f"  🎯 صفقات في ربح جزئي: {partial_win_count}")
    print(f"  ✅ صفقات منتهية: {closed_count}")
    
    conn.close()
    print("\n✅ اكتمل التحديث!")

def show_status_report():
    """عرض تقرير شامل لحالة الصفقات"""
    print("\n" + "=" * 90)
    print("📋 تقرير حالة الصفقات")
    print("=" * 90)
    
    conn = sqlite3.connect('vip_signals.db')
    c = conn.cursor()
    
    # الصفقات النشطة
    print("\n⏳ الصفقات النشطة:")
    print("-" * 90)
    c.execute('''
        SELECT symbol, signal_type, entry_price, stop_loss, take_profit_1, 
               quality_score, created_at
        FROM signals
        WHERE status = 'active'
        ORDER BY created_at DESC
    ''')
    active = c.fetchall()
    
    if active:
        for sym, sig, entry, sl, tp1, quality, time in active:
            direction = '🟢 شراء' if sig == 'buy' else '🔴 بيع'
            print(f"{direction} {sym:10} | الدخول: {entry:>10.5f} | SL: {sl:>10.5f} | TP1: {tp1:>10.5f} | {time[:16]}")
    else:
        print("لا توجد صفقات نشطة")
    
    # الصفقات في ربح جزئي
    print("\n🎯 الصفقات في ربح جزئي:")
    print("-" * 90)
    c.execute('''
        SELECT symbol, signal_type, entry_price, close_price, created_at
        FROM signals
        WHERE status = 'partial_win'
        ORDER BY created_at DESC
    ''')
    partial = c.fetchall()
    
    if partial:
        for sym, sig, entry, close, time in partial:
            direction = '🟢 شراء' if sig == 'buy' else '🔴 بيع'
            print(f"{direction} {sym:10} | الدخول: {entry:>10.5f} | الإغلاق: {close:>10.5f} | {time[:16]}")
    else:
        print("لا توجد صفقات في ربح جزئي")
    
    # الصفقات المنتهية
    print("\n✅ الصفقات المنتهية:")
    print("-" * 90)
    c.execute('''
        SELECT symbol, signal_type, entry_price, close_price, result, close_time
        FROM signals
        WHERE status = 'closed'
        ORDER BY close_time DESC
        LIMIT 10
    ''')
    closed = c.fetchall()
    
    if closed:
        for sym, sig, entry, close, result, time in closed:
            direction = '🟢 شراء' if sig == 'buy' else '🔴 بيع'
            result_emoji = '✅ ربح' if result == 'win' else '❌ خسارة'
            print(f"{result_emoji} {direction} {sym:10} | الدخول: {entry:>10.5f} | الإغلاق: {close:>10.5f} | {time[:16] if time else 'N/A'}")
    else:
        print("لا توجد صفقات منتهية")
    
    # إحصائيات
    print("\n📊 الإحصائيات الإجمالية:")
    print("-" * 90)
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'active'")
    active_total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND result = 'win'")
    wins = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed' AND result = 'loss'")
    losses = c.fetchone()[0]
    
    total_closed = wins + losses
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
    
    print(f"⏳ صفقات نشطة: {active_total}")
    print(f"✅ صفقات رابحة: {wins}")
    print(f"❌ صفقات خاسرة: {losses}")
    print(f"📈 نسبة النجاح: {win_rate:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    update_signals_status()
    show_status_report()

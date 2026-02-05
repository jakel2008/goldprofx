"""
اختبار عرض الأرقام بوضوح على صفحة الإشارات
تحسين حجم الخطوط والألوان
"""

import sqlite3
import yfinance as yf
from datetime import datetime

# خريطة رموز Yahoo Finance
YF_SYMBOLS = {
    'XAUUSD': 'GC=F',
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'BTCUSD': 'BTC-USD'
}

print("=" * 70)
print("🔍 اختبار عرض الأرقام بوضوح على صفحة الإشارات")
print("=" * 70)
print()

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('vip_signals.db')
c = conn.cursor()

# جلب الإشارات النشطة
c.execute("""
    SELECT symbol, signal_type, entry_price, stop_loss, take_profit_1, 
           take_profit_2, take_profit_3, quality_score, status
    FROM signals 
    WHERE status = 'active'
    ORDER BY created_at DESC 
    LIMIT 5
""")

active_signals = c.fetchall()
conn.close()

if not active_signals:
    print("⚠️ لا توجد إشارات نشطة حالياً")
else:
    print(f"✅ تم العثور على {len(active_signals)} إشارة نشطة\n")
    
    for signal in active_signals:
        symbol, signal_type, entry_price, sl, tp1, tp2, tp3, quality, status = signal
        
        print("=" * 70)
        print(f"{'🟢' if signal_type == 'buy' else '🔴'} {symbol} - {'شراء' if signal_type == 'buy' else 'بيع'}")
        print("=" * 70)
        
        # جلب السعر الحالي من Yahoo Finance
        yf_symbol = YF_SYMBOLS.get(symbol)
        
        if yf_symbol:
            try:
                ticker = yf.Ticker(yf_symbol)
                hist = ticker.history(period='1d', interval='5m')
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    # حساب النقاط
                    if signal_type == 'buy':
                        pips = current_price - entry_price
                    else:
                        pips = entry_price - current_price
                    
                    # حساب التقدم نحو الهدف الأول
                    if tp1:
                        if signal_type == 'buy':
                            total_range = tp1 - entry_price
                        else:
                            total_range = entry_price - tp1
                        
                        if total_range > 0:
                            progress = int((pips / total_range) * 100)
                        else:
                            progress = 0
                    else:
                        progress = 0
                    
                    # عرض الأرقام بخطوط كبيرة
                    print()
                    print("┌─────────────────────────────────────────┐")
                    print("│          💰 سعر الدخول                  │")
                    print(f"│      {entry_price:>12.5f}                  │")
                    print("└─────────────────────────────────────────┘")
                    print()
                    print("              {'⬆️' if pips > 0 else '⬇️'}")
                    print()
                    print("┌─────────────────────────────────────────┐")
                    print("│          📈 السعر الحالي                │")
                    print(f"│      {current_price:>12.5f}                  │")
                    print("└─────────────────────────────────────────┘")
                    print()
                    print("┌─────────────────────────────────────────┐")
                    print("│         الربح/الخسارة                   │")
                    print(f"│      {'+' if pips > 0 else ''}{pips:>10.2f} نقطة            │")
                    print("└─────────────────────────────────────────┘")
                    print()
                    
                    if progress > 0:
                        print(f"🎯 التقدم نحو الهدف الأول: {progress}%")
                        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
                        print(f"   [{progress_bar}] {progress}%")
                    
                    print()
                    
                else:
                    print("⚠️ لا توجد بيانات سعرية حالية")
                    
            except Exception as e:
                print(f"❌ خطأ في جلب السعر: {str(e)}")
        else:
            print(f"⚠️ رمز Yahoo Finance غير متوفر لـ {symbol}")
        
        print()

print("=" * 70)
print("✅ انتهى الاختبار")
print()
print("📌 التحسينات المطبقة:")
print("   1. حجم الخط للأسعار: 42px (كبير جداً)")
print("   2. حجم خط النقاط: 48px (أكبر)")
print("   3. الأرقام بخط سميك 900 (الأسمك)")
print("   4. حدود بيضاء سميكة 4px")
print("   5. ظلال قوية للأسعار")
print("   6. تأثير وميض للسعر الحالي")
print("   7. أسهم كبيرة 60px")
print("=" * 70)

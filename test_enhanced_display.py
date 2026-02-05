"""
اختبار عرض الأسعار الحالية المحسّن
Test Enhanced Current Price Display
"""

import sqlite3
from datetime import datetime
import yfinance as yf

# خريطة الرموز
YF_SYMBOLS = {
    'XAUUSD': 'GC=F',
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X',
    'BTCUSD': 'BTC-USD'
}

def test_price_display():
    """اختبار عرض الأسعار مع التنسيق المحسّن"""
    
    print("=" * 80)
    print("🎨 اختبار العرض المحسّن للأسعار الحالية")
    print("=" * 80)
    print()
    
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # جلب الإشارات النشطة
        c.execute('''
            SELECT * FROM signals 
            WHERE status = 'active' 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        rows = c.fetchall()
        
        if not rows:
            print("⚠️  لا توجد إشارات نشطة")
            return
        
        print(f"📊 عدد الإشارات النشطة: {len(rows)}")
        print("=" * 80)
        
        for row in rows:
            symbol = row['symbol']
            signal_type = row['signal_type']
            entry = row['entry_price']
            tp1 = row['take_profit_1']
            
            print(f"\n{'🟢' if signal_type == 'buy' else '🔴'} {symbol} - {signal_type.upper()}")
            print("-" * 80)
            
            # جلب السعر الحالي
            if symbol in YF_SYMBOLS:
                try:
                    ticker = yf.Ticker(YF_SYMBOLS[symbol])
                    hist = ticker.history(period='1d', interval='5m')
                    
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
                        
                        # حساب النقاط
                        if signal_type == 'buy':
                            pips = current_price - entry
                            total_range = tp1 - entry
                        else:
                            pips = entry - current_price
                            total_range = entry - tp1
                        
                        # حساب التقدم
                        progress = int((pips / total_range) * 100) if total_range > 0 else 0
                        
                        print(f"   💰 سعر الدخول:  {entry:.5f}")
                        print(f"   📈 السعر الحالي: {current_price:.5f}")
                        print()
                        
                        # عرض النقاط بتنسيق محسّن
                        if pips > 0:
                            print(f"   ✅ الربح: +{pips:.2f} نقطة")
                            print(f"   {'█' * min(int(pips * 10), 50)}")
                        else:
                            print(f"   ❌ الخسارة: {pips:.2f} نقطة")
                            print(f"   {'▓' * min(int(abs(pips) * 10), 50)}")
                        
                        print()
                        
                        # عرض شريط التقدم
                        if progress > 0:
                            bar_length = 50
                            filled = int((progress / 100) * bar_length)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f"   🎯 التقدم نحو الهدف الأول: {progress}%")
                            print(f"   [{bar}]")
                        
                        print()
                        print(f"   🎯 الهدف الأول: {tp1:.5f}")
                        
                        # حساب المسافة المتبقية
                        if signal_type == 'buy':
                            remaining = tp1 - current_price
                        else:
                            remaining = current_price - tp1
                        
                        print(f"   📏 المسافة المتبقية: {remaining:.5f}")
                        
                    else:
                        print(f"   ⚠️  لا توجد بيانات سعرية")
                        
                except Exception as e:
                    print(f"   ❌ خطأ في جلب السعر: {e}")
            else:
                print(f"   ⚠️  الرمز غير مدعوم في Yahoo Finance")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("✨ التحسينات الجديدة في صفحة الويب:")
        print("=" * 80)
        print("  1. 🎨 قسم مقارنة الأسعار (الدخول ↔️ الحالي)")
        print("  2. ⬆️ سهم متحرك يوضح الاتجاه")
        print("  3. 💰 عرض النقاط بحجم كبير وألوان واضحة")
        print("  4. 📊 شريط تقدم متحرك بتدرج ملون")
        print("  5. ⚡ أيقونة متحركة في الخلفية")
        print("  6. ✨ تأثيرات نبض وإضاءة للأرباح")
        print("  7. 🔴 تأثير اهتزاز للخسائر")
        print()
        print("🚀 لمشاهدة التحسينات:")
        print("   python web_app.py")
        print("   ثم افتح: http://localhost:5000/signals")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_price_display()

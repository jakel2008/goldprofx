# -*- coding: utf-8 -*-
"""
توليد إشارات جديدة بأسعار حقيقية من السوق
"""
import yfinance as yf
import sqlite3
from datetime import datetime
import random

print("🔄 توليد إشارات جديدة بأسعار حية...\n")

# حذف جميع الإشارات القديمة
conn = sqlite3.connect('vip_signals.db')
c = conn.cursor()
c.execute('DELETE FROM signals')
conn.commit()
print("🧹 تم حذف الإشارات القديمة\n")

# خريطة الأزواج
pairs_map = {
    'EURUSD=X': {'name': 'EURUSD', 'pip': 0.0001},
    'GBPUSD=X': {'name': 'GBPUSD', 'pip': 0.0001},
    'GC=F': {'name': 'XAUUSD', 'pip': 0.1},
    'BTC-USD': {'name': 'BTCUSD', 'pip': 1.0},
    'USDJPY=X': {'name': 'USDJPY', 'pip': 0.01},
    'AUDUSD=X': {'name': 'AUDUSD', 'pip': 0.0001}
}

signals_created = 0

for yahoo_symbol, info in pairs_map.items():
    try:
        # جلب السعر الحالي
        ticker = yf.Ticker(yahoo_symbol)
        data = ticker.history(period='1d', interval='5m')
        
        if data.empty:
            print(f"❌ {info['name']}: لا توجد بيانات")
            continue
        
        current_price = float(data['Close'].iloc[-1])
        pip = info['pip']
        
        # تحديد اتجاه الإشارة (عشوائي للتجربة)
        signal_type = random.choice(['buy', 'sell'])
        
        # حساب مستويات الدخول والخروج
        if signal_type == 'buy':
            entry = current_price
            sl = entry - (30 * pip)
            tp1 = entry + (50 * pip)
            tp2 = entry + (100 * pip)
            tp3 = entry + (150 * pip)
        else:  # sell
            entry = current_price
            sl = entry + (30 * pip)
            tp1 = entry - (50 * pip)
            tp2 = entry - (100 * pip)
            tp3 = entry - (150 * pip)
        
        # جودة عشوائية واقعية
        quality = random.randint(75, 95)
        
        # فحص وإغلاق الصفقات المعاكسة النشطة التي وصلت TP1 أو أكثر
        try:
            c.execute('''
                SELECT signal_id, signal_type 
                FROM signals 
                WHERE symbol=? AND status='active' AND result='win'
            ''', (info['name'],))
            
            existing_signals = c.fetchall()
            for existing in existing_signals:
                existing_type = existing[1]
                # فحص إذا كانت الصفقة معاكسة
                if (signal_type == 'buy' and existing_type.lower() == 'sell') or \
                   (signal_type == 'sell' and existing_type.lower() == 'buy'):
                    # إغلاق الصفقة المعاكسة
                    c.execute('''
                        UPDATE signals 
                        SET status='closed' 
                        WHERE signal_id=?
                    ''', (existing[0],))
                    print(f"  🔄 إغلاق صفقة {existing_type} معاكسة للصفقة الجديدة")
        except Exception as e:
            pass
        
        # حفظ الإشارة
        signal_id = f"{info['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute('''
            INSERT INTO signals 
            (signal_id, symbol, signal_type, entry_price, stop_loss, 
             take_profit_1, take_profit_2, take_profit_3, 
             quality_score, timeframe, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (signal_id, info['name'], signal_type, entry, sl, 
              tp1, tp2, tp3, quality, '5m', 'active', timestamp))
        
        conn.commit()
        signals_created += 1
        
        print(f"✅ {info['name']:10} {signal_type.upper():4} - السعر: {entry:>12.5f} - الجودة: {quality}/100")
        
    except Exception as e:
        print(f"❌ {info.get('name', yahoo_symbol)}: خطأ - {e}")

conn.close()

print(f"\n✅ تم توليد {signals_created} إشارة جديدة بأسعار حية!")
print(f"📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n🌐 افتح المتصفح: http://localhost:5000/signals")

"""
تطبيق ويب بسيط لعرض إشارات التداول
نسخة مبسطة بدون تحديث حي للأسعار
"""

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# تعطيل التخزين المؤقت
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.route('/')
def index():
    """الصفحة الرئيسية"""
    signal_list = load_signals()
    return render_template('signals.html', signals=signal_list)


@app.route('/signals')
def signals_page():
    """صفحة عرض الإشارات"""
    signal_list = load_signals()
    return render_template('signals.html', signals=signal_list)


def load_signals():
    """تحميل الإشارات من قاعدة البيانات"""
    signals = []
    
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # جلب إشارات اليوم
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT signal_id, symbol, signal_type, entry_price, stop_loss,
                   take_profit_1, take_profit_2, take_profit_3,
                   status, result, quality_score, timestamp, timeframe,
                   tp1_locked, tp2_locked, tp3_locked, activated, current_price,
                   created_at
            FROM signals
            WHERE DATE(created_at) = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (today,))
        
        rows = c.fetchall()
        
        for row in rows:
            symbol = row['symbol']
            signal_type = row['signal_type']
            entry = row['entry_price']
            sl = row['stop_loss']
            tp1 = row['take_profit_1']
            tp2 = row['take_profit_2']
            tp3 = row['take_profit_3']
            status = row['status']
            result = row['result'] if row['result'] else 'pending'
            quality_score = row['quality_score']
            timestamp = row['timestamp']
            timeframe = row['timeframe'] if 'timeframe' in row.keys() else 'H1'
            
            # حقول القفل والتفعيل
            activated = row['activated'] if 'activated' in row.keys() else 0
            tp1_locked = row['tp1_locked'] if 'tp1_locked' in row.keys() else 0
            tp2_locked = row['tp2_locked'] if 'tp2_locked' in row.keys() else 0
            tp3_locked = row['tp3_locked'] if 'tp3_locked' in row.keys() else 0
            
            # السعر الحالي - استخدام السعر المحفوظ أو سعر الدخول
            current_price = row['current_price'] if row['current_price'] else entry
            
            # حساب النقاط والتقدم
            pips = 0
            progress = 0
            tp_levels_hit = 0
            
            if status == 'active':
                if signal_type == 'buy':
                    pips = current_price - entry
                    total_range = tp1 - entry
                else:
                    pips = entry - current_price
                    total_range = entry - tp1
                
                if total_range > 0:
                    progress = int((pips / total_range) * 100)
                
                # عدد الأهداف المحققة
                tp_levels_hit = tp1_locked + tp2_locked + tp3_locked
            
            signals.append({
                'signal_id': row['signal_id'],
                'pair': symbol,
                'symbol': symbol,
                'signal': signal_type,
                'signal_type': signal_type,
                'rec': signal_type.upper(),
                'entry': entry,
                'entry_price': entry,
                'sl': sl,
                'stop_loss': sl,
                'tp1': tp1,
                'tp2': tp2,
                'tp3': tp3,
                'take_profit_1': tp1,
                'take_profit_2': tp2,
                'take_profit_3': tp3,
                'status': status,
                'result': result,
                'quality_score': quality_score,
                'timestamp': timestamp,
                'timeframe': timeframe,
                'current_price': current_price,
                'pips': round(pips, 2),
                'progress': max(0, progress),
                'tp_levels_hit': tp_levels_hit,
                'tp1_locked': tp1_locked,
                'tp2_locked': tp2_locked,
                'tp3_locked': tp3_locked,
                'activated': activated
            })
        
        conn.close()
        
    except Exception as e:
        print(f"خطأ في تحميل الإشارات: {e}")
    
    return signals


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 بدء تشغيل موقع عرض الإشارات")
    print("=" * 60)
    print(f"📍 الرابط: http://localhost:5000")
    print(f"📍 صفحة الإشارات: http://localhost:5000/signals")
    print("=" * 60)
    print("ℹ️  ملاحظة: هذه نسخة مبسطة بدون تحديث حي للأسعار")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

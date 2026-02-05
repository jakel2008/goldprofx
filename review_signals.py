# -*- coding: utf-8 -*-
"""
مراجعة سريعة للتوصيات المنشورة - بدون فحص الأسعار الحية
"""

import os
import json
from datetime import datetime

os.system('chcp 65001 > nul')

def review_signals():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         📋 مراجعة التوصيات المنشورة - نظرة عامة             ║
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
    
    print(f"📊 إجمالي التوصيات: {len(signal_files)}\n")
    print(f"{'='*80}")
    
    for idx, signal_file in enumerate(signal_files, 1):
        file_path = os.path.join(signals_dir, signal_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                signal = json.load(f)
            
            symbol = signal.get('symbol', 'UNKNOWN')
            entry = signal.get('entry_price') or signal.get('entry')
            sl = signal.get('stop_loss') or signal.get('sl')
            
            # التعامل مع TP
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
            confidence = signal.get('confidence', 'N/A')
            
            # تحديد اتجاه الصفقة
            if 'BUY' in str(trade_type).upper() or 'شراء' in str(trade_type):
                direction = "🟢 شراء"
            elif 'SELL' in str(trade_type).upper() or 'بيع' in str(trade_type):
                direction = "🔴 بيع"
            else:
                direction = "⚪ غير محدد"
            
            # حساب RR Ratio
            if entry and sl and tp_list and len(tp_list) > 0:
                risk = abs(entry - sl)
                reward = abs(tp_list[0] - entry)
                rr_ratio = reward / risk if risk > 0 else 0
            else:
                rr_ratio = 0
            
            print(f"\n📌 توصية #{idx}: {symbol}")
            print(f"{'─'*80}")
            print(f"  الاتجاه: {direction}")
            print(f"  الدخول: {entry}")
            print(f"  وقف الخسارة: {sl}")
            
            if tp_list:
                print(f"  أهداف الربح:")
                for i, tp in enumerate(tp_list, 1):
                    print(f"    TP{i}: {tp}")
            
            print(f"  نسبة R:R: {rr_ratio:.2f}:1" if rr_ratio > 0 else "  نسبة R:R: غير محسوبة")
            print(f"  الثقة: {confidence}")
            print(f"  التوقيت: {timestamp}")
            print(f"  الملف: {signal_file}")
            
        except Exception as e:
            print(f"\n⚠️  خطأ في قراءة {signal_file}: {e}")
    
    print(f"\n{'='*80}")
    print(f"✅ انتهت المراجعة\n")
    
    # قراءة active_trades.json
    print(f"\n{'='*80}")
    print("📁 الصفقات المسجلة في active_trades.json:")
    print(f"{'='*80}\n")
    
    try:
        if os.path.exists("active_trades.json"):
            with open("active_trades.json", 'r', encoding='utf-8') as f:
                active_trades = json.load(f)
            
            print(f"إجمالي معرفات الصفقات المحفوظة: {len(active_trades)}")
            
            if active_trades:
                print("\nآخر 10 صفقات:")
                for trade_id in active_trades[-10:]:
                    print(f"  • {trade_id}")
        else:
            print("❌ ملف active_trades.json غير موجود")
    except Exception as e:
        print(f"⚠️  خطأ في قراءة active_trades.json: {e}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    review_signals()

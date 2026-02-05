#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار النظام المحسّن
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from auto_pairs_analyzer import analyze_pair_5m

print("="*80)
print("🧪 اختبار النظام المحسّن")
print("="*80)
print()

pairs = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD', 'USDJPY']

for pair in pairs:
    print(f"📊 تحليل {pair}...")
    print("-"*80)
    
    try:
        analysis = analyze_pair_5m(pair)
        
        if analysis:
            print(f"✅ توصية: {analysis['recommendation']}")
            print(f"السعر: {analysis['close_price']:.5f}")
            print(f"RSI: {analysis['rsi']:.2f}")
            print(f"MACD: {analysis['macd']:.5f}")
            print(f"الاتجاه: {analysis.get('trend', 'N/A')}")
            
            if analysis.get('entry'):
                print(f"\n📈 مناطق التداول:")
                print(f"  الدخول: {analysis['entry']:.5f}")
                print(f"  SL: {analysis['stop_loss']:.5f}")
                print(f"  TP1: {analysis['take_profit']:.5f}")
                print(f"  TP2: {analysis['take_profit_2']:.5f}")
                print(f"  TP3: {analysis['take_profit_3']:.5f}")
                
                # حساب RR ratio
                sl_distance = abs(analysis['entry'] - analysis['stop_loss'])
                tp1_distance = abs(analysis['take_profit'] - analysis['entry'])
                rr_ratio = tp1_distance / sl_distance if sl_distance > 0 else 0
                
                print(f"\n  💰 نسبة المخاطرة/العائد: 1:{rr_ratio:.2f}")
                
                if rr_ratio >= 2:
                    print(f"  ✅ RR ratio ممتاز")
                else:
                    print(f"  ⚠️ RR ratio ضعيف")
                    
            if analysis.get('signals'):
                print(f"\n⚡ الإشارات:")
                for signal in analysis['signals']:
                    print(f"  • {signal}")
        else:
            print("⏸️ لا توجد توصية (لم تتحقق الشروط)")
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
    
    print()
    print("="*80)
    print()

print("\n✅ اكتمل الاختبار")
print("\n📝 ملاحظة: النظام المحسّن:")
print("  • يشترط RSI > 75 أو < 25 (بدلاً من 70/30)")
print("  • يتحقق من MACD crossover")
print("  • يشترط اتجاه واضح (EMA 20 vs 50)")
print("  • RR ratio محسّن (2:1 على الأقل)")
print("  • Stop Loss أضيق (1.2 ATR بدلاً من 1.5)")
print("  • يُلغي الصفقات ذات الأهداف البعيدة جداً")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار مفصل للنظام
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("اختبار التحليل الكامل")
print("="*70)
print()

try:
    from auto_pairs_analyzer import analyze_pair_5m, generate_pair_report
    
    # الأزواج للاختبار
    pairs = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    for pair in pairs:
        print(f"تحليل {pair}...")
        print("-"*70)
        
        try:
            analysis = analyze_pair_5m(pair)
            
            if analysis:
                # عرض التحليل الكامل
                print(f"✅ نجح التحليل!")
                print(f"الرمز: {analysis['symbol']}")
                print(f"السعر: {analysis.get('close_price', 0):.5f}")
                print(f"RSI: {analysis.get('rsi', 0):.2f}")
                print(f"MACD: {analysis.get('macd', 0):.5f}")
                print(f"التوصية: {analysis.get('recommendation', 'N/A')}")
                
                # التحقق من نقاط أخذ الربح
                print()
                print("نقاط أخذ الربح:")
                
                if analysis.get('entry'):
                    print(f"  الدخول: {analysis['entry']:.5f}")
                
                if analysis.get('stop_loss'):
                    print(f"  SL: {analysis['stop_loss']:.5f}")
                
                if analysis.get('take_profit'):
                    print(f"  TP1: {analysis['take_profit']:.5f} ✅")
                else:
                    print(f"  TP1: غير موجود ❌")
                
                if analysis.get('take_profit_2'):
                    print(f"  TP2: {analysis['take_profit_2']:.5f} ✅")
                else:
                    print(f"  TP2: غير موجود ❌")
                
                if analysis.get('take_profit_3'):
                    print(f"  TP3: {analysis['take_profit_3']:.5f} ✅")
                else:
                    print(f"  TP3: غير موجود ❌")
                
                # عرض التقرير
                print()
                print("التقرير:")
                print("-"*70)
                report = generate_pair_report(analysis)
                if report:
                    print(report)
                else:
                    print("فشل في توليد التقرير")
                    
            else:
                print(f"❌ فشل التحليل - لا توجد بيانات")
                
        except Exception as e:
            print(f"❌ خطأ في تحليل {pair}: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        print("="*70)
        print()

except Exception as e:
    print(f"خطأ في استيراد الوحدة: {e}")
    import traceback
    traceback.print_exc()

print()
print("✅ انتهى الاختبار!")

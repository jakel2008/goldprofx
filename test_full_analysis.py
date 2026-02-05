#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار كامل للنظام مع 3 نقاط أخذ ربح
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from auto_pairs_analyzer import analyze_pair_5m, generate_pair_report, save_trade
import json

print("="*70)
print("اختبار التحليل الكامل مع 3 نقاط أخذ ربح")
print("="*70)
print()

# اختبار زوج واحد
print("1️⃣ اختبار تحليل زوج EURUSD...")
print("-"*70)

analysis = analyze_pair_5m('EURUSD')

if analysis:
    print(f"✅ تم التحليل بنجاح!")
    print(f"الزوج: {analysis['symbol']}")
    print(f"التوصية: {analysis['recommendation']}")
    print(f"السعر الحالي: {analysis['current_price']:.5f}")
    print(f"نقطة الدخول: {analysis['entry']:.5f}")
    print(f"وقف الخسارة: {analysis['stop_loss']:.5f}")
    print()
    print("📊 نقاط أخذ الربح:")
    print(f"  TP1 (الهدف الأول): {analysis['take_profit']:.5f}")
    
    if 'take_profit_2' in analysis and analysis['take_profit_2']:
        print(f"  TP2 (الهدف الثاني): {analysis['take_profit_2']:.5f}")
    else:
        print("  ⚠️ TP2 غير موجود!")
    
    if 'take_profit_3' in analysis and analysis['take_profit_3']:
        print(f"  TP3 (الهدف الثالث): {analysis['take_profit_3']:.5f}")
    else:
        print("  ⚠️ TP3 غير موجود!")
    
    print()
    print("-"*70)
    print("2️⃣ اختبار توليد التقرير...")
    print("-"*70)
    
    report = generate_pair_report(analysis)
    print(report)
    
    print()
    print("-"*70)
    print("3️⃣ اختبار حفظ الصفقة...")
    print("-"*70)
    
    # حفظ الصفقة
    save_trade(
        analysis['symbol'],
        analysis['recommendation'],
        analysis['entry'],
        analysis['stop_loss'],
        analysis['take_profit'],
        analysis.get('take_profit_2'),
        analysis.get('take_profit_3')
    )
    
    print("✅ تم حفظ الصفقة بنجاح!")
    
    # قراءة وعرض الصفقة المحفوظة
    with open('active_trades.json', 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    # عرض آخر صفقة
    last_trade_id = list(trades.keys())[-1]
    last_trade = trades[last_trade_id]
    
    print()
    print(f"الصفقة المحفوظة: {last_trade_id}")
    print(f"  الزوج: {last_trade['symbol']}")
    print(f"  التوصية: {last_trade['recommendation']}")
    print(f"  الدخول: {last_trade['entry']:.5f}")
    print(f"  SL: {last_trade['stop_loss']:.5f}")
    print(f"  TP1: {last_trade['take_profit']:.5f}")
    
    if 'take_profit_2' in last_trade and last_trade['take_profit_2']:
        print(f"  TP2: {last_trade['take_profit_2']:.5f}")
        print("  ✅ TP2 محفوظ بنجاح!")
    else:
        print("  ❌ TP2 غير محفوظ!")
    
    if 'take_profit_3' in last_trade and last_trade['take_profit_3']:
        print(f"  TP3: {last_trade['take_profit_3']:.5f}")
        print("  ✅ TP3 محفوظ بنجاح!")
    else:
        print("  ❌ TP3 غير محفوظ!")
    
else:
    print("❌ فشل التحليل!")

print()
print("="*70)
print("✅ اكتمل الاختبار!")
print("="*70)

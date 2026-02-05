#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار إرسال التوصيات على البوت
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from auto_pairs_analyzer import run_hourly_5min_analysis
import json
import os

print("="*70)
print("اختبار إرسال التوصيات على Telegram Bot")
print("="*70)
print()

# حذف الصفقات القديمة للاختبار النظيف
if os.path.exists('active_trades.json'):
    with open('active_trades.json', 'r', encoding='utf-8') as f:
        old_trades = json.load(f)
    print(f"⚠️ يوجد {len(old_trades)} صفقات قديمة")
    print("🗑️ سيتم مسحها للاختبار...")
    os.remove('active_trades.json')
    print("✅ تم المسح!")
    print()

print("🚀 جاري تشغيل التحليل وإرسال التوصيات...")
print("-"*70)
print()

try:
    # تشغيل التحليل الكامل
    run_hourly_5min_analysis()
    
    print()
    print("="*70)
    print("✅ اكتمل التحليل والإرسال!")
    print("="*70)
    print()
    
    # التحقق من الصفقات المحفوظة
    if os.path.exists('active_trades.json'):
        with open('active_trades.json', 'r', encoding='utf-8') as f:
            trades = json.load(f)
        
        print(f"📊 عدد الصفقات المحفوظة: {len(trades)}")
        print()
        
        # عرض كل صفقة
        for i, (trade_id, trade) in enumerate(trades.items(), 1):
            print(f"الصفقة #{i}: {trade_id}")
            print(f"  الزوج: {trade['symbol']}")
            print(f"  التوصية: {trade['recommendation']}")
            print(f"  الدخول: {trade['entry']:.5f}")
            print(f"  SL: {trade['stop_loss']:.5f}")
            print(f"  TP1: {trade['take_profit']:.5f}")
            
            # التحقق من TP2 و TP3
            has_tp2 = 'take_profit_2' in trade and trade['take_profit_2'] is not None
            has_tp3 = 'take_profit_3' in trade and trade['take_profit_3'] is not None
            
            if has_tp2:
                print(f"  TP2: {trade['take_profit_2']:.5f} ✅")
            else:
                print(f"  TP2: غير موجود ❌")
            
            if has_tp3:
                print(f"  TP3: {trade['take_profit_3']:.5f} ✅")
            else:
                print(f"  TP3: غير موجود ❌")
            
            print(f"  الحالة: {trade['status']}")
            print(f"  الوقت: {trade['open_time']}")
            
            # إحصائيات
            if has_tp2 and has_tp3:
                print("  ✅ الصفقة تحتوي على 3 نقاط أخذ ربح كاملة!")
            else:
                print("  ⚠️ الصفقة لا تحتوي على 3 نقاط أخذ ربح!")
            
            print("-"*70)
        
        # إحصائيات نهائية
        trades_with_3tp = sum(1 for t in trades.values() 
                              if 'take_profit_2' in t and t['take_profit_2'] 
                              and 'take_profit_3' in t and t['take_profit_3'])
        
        print()
        print(f"📊 الإحصائيات:")
        print(f"  إجمالي الصفقات: {len(trades)}")
        print(f"  الصفقات بـ 3 نقاط: {trades_with_3tp}")
        print(f"  النسبة: {trades_with_3tp/len(trades)*100:.1f}%")
        
        if trades_with_3tp == len(trades):
            print()
            print("✅ جميع الصفقات تحتوي على 3 نقاط أخذ ربح!")
        else:
            print()
            print("⚠️ بعض الصفقات لا تحتوي على 3 نقاط أخذ ربح!")
    else:
        print("❌ لم يتم حفظ أي صفقات!")
        
except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("تأكد من البوت على Telegram:")
print("https://t.me/YourBotName")
print("="*70)

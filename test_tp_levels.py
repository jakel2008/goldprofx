#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اختبار التوصيات الجديدة مع 3 نقاط أخذ الربح
"""

import sys
sys.path.insert(0, 'd:\\GOLD PRO')

from auto_pairs_analyzer import analyze_pair_5m, generate_pair_report

print('=' * 70)
print('اختبار التوصيات الجديدة - 3 نقاط أخذ الربح')
print('=' * 70)
print()

# اختبار مع XAUUSD
pair = 'XAUUSD'
print(f'تحليل {pair}...')
print()

analysis = analyze_pair_5m(pair)

if analysis and analysis['recommendation'] != 'حياد':
    print(f'التوصية: {analysis["recommendation"]}')
    print(f'سعر الدخول: {analysis["entry"]:.5f}')
    print(f'وقف الخسارة: {analysis["stop_loss"]:.5f}')
    print()
    print('نقاط أخذ الربح الثلاثة:')
    print(f'  TP1: {analysis["take_profit"]:.5f}')
    print(f'  TP2: {analysis["take_profit_2"]:.5f}')
    print(f'  TP3: {analysis["take_profit_3"]:.5f}')
    print()
    print('-' * 70)
    print('التقرير:')
    print('-' * 70)
    report = generate_pair_report(analysis)
    print(report)
else:
    print('لا توجد توصية قوية حالياً')

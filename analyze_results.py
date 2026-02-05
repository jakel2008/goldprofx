#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تحليل شامل لنتائج الصفقات وحساب الإحصائيات
"""

import json
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def analyze_trades():
    """تحليل شامل لجميع الصفقات"""
    
    try:
        with open('active_trades.json', 'r', encoding='utf-8') as f:
            trades = json.load(f)
    except FileNotFoundError:
        print("❌ لم يتم العثور على ملف الصفقات")
        return
    
    if not trades:
        print("⚠️ لا توجد صفقات")
        return
    
    print("="*80)
    print("📊 تحليل شامل لنتائج الصفقات")
    print("="*80)
    print()
    
    # إحصائيات عامة
    total_trades = len(trades)
    active_trades = sum(1 for t in trades.values() if t['status'] == 'active')
    closed_trades = sum(1 for t in trades.values() if t['status'] == 'closed')
    
    wins = sum(1 for t in trades.values() if t.get('result') == 'win')
    losses = sum(1 for t in trades.values() if t.get('result') == 'loss')
    
    win_rate = (wins / closed_trades * 100) if closed_trades > 0 else 0
    
    total_pips = sum(t.get('pips', 0) for t in trades.values() if t.get('pips'))
    
    print(f"إجمالي الصفقات: {total_trades}")
    print(f"صفقات نشطة: {active_trades}")
    print(f"صفقات مغلقة: {closed_trades}")
    print(f"صفقات رابحة: {wins} ✅")
    print(f"صفقات خاسرة: {losses} ❌")
    print(f"معدل النجاح: {win_rate:.1f}%")
    print(f"إجمالي النقاط: {total_pips:.1f}")
    print()
    
    # تحليل حسب الزوج
    print("="*80)
    print("📈 تحليل حسب الزوج")
    print("="*80)
    print()
    
    pairs_stats = {}
    for trade in trades.values():
        symbol = trade['symbol']
        if symbol not in pairs_stats:
            pairs_stats[symbol] = {
                'total': 0,
                'wins': 0,
                'losses': 0,
                'pips': 0,
                'active': 0
            }
        
        pairs_stats[symbol]['total'] += 1
        
        if trade['status'] == 'active':
            pairs_stats[symbol]['active'] += 1
        elif trade.get('result') == 'win':
            pairs_stats[symbol]['wins'] += 1
            pairs_stats[symbol]['pips'] += trade.get('pips', 0)
        elif trade.get('result') == 'loss':
            pairs_stats[symbol]['losses'] += 1
            pairs_stats[symbol]['pips'] += trade.get('pips', 0)
    
    for symbol, stats in sorted(pairs_stats.items()):
        closed = stats['wins'] + stats['losses']
        win_rate_pair = (stats['wins'] / closed * 100) if closed > 0 else 0
        
        print(f"{symbol}:")
        print(f"  إجمالي: {stats['total']} | نشطة: {stats['active']}")
        print(f"  رابحة: {stats['wins']} | خاسرة: {stats['losses']}")
        print(f"  معدل النجاح: {win_rate_pair:.1f}%")
        print(f"  النقاط: {stats['pips']:.1f}")
        
        # تقييم الأداء
        if win_rate_pair < 40:
            print(f"  ⚠️ أداء ضعيف - يحتاج تحسين")
        elif win_rate_pair < 60:
            print(f"  📊 أداء متوسط")
        else:
            print(f"  ✅ أداء ممتاز")
        print()
    
    # تحليل حسب الاتجاه
    print("="*80)
    print("🔄 تحليل حسب الاتجاه")
    print("="*80)
    print()
    
    buy_trades = [t for t in trades.values() if t['direction'] == 'buy']
    sell_trades = [t for t in trades.values() if t['direction'] == 'sell']
    
    buy_wins = sum(1 for t in buy_trades if t.get('result') == 'win')
    buy_losses = sum(1 for t in buy_trades if t.get('result') == 'loss')
    buy_closed = buy_wins + buy_losses
    buy_rate = (buy_wins / buy_closed * 100) if buy_closed > 0 else 0
    
    sell_wins = sum(1 for t in sell_trades if t.get('result') == 'win')
    sell_losses = sum(1 for t in sell_trades if t.get('result') == 'loss')
    sell_closed = sell_wins + sell_losses
    sell_rate = (sell_wins / sell_closed * 100) if sell_closed > 0 else 0
    
    print(f"صفقات الشراء:")
    print(f"  إجمالي: {len(buy_trades)}")
    print(f"  رابحة: {buy_wins} | خاسرة: {buy_losses}")
    print(f"  معدل النجاح: {buy_rate:.1f}%")
    if buy_rate < 50:
        print(f"  ⚠️ ضعف في صفقات الشراء")
    print()
    
    print(f"صفقات البيع:")
    print(f"  إجمالي: {len(sell_trades)}")
    print(f"  رابحة: {sell_wins} | خاسرة: {sell_losses}")
    print(f"  معدل النجاح: {sell_rate:.1f}%")
    if sell_rate < 50:
        print(f"  ⚠️ ضعف في صفقات البيع")
    print()
    
    # أسوأ الصفقات
    print("="*80)
    print("📉 أسوأ 5 صفقات خاسرة")
    print("="*80)
    print()
    
    losing_trades = [t for t in trades.values() if t.get('result') == 'loss']
    losing_trades.sort(key=lambda x: x.get('pips', 0))
    
    for i, trade in enumerate(losing_trades[:5], 1):
        print(f"{i}. {trade['symbol']} ({trade['direction']})")
        print(f"   الخسارة: {trade.get('pips', 0):.1f} نقطة")
        print(f"   الدخول: {trade['entry']:.5f}")
        print(f"   SL: {trade['stop_loss']:.5f}")
        print(f"   الإغلاق: {trade.get('close_price', 0):.5f}")
        print()
    
    # توصيات للتحسين
    print("="*80)
    print("💡 توصيات التحسين")
    print("="*80)
    print()
    
    if win_rate < 50:
        print("⚠️ معدل النجاح منخفض (<50%) - يحتاج تحسين عاجل")
        print("   التوصيات:")
        print("   1. تشديد شروط الدخول (إضافة فلاتر)")
        print("   2. تحسين حساب Stop Loss")
        print("   3. إضافة تأكيدات من multiple timeframes")
        print()
    
    if abs(buy_rate - sell_rate) > 20:
        print("⚠️ فرق كبير بين صفقات الشراء والبيع")
        print("   التوصيات:")
        print("   1. مراجعة شروط تحديد الاتجاه")
        print("   2. تحسين فلاتر RSI/MACD")
        print()
    
    # حساب متوسط المخاطرة/العائد
    if closed_trades > 0:
        avg_win_pips = sum(t.get('pips', 0) for t in trades.values() if t.get('result') == 'win') / wins if wins > 0 else 0
        avg_loss_pips = abs(sum(t.get('pips', 0) for t in trades.values() if t.get('result') == 'loss')) / losses if losses > 0 else 0
        
        print(f"📊 متوسط الربح: {avg_win_pips:.1f} نقطة")
        print(f"📊 متوسط الخسارة: {avg_loss_pips:.1f} نقطة")
        
        if avg_loss_pips > 0:
            rr_ratio = avg_win_pips / avg_loss_pips
            print(f"📊 نسبة المخاطرة/العائد: 1:{rr_ratio:.2f}")
            
            if rr_ratio < 1.5:
                print("   ⚠️ نسبة المخاطرة/العائد منخفضة - يجب أن تكون >= 2:1")
                print()
    
    print("="*80)
    print("✅ اكتمل التحليل")
    print("="*80)

if __name__ == "__main__":
    analyze_trades()

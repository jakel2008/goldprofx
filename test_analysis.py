#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار محرك التحليل
"""

import json
from analysis_engine import AnalysisEngine

def test_analysis():
    print("=" * 60)
    print("🧪 اختبار محرك التحليل")
    print("=" * 60)
    
    # إنشاء محرك التحليل
    engine = AnalysisEngine()
    
    # اختبار على زوج واحد
    test_symbol = "EURUSD"
    test_ticker = "EURUSD=X"
    test_timeframe = "1d"
    
    print(f"\n📊 تحليل {test_symbol} على إطار {test_timeframe}")
    print("-" * 60)
    
    try:
        result = engine.analyze_symbol(test_symbol, test_ticker, test_timeframe)
        
        if result:
            print(f"\n✅ نتيجة التحليل:")
            print(f"   الزوج: {result['symbol']}")
            print(f"   الإطار الزمني: {result['timeframe']}")
            
            consensus = result.get('consensus', {})
            print(f"   الإجماع: {consensus.get('signal', 'N/A').upper()}")
            print(f"   القوة: {consensus.get('strength', 0)}%")
            print(f"   أصوات الشراء: {consensus.get('buy_votes', 0)}")
            print(f"   أصوات البيع: {consensus.get('sell_votes', 0)}")
            print(f"   السعر الحالي: {result.get('current_price', 0):.5f}")
            
            print(f"\n📈 نتائج الاستراتيجيات:")
            strategies = result.get('strategies_results', {})
            for strategy, data in strategies.items():
                signal = data.get('signal', 'N/A')
                confidence = data.get('confidence', 0)
                emoji = "🟢" if signal == "buy" else "🔴" if signal == "sell" else "⚪"
                print(f"   {emoji} {strategy}: {signal} ({confidence}%)")
            
            print(f"\n🔍 ملخص:")
            print(f"   • عدد الاستراتيجيات: {len(strategies)}")
            print(f"   • توصية الشراء: {consensus.get('buy_votes', 0)}")
            print(f"   • توصية البيع: {consensus.get('sell_votes', 0)}")
            print(f"   • محايد: {consensus.get('total_strategies', 0) - consensus.get('buy_votes', 0) - consensus.get('sell_votes', 0)}")
            
            # حفظ النتيجة
            import os
            os.makedirs('analysis', exist_ok=True)
            output_file = f"analysis/test_analysis_{test_symbol.replace('=', '_')}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 تم حفظ التحليل في: {output_file}")
            
        else:
            print("⚠️  فشل التحليل")
            
    except Exception as e:
        print(f"❌ خطأ في التحليل: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ انتهى الاختبار")
    print("=" * 60)

if __name__ == "__main__":
    test_analysis()

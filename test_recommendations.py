#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار محرك التوصيات
"""

import json
from recommendations_engine import RecommendationsEngine

def test_recommendations():
    print("=" * 60)
    print("🧪 اختبار محرك التوصيات")
    print("=" * 60)
    
    # تحميل التفضيلات
    try:
        with open('user_preferences.json', 'r', encoding='utf-8') as f:
            prefs = json.load(f)
        print(f"\n✅ تم تحميل التفضيلات:")
        print(f"   الفئات: {', '.join(prefs['categories'])}")
        print(f"   الحد الأدنى للجودة: {prefs['min_quality_score']}")
    except Exception as e:
        print(f"❌ خطأ في تحميل التفضيلات: {e}")
        return
    
    # إنشاء محرك التوصيات (يحمل التفضيلات تلقائياً)
    print("\n🔄 جاري تحليل الأسواق...")
    engine = RecommendationsEngine()
    
    # مسح شامل للأزواج المفضلة
    print(f"\n\n🔍 مسح الأزواج المفضلة...")
    try:
        recommendations = engine.scan_all_pairs()
        
        print(f"\n✅ تم توليد {len(recommendations)} توصية")
        print("\n📋 التوصيات:")
        print("-" * 60)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['symbol']}")
            print(f"   📈 {rec['signal'].upper()}")
            print(f"   💰 الدخول: {rec['entry_price']:.5f}")
            print(f"   🛡️  SL: {rec['stop_loss']:.5f}")
            print(f"   🎯 TP1: {rec['take_profit_1']:.5f} | TP2: {rec['take_profit_2']:.5f} | TP3: {rec['take_profit_3']:.5f}")
            print(f"   ⭐ الجودة: {rec['quality_score']}/100")
        
        # حفظ التوصيات
        output_file = f"recommendations/test_recommendations.json"
        import os
        os.makedirs('recommendations', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ التوصيات في: {output_file}")
        
    except Exception as e:
        print(f"❌ خطأ في المسح: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ انتهى الاختبار")
    print("=" * 60)

if __name__ == "__main__":
    test_recommendations()

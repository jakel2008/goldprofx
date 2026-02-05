"""
اختبار إرسال التوصيات الحقيقية
"""
import os
import sys

# إصلاح الترميز
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from recommendations_broadcaster import get_new_recommendations, broadcast_recommendations

print("=" * 60)
print("🔍 البحث عن توصيات جديدة...")
print("=" * 60)

new_recs = get_new_recommendations()

if new_recs:
    print(f"\n✅ تم العثور على {len(new_recs)} توصية جديدة:")
    for i, rec in enumerate(new_recs, 1):
        print(f"\n{i}. {rec['symbol']} - {rec['signal'].upper()}")
        print(f"   الإطار الزمني: {rec['timeframe']}")
        print(f"   الجودة: {rec['quality_score']}/100")
        print(f"   الدخول: {rec['entry']}")
    
    print("\n" + "=" * 60)
    response = input("هل تريد إرسال هذه التوصيات؟ (y/n): ")
    
    if response.lower() == 'y':
        broadcast_recommendations(new_recs, test_mode=False)
        print("\n✅ تم الإرسال!")
    else:
        print("\n❌ تم الإلغاء")
else:
    print("\n⚠️ لا توجد توصيات جديدة")

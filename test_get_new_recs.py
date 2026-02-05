"""
اختبار قراءة التوصيات الجديدة
"""
from recommendations_broadcaster import get_new_recommendations

print("=" * 60)
print("فحص التوصيات الجديدة...")
print("=" * 60)

recs = get_new_recommendations()

print(f"\n✅ عدد التوصيات الجديدة: {len(recs)}")

if recs:
    for i, rec in enumerate(recs, 1):
        print(f"\n{i}. {rec['symbol']} - {rec['signal'].upper()}")
        print(f"   الجودة: {rec['quality_score']}/100")
        print(f"   الوقت: {rec['timestamp']}")
        print(f"   ID: {rec.get('recommendation_id', 'N/A')}")
else:
    print("\n⚠️ لا توجد توصيات جديدة (ربما تم إرسال الكل)")

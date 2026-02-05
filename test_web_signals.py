"""
اختبار عرض النتائج على صفحة الويب
Test Web Signals Display with Results
"""

import sqlite3
from datetime import datetime

def test_signals_display():
    """اختبار عرض الإشارات مع النتائج"""
    
    try:
        conn = sqlite3.connect('vip_signals.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        print("=" * 60)
        print("🔍 اختبار عرض الإشارات على صفحة الويب")
        print("=" * 60)
        
        # جلب جميع الإشارات
        c.execute('''
            SELECT * FROM signals 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        
        rows = c.fetchall()
        
        if not rows:
            print("\n⚠️  لا توجد إشارات في قاعدة البيانات")
            return
        
        print(f"\n📊 عدد الإشارات: {len(rows)}")
        print("\n" + "=" * 60)
        
        active_count = 0
        closed_count = 0
        win_count = 0
        loss_count = 0
        
        for row in rows:
            print(f"\n{'🟢' if row['signal_type'] == 'buy' else '🔴'} {row['symbol']} - {row['signal_type'].upper()}")
            print(f"   📍 الدخول: {row['entry_price']}")
            print(f"   🛑 SL: {row['stop_loss']}")
            print(f"   🎯 TP1: {row['take_profit_1']}")
            
            status = row['status'] or 'active'
            result = None
            
            # Check if result column exists
            try:
                result = row['result']
            except:
                pass
            
            if status == 'active':
                print(f"   ⚡ الحالة: نشطة")
                active_count += 1
            elif status == 'closed':
                print(f"   ✓ الحالة: مغلقة")
                closed_count += 1
                
                if result:
                    if result == 'win':
                        print(f"   🎯 النتيجة: ربح")
                        win_count += 1
                    elif result == 'loss':
                        print(f"   ❌ النتيجة: خسارة")
                        loss_count += 1
                
                # عرض سعر الإغلاق
                try:
                    close_price = row['close_price']
                    if close_price:
                        print(f"   💰 سعر الإغلاق: {close_price}")
                except:
                    pass
            
            print(f"   ⏰ الوقت: {row['created_at'][:19]}")
        
        print("\n" + "=" * 60)
        print("📈 ملخص الإحصائيات:")
        print(f"   ⚡ صفقات نشطة: {active_count}")
        print(f"   ✓ صفقات مغلقة: {closed_count}")
        print(f"   🎯 أرباح: {win_count}")
        print(f"   ❌ خسائر: {loss_count}")
        print("=" * 60)
        
        conn.close()
        
        print("\n✅ يمكنك الآن فتح صفحة الويب لعرض النتائج:")
        print("   python web_app.py")
        print("   ثم افتح: http://localhost:5000/signals")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_signals_display()

"""
نظام بث التوصيات المتقدم
Advanced Recommendations Broadcasting System
يقرأ التوصيات الجديدة ويرسلها عبر التليجرام
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

# استيراد دوال البوت
try:
    from vip_bot_simple import send_broadcast_signal
    from vip_subscription_system import SubscriptionManager
except ImportError:
    print("⚠️ تأكد من وجود الملفات المطلوبة")
    exit(1)

# مسارات الملفات
RECOMMENDATIONS_DIR = Path(__file__).parent / "recommendations"
SENT_RECOMMENDATIONS_FILE = Path(__file__).parent / "sent_recommendations.json"

subscription_manager = SubscriptionManager()


def load_sent_recommendations():
    """تحميل قائمة التوصيات المرسلة"""
    if SENT_RECOMMENDATIONS_FILE.exists():
        try:
            with open(SENT_RECOMMENDATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_sent_recommendation(rec_id):
    """حفظ معرف التوصية المرسلة"""
    sent = load_sent_recommendations()
    sent.append({
        'recommendation_id': rec_id,
        'sent_at': datetime.now().isoformat()
    })
    # الاحتفاظ بآخر 1000 توصية فقط
    if len(sent) > 1000:
        sent = sent[-1000:]
    
    with open(SENT_RECOMMENDATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent, f, indent=2, ensure_ascii=False)


def format_recommendation_message(rec):
    """تنسيق رسالة التوصية"""
    signal_emoji = "🟢" if rec['signal'] == 'buy' else "🔴"
    
    message = f"""
{signal_emoji} **توصية جديدة - {rec['symbol']}**

📊 **الإشارة:** {rec['signal'].upper()}
💰 **الدخول:** {rec['entry']:.5f}
🛡️ **وقف الخسارة:** {rec['stop_loss']:.5f}

🎯 **أهداف الربح:**
   TP1: {rec['take_profit_1']:.5f} (R:R 1:2)
   TP2: {rec['take_profit_2']:.5f} (R:R 1:3)
   TP3: {rec['take_profit_3']:.5f} (R:R 1:4)

⭐ **جودة التوصية:** {rec['quality_score']}/100
📅 **الوقت:** {rec['timestamp']}
⏰ **الإطار الزمني:** {rec['timeframe']}

📝 **الأسباب:**
{chr(10).join(f'• {reason}' for reason in rec.get('reasons', ['تحليل فني شامل']))}

⚠️ **تنبيه:** احرص على إدارة المخاطر وعدم المخاطرة بأكثر من 2% من رأس المال
"""
    return message


def get_new_recommendations():
    """جلب التوصيات الجديدة التي لم ترسل"""
    if not RECOMMENDATIONS_DIR.exists():
        return []
    
    sent = load_sent_recommendations()
    sent_ids = {item['recommendation_id'] for item in sent}
    
    new_recommendations = []
    
    # قراءة جميع ملفات التوصيات
    for rec_file in sorted(RECOMMENDATIONS_DIR.glob("recommendations_*.json"), reverse=True):
        try:
            with open(rec_file, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)
                
                for rec in recommendations:
                    rec_id = f"{rec['symbol']}_{rec['timeframe']}_{rec['timestamp']}"
                    
                    if rec_id not in sent_ids:
                        rec['recommendation_id'] = rec_id
                        rec['file'] = rec_file.name
                        new_recommendations.append(rec)
        except Exception as e:
            print(f"خطأ في قراءة {rec_file}: {e}")
    
    return new_recommendations


def broadcast_recommendations(recommendations, test_mode=False):
    """إرسال التوصيات للمشتركين"""
    if not recommendations:
        print("✅ لا توجد توصيات جديدة للإرسال")
        return
    
    print(f"\n{'='*60}")
    print(f"📤 بث {len(recommendations)} توصية جديدة")
    print(f"{'='*60}\n")
    
    for rec in recommendations:
        try:
            # تنسيق البيانات للإرسال
            signal_data = {
                'symbol': rec['symbol'],
                'signal': rec['signal'],
                'entry': rec['entry'],
                'sl': rec['stop_loss'],
                'tp1': rec['take_profit_1'],
                'tp2': rec['take_profit_2'],
                'tp3': rec['take_profit_3'],
                'timeframe': rec.get('timeframe', '1h'),
                'strategy': 'Recommendations Engine'
            }
            
            if test_mode:
                print(f"🧪 [TEST MODE] التوصية: {rec['symbol']} - {rec['signal']}")
                print(f"   الجودة: {rec['quality_score']}/100")
            else:
                # استخدام دالة البث من البوت مباشرةً
                try:
                    send_broadcast_signal(signal_data, rec['quality_score'])
                    print(f"✅ {rec['symbol']} - تم الإرسال إلى المشتركين المؤهلين")
                    save_sent_recommendation(rec['recommendation_id'])
                except Exception as e:
                    print(f"❌ فشل إرسال التوصية {rec['symbol']}: {e}")
                    import traceback
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"❌ خطأ في بث التوصية {rec.get('symbol', 'Unknown')}: {e}")
        
        time.sleep(1)  # فاصل بين التوصيات


def monitor_recommendations(interval=300, test_mode=False):
    """مراقبة التوصيات الجديدة وإرسالها تلقائياً"""
    print("\n" + "="*60)
    print("🔄 نظام المراقبة المستمر للتوصيات")
    print("="*60)
    print(f"⏰ الفحص كل {interval} ثانية")
    print(f"📂 المجلد: {RECOMMENDATIONS_DIR}")
    if test_mode:
        print("🧪 وضع الاختبار: لن يتم إرسال الرسائل فعلياً")
    print("="*60 + "\n")
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] جاري فحص التوصيات الجديدة...")
            
            new_recs = get_new_recommendations()
            
            if new_recs:
                print(f"🎯 تم العثور على {len(new_recs)} توصية جديدة")
                broadcast_recommendations(new_recs, test_mode=test_mode)
            else:
                print("✅ لا توجد توصيات جديدة")
            
            print(f"⏳ الانتظار {interval} ثانية...\n")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n⚠️ تم إيقاف المراقبة")
            break
        except Exception as e:
            print(f"❌ خطأ في المراقبة: {e}")
            time.sleep(60)


if __name__ == "__main__":
    import sys
    
    # التحقق من وجود مجلد التوصيات
    if not RECOMMENDATIONS_DIR.exists():
        print("⚠️ مجلد التوصيات غير موجود، سيتم إنشاؤه")
        RECOMMENDATIONS_DIR.mkdir(exist_ok=True)
    
    # وضع الاختبار
    test_mode = '--test' in sys.argv
    
    if '--once' in sys.argv:
        # إرسال مرة واحدة فقط
        print("📤 إرسال التوصيات الجديدة (مرة واحدة)")
        new_recs = get_new_recommendations()
        broadcast_recommendations(new_recs, test_mode=test_mode)
    else:
        # مراقبة مستمرة
        monitor_recommendations(interval=300, test_mode=test_mode)

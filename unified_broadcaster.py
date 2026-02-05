# -*- coding: utf-8 -*-
"""
نظام بث الإشارات الموحد - الإصدار 2.0
يرسل الإشارات للبوت والويب معاً في نفس اللحظة
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from unified_signal_manager import UnifiedSignalManager

# مسارات الملفات
SIGNALS_DIR = Path(__file__).parent / "signals"
SENT_SIGNALS_FILE = Path(__file__).parent / "sent_signals.json"
CHECK_INTERVAL = 60  # فحص كل 60 ثانية


def load_sent_signals():
    """تحميل قائمة الإشارات المرسلة"""
    if SENT_SIGNALS_FILE.exists():
        try:
            with open(SENT_SIGNALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_sent_signal(signal_id):
    """حفظ معرف الإشارة المرسلة"""
    sent = load_sent_signals()
    sent.append({
        'signal_id': signal_id,
        'sent_at': datetime.now().isoformat()
    })
    # الاحتفاظ بآخر 1000 إشارة فقط
    if len(sent) > 1000:
        sent = sent[-1000:]
    
    with open(SENT_SIGNALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent, f, indent=2, ensure_ascii=False)


def read_and_broadcast_signals():
    """قراءة الإشارات وبثها عبر النظام الموحد"""
    
    # تأكد من وجود مجلد الإشارات
    if not SIGNALS_DIR.exists():
        print(f"📂 إنشاء مجلد الإشارات: {SIGNALS_DIR}")
        SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
        return
    
    # قراءة الإشارات المرسلة
    sent_ids = [item['signal_id'] for item in load_sent_signals()]
    
    # البحث عن إشارات جديدة
    signal_files = sorted(SIGNALS_DIR.glob("*.json"))
    
    if not signal_files:
        print("📭 لا توجد ملفات إشارات للمعالجة")
        return
    
    # إنشاء مدير الإشارات الموحد
    unified_manager = UnifiedSignalManager()
    
    new_signals = 0
    
    for signal_file in signal_files:
        signal_id = signal_file.stem  # اسم الملف بدون امتداد
        
        # تخطي الإشارات المرسلة مسبقاً
        if signal_id in sent_ids:
            continue
        
        try:
            # قراءة الإشارة
            with open(signal_file, 'r', encoding='utf-8') as f:
                signal_data = json.load(f)
            
            print(f"\n{'='*70}")
            print(f"📡 نشر إشارة جديدة: {signal_id}")
            print(f"{'='*70}")
            
            # نشر الإشارة عبر النظام الموحد (ويب + بوت)
            report = unified_manager.publish_signal(signal_data)
            
            # عرض التقرير
            print(f"\n📊 تقرير النشر:")
            print(f"   ✅ حفظ في قاعدة الويب: {'نعم' if report['web_saved'] else 'لا'}")
            print(f"   ✅ حفظ كملف: {'نعم' if report['file_saved'] else 'لا'}")
            print(f"   📤 تم الإرسال للبوت: {report['telegram_sent']} مستخدم")
            
            if report['telegram_failed'] > 0:
                print(f"   ⚠️  فشل الإرسال: {report['telegram_failed']} مستخدم")
            
            if report['errors']:
                print(f"   ❌ أخطاء:")
                for error in report['errors']:
                    print(f"      • {error}")
            
            # حفظ الإشارة كمرسلة
            save_sent_signal(signal_id)
            new_signals += 1
            
            print(f"\n✅ تم نشر الإشارة بنجاح!")
            
        except Exception as e:
            print(f"❌ خطأ في معالجة {signal_file.name}: {e}")
    
    if new_signals > 0:
        print(f"\n{'='*70}")
        print(f"✅ تم نشر {new_signals} إشارة جديدة")
        print(f"{'='*70}\n")
    else:
        print("✅ جميع الإشارات تم نشرها مسبقاً")


def main():
    """البرنامج الرئيسي للبث المستمر"""
    os.system('chcp 65001 > nul')
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           📡 نظام البث الموحد - ويب + بوت                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

🔄 يعمل النظام الآن...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ مزامنة تلقائية بين الويب والبوت
  ✅ إرسال الإشارات لكليهما معاً
  ✅ قاعدة بيانات موحدة
  ✅ فحص كل {CHECK_INTERVAL} ثانية

اضغط Ctrl+C للإيقاف
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    # مزامنة أولية للقواعد
    print("\n🔄 مزامنة قواعد البيانات الأولية...")
    unified_manager = UnifiedSignalManager()
    sync_result = unified_manager.sync_databases()
    
    print(f"\n✅ المزامنة الأولية:")
    print(f"   • المستخدمين: {sync_result['users']}")
    print(f"   • الإشارات: {sync_result['signals']}")
    
    # عرض الإحصائيات
    print("\n📊 الإحصائيات الموحدة:")
    stats = unified_manager.get_unified_statistics()
    print(f"   • إجمالي الإشارات: {stats['total_signals']}")
    print(f"   • إشارات اليوم: {stats['signals_today']}")
    print(f"   • المستخدمين النشطين: {stats['active_users']}/{stats['total_users']}")
    
    print(f"\n{'='*70}")
    print("🚀 بدء البث التلقائي...")
    print(f"{'='*70}\n")
    
    # حلقة البث المستمر
    cycle = 0
    try:
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n[{timestamp}] 🔍 دورة #{cycle} - فحص الإشارات الجديدة...")
            
            read_and_broadcast_signals()
            
            print(f"⏳ الانتظار {CHECK_INTERVAL} ثانية...\n")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف نظام البث")
        print(f"🕒 وقت الإيقاف: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 إجمالي الدورات: {cycle}\n")


if __name__ == "__main__":
    main()

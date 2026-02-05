# إضافة إشارة من ملف JSON إلى قاعدة البيانات وبثها للبوت والموقع
from unified_signal_manager import UnifiedSignalManager
import json
import sys
import os

if __name__ == "__main__":
    # اسم ملف الإشارة (يمكن تغييره حسب الحاجة)
    signal_file = sys.argv[1] if len(sys.argv) > 1 else "signals/TEST_SIGNAL_20260131.json"
    if not os.path.exists(signal_file):
        print(f"❌ الملف غير موجود: {signal_file}")
        sys.exit(1)
    
    with open(signal_file, 'r', encoding='utf-8') as f:
        signal_data = json.load(f)
    
    manager = UnifiedSignalManager()
    report = manager.publish_signal(signal_data)
    print("--- تقرير النشر ---")
    print(report)
    print("تمت إضافة الإشارة للقاعدة وبثها للبوت والموقع.")

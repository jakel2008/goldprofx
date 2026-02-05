"""
اختبار إرسال رسالة عبر البوت
"""
import os
import sys

# إصلاح الترميز
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from vip_bot_simple import send_broadcast_signal

# إعداد توصية تجريبية
test_signal = {
    'symbol': 'EURUSD',
    'signal': 'buy',
    'entry': 1.0850,
    'sl': 1.0820,
    'tp1': 1.0900,
    'tp2': 1.0950,
    'tp3': 1.1000,
    'quality_score': 85,
    'timestamp': '2026-01-24T08:00:00',
    'timeframe': '1h',
    'strategy': 'Test Signal'
}

print("=" * 50)
print("اختبار إرسال رسالة تجريبية...")
print("=" * 50)

try:
    send_broadcast_signal(test_signal, test_signal['quality_score'])
    print("\n✅ تم إرسال الرسالة بنجاح!")
except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

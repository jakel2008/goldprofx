#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""توليد إشارات حية للعرض"""

from unified_signal_manager import UnifiedSignalManager
from datetime import datetime

manager = UnifiedSignalManager()

# إشارات تجريبية حية
live_signals = [
    {
        "pair": "EURUSD",
        "signal": "buy",
        "entry": 1.0850,
        "sl": 1.0820,
        "tp1": 1.0900,
        "tp2": 1.0950,
        "tp3": 1.1000,
        "quality_score": 88,
        "timeframe": "5m",
        "timestamp": datetime.now().isoformat()
    },
    {
        "pair": "XAUUSD",
        "signal": "sell",
        "entry": 2650.50,
        "sl": 2655.00,
        "tp1": 2640.00,
        "tp2": 2630.00,
        "tp3": 2620.00,
        "quality_score": 92,
        "timeframe": "5m",
        "timestamp": datetime.now().isoformat()
    },
    {
        "pair": "GBPUSD",
        "signal": "buy",
        "entry": 1.2650,
        "sl": 1.2620,
        "tp1": 1.2700,
        "tp2": 1.2750,
        "tp3": 1.2800,
        "quality_score": 85,
        "timeframe": "5m",
        "timestamp": datetime.now().isoformat()
    },
    {
        "pair": "BTCUSD",
        "signal": "buy",
        "entry": 42500.00,
        "sl": 42000.00,
        "tp1": 43000.00,
        "tp2": 43500.00,
        "tp3": 44000.00,
        "quality_score": 95,
        "timeframe": "5m",
        "timestamp": datetime.now().isoformat()
    }
]

print("📡 نشر الإشارات الحية...")
print("="*50)

for signal in live_signals:
    report = manager.publish_signal(signal)
    
    web_status = "✅" if report['web_saved'] else "❌"
    bot_count = report['telegram_sent']
    
    print(f"{signal['pair']} - {signal['signal'].upper()}")
    print(f"  🌐 الويب: {web_status}")
    print(f"  📱 البوت: {bot_count} مستخدم")
    print(f"  ⭐ الجودة: {signal['quality_score']}/100")
    print()

print("="*50)
print(f"✅ تم نشر {len(live_signals)} إشارة بنجاح!")
print("\n🌐 تحديث الصفحة: http://localhost:5000/signals")

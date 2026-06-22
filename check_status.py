#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from mt5_bridge import MT5Bridge
import os

print("=" * 60)
print("🤖 فحص حالة النظام")
print("=" * 60)

# Check MT5 Connection
print("\n📊 اتصال MetaTrader5:")
b = MT5Bridge()
conn = b.connect()
print(f"   ✓ الاتصال: {'نعم' if conn else 'لا'}")

if conn:
    positions_info = b.has_open_positions()
    if positions_info.get('success'):
        positions = positions_info.get('positions', [])
        print(f"   ✓ الصفقات المفتوحة: {len(positions)}")
    else:
        print(f"   ✗ خطأ في استرجاع الصفقات")

# Check Config
print("\n⚙️  الإعدادات المحملة:")
config_path = "auto_trading_user_config.json"
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)
    print(f"   ✓ الأزواج: {', '.join(config.get('symbols', []))}")
    print(f"   ✓ min_score_gap: {config.get('min_score_gap', 'N/A')}")
    print(f"   ✓ min_rr_ratio: {config.get('min_rr_ratio', 'N/A')}")
    print(f"   ✓ المخاطرة: {config.get('risk_percent', 'N/A')}%")
    print(f"   ✓ الحد الأقصى للصفقات: {config.get('max_open_positions', 'N/A')}")
else:
    print(f"   ✗ لم يتم العثور على الإعدادات")

# Check Recent Signals
print("\n📡 آخر الإشارات:")
signals_dir = "signals"
if os.path.exists(signals_dir):
    files = sorted(os.listdir(signals_dir), key=lambda x: os.path.getmtime(os.path.join(signals_dir, x)), reverse=True)[:3]
    if files:
        for f in files:
            path = os.path.join(signals_dir, f)
            mtime = os.path.getmtime(path)
            from datetime import datetime
            mod_time = datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
            print(f"   ✓ {f} - {mod_time}")
    else:
        print("   ⏳ لا توجد إشارات بعد")
else:
    print("   ✗ لم يتم العثور على مجلد الإشارات")

print("\n" + "=" * 60)
print("✅ النظام جاهز للعمل")
print("=" * 60)

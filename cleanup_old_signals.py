#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from datetime import datetime, timedelta

# تنظيف الملفات القديمة (أقدم من يومين)
SIGNALS_DIR = Path('signals')
cutoff_date = datetime.now() - timedelta(days=2)

deleted_count = 0
for signal_file in SIGNALS_DIR.glob('*.json'):
    try:
        parts = signal_file.stem.split('_')
        if len(parts) >= 3:
            date_str = parts[-2] + '_' + parts[-1]
            file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            
            if file_date < cutoff_date:
                signal_file.unlink()
                deleted_count += 1
    except:
        pass

print(f'✅ تم حذف {deleted_count} إشارة قديمة (أقدم من يومين)')

# إعادة بناء sent_signals.json من الإشارات الحالية فقط
sent = []
for signal_file in SIGNALS_DIR.glob('*.json'):
    try:
        with open(signal_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            data = [data]
        
        for item in data:
            symbol = item.get('symbol', item.get('pair', 'UNKNOWN'))
            entry = item.get('entry_price', item.get('entry', 0))
            sent.append({
                'signal_id': f'{symbol}_{entry}_{signal_file.stem}',
                'sent_at': datetime.now().isoformat()
            })
    except:
        pass

with open('sent_signals.json', 'w', encoding='utf-8') as f:
    json.dump(sent, f, indent=2, ensure_ascii=False)

print(f'✅ تم تحديث السجل: {len(sent)} إشارة حديثة فقط')
print('📍 الآن سيبث البث الإشارات الجديدة فقط')

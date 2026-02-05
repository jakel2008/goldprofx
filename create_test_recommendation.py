"""
اختبار سريع - توليد توصية جديدة
"""
import json
from datetime import datetime
from pathlib import Path

# إنشاء توصية تجريبية جديدة
new_recommendation = {
    "symbol": "EURUSD",
    "timeframe": "1h",
    "signal": "buy",
    "entry": 1.0850,
    "current_price": 1.0845,
    "stop_loss": 1.0820,
    "take_profit_1": 1.0900,
    "take_profit_2": 1.0950,
    "take_profit_3": 1.1000,
    "risk_reward": [2, 3, 4],
    "atr": 0.0015,
    "rsi": 45.5,
    "support_levels": [1.0830, 1.0810, 1.0790],
    "resistance_levels": [1.0880, 1.0920, 1.0960],
    "timestamp": datetime.now().isoformat(),
    "quality_score": 80
}

# حفظ في ملف جديد
filename = f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
filepath = Path("recommendations") / filename

recommendations_dir = Path("recommendations")
recommendations_dir.mkdir(exist_ok=True)

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump([new_recommendation], f, indent=2, ensure_ascii=False)

print(f"✅ تم إنشاء توصية جديدة: {filename}")
print(f"📊 الرمز: {new_recommendation['symbol']}")
print(f"📈 الإشارة: {new_recommendation['signal'].upper()}")
print(f"⭐ الجودة: {new_recommendation['quality_score']}/100")

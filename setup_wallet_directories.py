"""
إعداد مجلدات المحافظ المتعددة
Setup Multi Wallet Directories
"""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = PROJECT_ROOT / "multi_account_config.json"

def setup_wallet_directories():
    """إنشاء مجلدات المحافظ المطلوبة"""
    
    print("\n" + "="*60)
    print("🚀 إعداد مجلدات المحافظ المتعددة")
    print("="*60 + "\n")
    
    if not REGISTRY_PATH.exists():
        print(f"❌ الملف غير موجود: {REGISTRY_PATH}")
        return False
    
    try:
        with REGISTRY_PATH.open("r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        return False
    
    accounts = registry.get("accounts", [])
    if not accounts:
        print("❌ لا توجد حسابات في الملف")
        return False
    
    created_count = 0
    
    for acc in accounts:
        acc_id = acc.get("id", "unknown")
        config_path = PROJECT_ROOT / acc.get("config", f"accounts/{acc_id}/config.json")
        wallet_path = PROJECT_ROOT / acc.get("wallet", f"accounts/{acc_id}/wallet.json")
        state_path = PROJECT_ROOT / acc.get("state", f"accounts/{acc_id}/runtime_state.json")
        
        # إنشاء المجلد
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # إنشاء ملفات فارغة إذا لم تكن موجودة
        if not wallet_path.exists():
            with wallet_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "enabled": False,
                    "login": 0,
                    "password": "",
                    "server": "",
                    "path": "",
                    "magic": 88001,
                    "deviation": 20,
                    "default_volume": 0.01,
                }, f, ensure_ascii=False, indent=2)
            print(f"✅ تم إنشاء: {wallet_path.relative_to(PROJECT_ROOT)}")
            created_count += 1
        
        if not config_path.exists():
            with config_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "enabled": False,
                    "symbols": ["XAUUSD", "BTCUSD"],
                    "intervals": ["15m", "1h"],
                    "max_risk_percent_of_equity": 1.0,
                    "daily_loss_limit_usd": 200.0,
                    "scan_every_sec": 20,
                    "use_equity_for_risk": True,
                    "allow_normal_signals": True,
                    "allow_strong_signals": True,
                    "split_tp": True,
                    "dry_run": False,
                }, f, ensure_ascii=False, indent=2)
            print(f"✅ تم إنشاء: {config_path.relative_to(PROJECT_ROOT)}")
            created_count += 1
        
        if not state_path.exists():
            with state_path.open("w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            print(f"✅ تم إنشاء: {state_path.relative_to(PROJECT_ROOT)}")
            created_count += 1
    
    print("\n" + "="*60)
    print(f"✅ تم إعداد {len(accounts)} حساب")
    print(f"✅ تم إنشاء {created_count} ملف جديد")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    setup_wallet_directories()
    input("اضغط Enter للخروج...")

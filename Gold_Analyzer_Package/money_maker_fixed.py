import os
# Try to import dotenv, fallback to dummy if not installed
try:
    from dotenv import load_dotenv  # type: ignore  # If unresolved, fallback below
except ImportError:
    def load_dotenv():
        pass
import threading
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import requests
from datetime import datetime, timedelta


# Import missing functions from analyzer module with dynamic import fallback
import sys
import importlib
analyzer_imported = False

# Try to add script directory to sys.path first
analyzer_path = os.path.join(os.path.dirname(__file__), "analyzer.py")
if os.path.exists(analyzer_path):
    sys.path.insert(0, os.path.dirname(analyzer_path))

try:
    from analyzer import fetch_data, analyze, detect_signals  # type: ignore
    analyzer_imported = True
except ImportError:
    # Try dynamic import as fallback
    try:
        analyzer = importlib.import_module("analyzer")
        fetch_data = analyzer.fetch_data
        analyze = analyzer.analyze
        detect_signals = analyzer.detect_signals
        analyzer_imported = True
    except Exception:
        pass

if not analyzer_imported:
    def fetch_data(symbol, timeframe, outputsize=320):
        raise NotImplementedError("fetch_data not implemented")
    def analyze(df, indicators="All"):
        raise NotImplementedError("analyze not implemented")
    def detect_signals(df, timeframe, app_instance=None, htf_reco=None):
        raise NotImplementedError("detect_signals not implemented")

# ===== CONFIG =====
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set(map(int, filter(None, ADMIN_IDS_RAW.split(","))))

# كان يرفع ValueError ويوقف التشغيل بالكامل
if not BOT_TOKEN:
    print("⚠️  BOT_TOKEN غير موجود في البيئة، سيتم تعطيل إرسال رسائل التلغرام.")

# ===== VIP STORAGE =====
VIP_USERS_PATH = os.getenv("VIP_USERS_PATH", "vip_users.json")

def load_vips() -> Dict[str, str]:
    if not os.path.exists(VIP_USERS_PATH):
        return {}
    try:
        import json
        with open(VIP_USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_vips(data: Dict[str, str]) -> None:
    import json
    with open(VIP_USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

VIP_USERS: Dict[str, str] = load_vips()

# ===== TELEGRAM =====
def send_message(chat_id: int, text: str) -> None:
    if not BOT_TOKEN:
        print("⚠️ BOT_TOKEN مفقود، لن يتم إرسال الرسالة.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if not resp.ok:
            print(f"⚠️ فشل الإرسال: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ خطأ أثناء الإرسال: {e}")

# ===== DATA CLASSES =====
@dataclass
class AnalysisResult:
    symbol: str
    timeframe: str
    recommendation: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    rr: float
    confidence: str

# ===== BOT LOOP (stub) =====
def bot_loop():
    """Stub: استبدل بالمنطق الفعلي للبوت."""
    return

def start_bot_thread():
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    print("✅ Telegram Bot started in background")

# ===== LINK BOT TO ANALYZER =====
def analyze_symbol_real(symbol: str, timeframe: str = "1h") -> Dict:
    try:
        df = fetch_data(symbol, timeframe, outputsize=320)
        if len(df) < 60:
            return {"error": "Not enough data"}
        df = analyze(df, indicators="All")
        signals, recommendation, levels, _ = detect_signals(
            df, timeframe, app_instance=None, htf_reco=None
        )
        return {
            "symbol": symbol,
            "tf": timeframe,
            "rec": recommendation,
            "entry": float(df.iloc[-1]["Close"]),
            "sl": float(levels.get("SL", 0)),
            "tp1": float(levels.get("TP1", 0)),
            "tp2": float(levels.get("TP2", 0)),
            "tp3": float(levels.get("TP3", 0)),
            "rr": float(str(levels.get("RR (TP1/SL)", "0")).replace(",", "")),
        }
    except Exception as e:
        return {"error": str(e)}

# ===== INPUT VALIDATION =====
def validate_vip_command(text: str) -> Tuple[bool, Optional[str], Optional[int]]:
    parts = text.split()
    if len(parts) != 3:
        return False, None, None
    try:
        _, uid, days = parts
        if not uid.isdigit():
            return False, None, None
        days = int(days)
        if days < 1 or days > 365:
            return False, None, None
        return True, uid, days
    except ValueError:
        return False, None, None

# ===== BOT COMMANDS =====
def handle_addvip(chat_id: int, text: str):
    valid, uid, days = validate_vip_command(text)
    if not valid:
        send_message(chat_id,
            "❌ الصيغة الصحيحة:\n"
            "/addvip USER_ID DAYS\n"
            "مثال: /addvip 123456789 30"
        )
        return
    try:
        expiry = datetime.now() + timedelta(days=days)
        VIP_USERS[uid] = expiry.isoformat()
        save_vips(VIP_USERS)
        send_message(chat_id, f"✅ تم تفعيل {uid} لمدة {days} يوم")
        send_message(int(uid),
            f"🎉 تم تفعيل اشتراكك في خدمة VIP\n"
            f"📅 صالح حتى: {expiry.strftime('%Y-%m-%d')}\n"
            f"💡 استخدم /gold أو /btc للحصول على التوصيات"
        )
    except Exception as e:
        send_message(chat_id, f"❌ خطأ: {str(e)}")

# ===== ANALYSIS (placeholder) =====
def detect_signals_v2(
    df: pd.DataFrame,
    interval: str,
    symbol: str,
    htf_reco: Optional[str] = None
) -> AnalysisResult:
    """
    Placeholder: استبدل بالمنطق الفعلي ثم أزل NotImplementedError.
    """
    raise NotImplementedError("detect_signals_v2 not implemented")

# ===== GUI PLACEHOLDER =====
class MoneyMakerApp:
    def mainloop(self):
        print("GUI placeholder. Replace MoneyMakerApp with real implementation.")

# ===== MAIN =====
if __name__ == "__main__":
    start_bot_thread()
    app = MoneyMakerApp()
    app.mainloop()
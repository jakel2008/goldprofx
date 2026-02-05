import os
import json
import time
import threading
import requests
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

# =========================
# VIP TRADING TELEGRAM BOT
# =========================

# ========= الإعدادات =========
BOT_TOKEN = "8253445917:AAEdoO2Nq7VlsBkVTuiOySpuPCk0zkBrlP0"  # ضع توكن بوتك هنا
ADMIN_IDS = {123456789}  # ضع آيدي الأدمن
VIP_CHANNEL_ID = -1001234567890  # ضع آيدي القناة الخاصة

DATA_FILE = "users.json"
TRADES_FILE = "trades_log.json"

SCAN_INTERVAL = 3600  # فحص تلقائي كل ساعة
DEFAULT_TF = "1H"

SYMBOLS = {
    "/gold": "XAUUSD",
    "/eurusd": "EURUSD",
    "/btc": "BTCUSD"
}

PLANS = {
    "week": 7,
    "month": 30,
    "year": 365
}

PRICES = {
    "week": "10 USDT",
    "month": "30 USDT",
    "year": "250 USDT"
}

# ============================

# ========= أدوات عامة =========
def ensure_json_file(path: str, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)

ensure_json_file(DATA_FILE, {})
ensure_json_file(TRADES_FILE, [])

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        return resp.ok
    except Exception as e:
        print("SEND MESSAGE ERROR:", e)
        return False

def load_users():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def log_trade(data):
    try:
        with open(TRADES_FILE, encoding="utf-8") as f:
            trades = json.load(f)
    except Exception:
        trades = []

    data["time"] = datetime.now().isoformat()
    trades.append(data)

    with open(TRADES_FILE, "w", encoding="utf-8") as f:
        json.dump(trades, f, indent=4)

USERS = load_users()

def is_admin(uid):
    return uid in ADMIN_IDS

def is_vip(uid):
    u = USERS.get(str(uid))
    if not u or "expires" not in u:
        return False
    try:
        expiry = datetime.fromisoformat(u["expires"])
    except ValueError:
        return False
    return datetime.now() < expiry

# ========= 🔴 ربط التحليل هنا =========
def analyze_symbol(symbol, timeframe=DEFAULT_TF):
    """
    🔴 هذه بيانات وهمية للعرض — استبدلها بتحليل حقيقي.
    """
    return {
        "symbol": symbol,
        "tf": timeframe,
        "rec": "شراء قوي",
        "entry": 2354.2,
        "sl": 2341.8,
        "tp1": 2368.5,
        "tp2": 2382.9,
        "tp3": 2401.3,
        "rr": 1.72
    }

def format_signal(d):
    return f"""
📊 <b>{d['symbol']}</b>
⏱ TF: {d['tf']}

🔥 <b>{d['rec']}</b>

🎯 Entry: {d['entry']}
🛑 SL: {d['sl']}
🎯 TP1: {d['tp1']}
🎯 TP2: {d['tp2']}
🎯 TP3: {d['tp3']}

📐 RR: {d['rr']}

⚠️ إدارة رأس المال 1–2%
© VIP SIGNALS
"""

def format_plans():
    lines = [f"{k}: {PRICES[k]} ({PLANS[k]} يوم)" for k in ["week", "month", "year"]]
    return "خطط الاشتراك:\n" + "\n".join(lines) + "\n\nاشترِ بالخيار:\n/buy week\n/buy month\n/buy year"

# ========= بوت تلجرام =========
def bot_loop():
    last_update = 0
    print("🚀 BOT STARTED")

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update + 1}"
            data = requests.get(url, timeout=20).json()

            for update in data.get("result", []):
                last_update = update["update_id"]
                msg = update.get("message") or {}
                if not msg:
                    continue
                text = (msg.get("text") or "").strip()
                uid = msg.get("chat", {}).get("id")
                if uid is None:
                    continue

                low = text.lower()

                # ===== START =====
                if low == "/start":
                    send_message(uid, "مرحباً! أهلاً بك في VIP TRADING.\n" + format_plans() +
                                       "\n\nالأزواج المتاحة:\n" + "\n".join(SYMBOLS.keys()))
                    continue

                # ===== الخطط =====
                if low == "/plans":
                    send_message(uid, format_plans())
                    continue

                # ===== شراء =====
                if low.startswith("/buy"):
                    parts = low.split()
                    if len(parts) < 2 or parts[1] not in PLANS:
                        send_message(uid, "استخدم: /buy week أو /buy month أو /buy year")
                        continue
                    plan = parts[1]
                    days = PLANS[plan]
                    expires = (datetime.now() + timedelta(days=days)).isoformat()
                    USERS[str(uid)] = {"plan": plan, "expires": expires}
                    save_users(USERS)
                    send_message(uid, f"تم تفعيل اشتراك {plan}. ينتهي في:\n{expires}")
                    continue

                # ===== إشارات للأعضاء =====
                if low in SYMBOLS:
                    if not is_vip(uid):
                        send_message(uid, "هذه الخدمة للأعضاء VIP. استخدم /plans للاشتراك.")
                        continue
                    sym = SYMBOLS[low]
                    sig = analyze_symbol(sym)
                    send_message(uid, format_signal(sig))
                    log_trade({"uid": uid, "symbol": sym, "signal": sig})
                    continue

                # ===== أوامر إدارية (اختياري) =====
                if low.startswith("/broadcast") and is_admin(uid):
                    msg_text = text[len("/broadcast"):].strip()
                    for u in list(USERS.keys()):
                        send_message(int(u), msg_text)
                    continue

        except Exception as e:
            print("BOT ERROR:", e)

        time.sleep(3)

# ========= فحص تلقائي =========
def auto_scan():
    # يفحص جميع العملات كل ساعة، ويرسل توصيات قوية للقناة VIP
    while True:
        try:
            for symbol in SYMBOLS.values():
                data = analyze_symbol(symbol)
                if data["rec"] in ["شراء قوي", "بيع قوي"]:
                    send_message(VIP_CHANNEL_ID, format_signal(data))
                    log_trade({"uid": "channel", "symbol": symbol, "signal": data})
        except Exception as e:
            print("SCAN ERROR:", e)
        time.sleep(SCAN_INTERVAL)

def start_bot():
    # تشغيل البوت والفحص في خيوط منفصلة
    threading.Thread(target=bot_loop, daemon=True).start()
    threading.Thread(target=auto_scan, daemon=True).start()

# ========= واجهة رسومية بسيطة =========
class MoneyMakerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Money Maker App")
        self.geometry("420x220")
        self.resizable(False, False)

        frm = ttk.Frame(self, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="VIP Trading Bot", font=("Segoe UI", 12, "bold")).pack(pady=(0, 8))
        self.status = ttk.Label(frm, text="الواجهة جاهزة. اضغط بدء لتشغيل البوت.", foreground="#2e7d32")
        self.status.pack(pady=(0, 12))

        btn_start = ttk.Button(frm, text="بدء البوت", command=self.on_start)
        btn_start.pack(pady=4)

        btn_plans = ttk.Button(frm, text="عرض الخطط (نص)", command=lambda: messagebox.showinfo("Plans", format_plans()))
        btn_plans.pack(pady=4)

        ttk.Label(frm, text="القنوات المتاحة:\n" + ", ".join(SYMBOLS.keys())).pack(pady=(8, 0))

    def on_start(self):
        start_bot()
        self.status.config(text="البوت يعمل (Threads). تأكد من توكن البوت والقناة.", foreground="#1565c0")
        messagebox.showinfo("Info", "تم تشغيل البوت والفحص في الخلفية.")

if __name__ == "__main__":
    app = MoneyMakerApp()
    app.mainloop()
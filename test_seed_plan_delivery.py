#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار توزيع الإشارات على مستخدمي Seed حسب الخطة.

الوضع الافتراضي: محاكاة الإرسال (بدون اتصال Telegram).
يمكن تشغيل إرسال فعلي باستخدام --real-send.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Dict, List

import telegram_sender


ROOT = Path(__file__).parent
VIP_DB = ROOT / "vip_subscriptions.db"
SEED_PREFIX = "seed_plan_"


def load_seed_users() -> List[Dict[str, object]]:
    conn = sqlite3.connect(VIP_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, username, plan, chat_id, telegram_id, status
        FROM users
        WHERE username LIKE ?
        ORDER BY user_id ASC
        """,
        (f"{SEED_PREFIX}%",),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def print_seed_users(users: List[Dict[str, object]]) -> None:
    print("\n[Seed Users]")
    for u in users:
        print(
            f"- {u.get('username')} | plan={u.get('plan')} | "
            f"chat_id={u.get('chat_id')} | status={u.get('status')}"
        )


def run_signal_case(quality_score: int, real_send: bool = False) -> Dict[str, object]:
    signal = {
        "symbol": "XAUUSD",
        "signal": "BUY",
        "entry": 2050.0,
        "sl": 2042.0,
        "tp1": 2060.0,
        "tp2": 2066.0,
        "tp3": 2072.0,
        "timeframe": "1h",
        "confidence": "seed_test",
        "quality_score": quality_score,
    }

    original_sender = telegram_sender.send_telegram_message

    if not real_send:
        def fake_sender(chat_id, text, parse_mode="HTML", bot_token=None):
            return {"success": True, "response": {"ok": True, "chat_id": str(chat_id)}}

        telegram_sender.send_telegram_message = fake_sender

    try:
        result = telegram_sender.send_signal_to_subscribers(signal, quality_score=quality_score)
    finally:
        telegram_sender.send_telegram_message = original_sender

    return result


def summarize_seed_details(result: Dict[str, object]) -> Dict[str, List[str]]:
    sent: List[str] = []
    skipped_quality: List[str] = []
    skipped_limit: List[str] = []
    failed: List[str] = []

    details = result.get("details", []) if isinstance(result, dict) else []
    for d in details:
        if not isinstance(d, dict):
            continue
        user_id = d.get("user_id")
        plan = d.get("plan")
        status = d.get("status")
        label = f"{user_id}({plan})"

        if status == "sent":
            sent.append(label)
        elif status == "skipped_quality":
            skipped_quality.append(label)
        elif status == "skipped_plan_limit":
            skipped_limit.append(label)
        elif status in ("failed", "error"):
            failed.append(label)

    return {
        "sent": sent,
        "skipped_quality": skipped_quality,
        "skipped_plan_limit": skipped_limit,
        "failed": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test seed plan delivery")
    parser.add_argument("--real-send", action="store_true", help="Send via real Telegram instead of simulation")
    args = parser.parse_args()

    users = load_seed_users()
    if not users:
        print("لم يتم العثور على مستخدمي Seed. شغّل seed_default_subscribers_safe.py أولاً.")
        return

    print("=" * 90)
    print("SEED PLAN DELIVERY TEST")
    print("=" * 90)
    print(f"Mode: {'REAL SEND' if args.real_send else 'SIMULATED SEND'}")
    print_seed_users(users)

    # حالات الجودة: عالي/متوسط/منخفض
    cases = [95, 75, 60]

    for quality in cases:
        print(f"\n--- Quality Test: {quality} ---")
        res = run_signal_case(quality_score=quality, real_send=args.real_send)
        summary = summarize_seed_details(res)

        print(f"sent_count={res.get('sent_count', 0)} | failed_count={res.get('failed_count', 0)}")
        print(f"sent={summary['sent']}")
        print(f"skipped_quality={summary['skipped_quality']}")
        print(f"skipped_plan_limit={summary['skipped_plan_limit']}")
        print(f"failed={summary['failed']}")

    print("\nDone.")


if __name__ == "__main__":
    main()

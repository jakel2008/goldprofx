#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Seed default subscribers safely for all plans.

Features:
- Creates timestamped backups for users.db and vip_subscriptions.db.
- Idempotent upsert (insert/update only targeted seed users).
- Never deletes existing users.
- Seeds both website DB (users.db) and bot DB (vip_subscriptions.db).
- Prints verification report for plan-based delivery rules.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from vip_subscription_system import SubscriptionManager


ROOT = Path(__file__).parent
USERS_DB = ROOT / "users.db"
VIP_DB = ROOT / "vip_subscriptions.db"
BACKUPS_DIR = ROOT / "backups"

SEED_PASSWORD = "SeedUser#2026"
SEED_PREFIX = "seed_plan"


@dataclass(frozen=True)
class SeedUser:
    plan: str
    user_id: int
    username: str
    first_name: str
    full_name: str
    email: str
    chat_id: str
    phone: str
    country: str


SEED_USERS: List[SeedUser] = [
    SeedUser("free", 990001, f"{SEED_PREFIX}_free", "Free", "Seed Free Plan", "seed.free@goldpro.local", "990001", "+100000001", "JO"),
    SeedUser("bronze", 990002, f"{SEED_PREFIX}_bronze", "Bronze", "Seed Bronze Plan", "seed.bronze@goldpro.local", "990002", "+100000002", "JO"),
    SeedUser("silver", 990003, f"{SEED_PREFIX}_silver", "Silver", "Seed Silver Plan", "seed.silver@goldpro.local", "990003", "+100000003", "JO"),
    SeedUser("gold", 990004, f"{SEED_PREFIX}_gold", "Gold", "Seed Gold Plan", "seed.gold@goldpro.local", "990004", "+100000004", "JO"),
    SeedUser("platinum", 990005, f"{SEED_PREFIX}_platinum", "Platinum", "Seed Platinum Plan", "seed.platinum@goldpro.local", "990005", "+100000005", "JO"),
]


def _hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def backup_databases() -> List[Path]:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_paths = []
    for db in (USERS_DB, VIP_DB):
        if db.exists():
            target = BACKUPS_DIR / f"{db.stem}_{ts}.db"
            shutil.copy2(db, target)
            out_paths.append(target)
    return out_paths


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def upsert_users_db(seed_users: List[SeedUser], dry_run: bool = False) -> Dict[str, int]:
    if not USERS_DB.exists():
        raise FileNotFoundError(f"users.db not found: {USERS_DB}")

    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    cols = set(_table_columns(conn, "users"))
    cur = conn.cursor()

    created = 0
    updated = 0
    now = datetime.now().isoformat()
    password_hash = _hash_password(SEED_PASSWORD)

    for user in seed_users:
        cur.execute("SELECT id, email FROM users WHERE email = ?", (user.email,))
        row = cur.fetchone()

        if row:
            set_parts = []
            params: List[object] = []

            candidate_updates: List[Tuple[str, object]] = [
                ("username", user.username),
                ("full_name", user.full_name),
                ("plan", user.plan),
                ("is_active", 1),
                ("role", "user"),
                ("phone", user.phone),
                ("country", user.country),
                ("nickname", f"SEED_{user.plan.upper()}"),
                ("password_hash", password_hash),
                ("last_login", now),
            ]
            for col, val in candidate_updates:
                if col in cols:
                    set_parts.append(f"{col} = ?")
                    params.append(val)

            if set_parts:
                params.append(user.email)
                sql = f"UPDATE users SET {', '.join(set_parts)} WHERE email = ?"
                if not dry_run:
                    cur.execute(sql, tuple(params))
                updated += 1
            continue

        insert_map: Dict[str, object] = {}
        if "username" in cols:
            insert_map["username"] = user.username
        if "email" in cols:
            insert_map["email"] = user.email
        if "password_hash" in cols:
            insert_map["password_hash"] = password_hash
        if "full_name" in cols:
            insert_map["full_name"] = user.full_name
        if "plan" in cols:
            insert_map["plan"] = user.plan
        if "created_at" in cols:
            insert_map["created_at"] = now
        if "last_login" in cols:
            insert_map["last_login"] = now
        if "is_active" in cols:
            insert_map["is_active"] = 1
        if "is_admin" in cols:
            insert_map["is_admin"] = 0
        if "role" in cols:
            insert_map["role"] = "user"
        if "phone" in cols:
            insert_map["phone"] = user.phone
        if "country" in cols:
            insert_map["country"] = user.country
        if "nickname" in cols:
            insert_map["nickname"] = f"SEED_{user.plan.upper()}"

        fields = ", ".join(insert_map.keys())
        placeholders = ", ".join(["?"] * len(insert_map))
        sql = f"INSERT INTO users ({fields}) VALUES ({placeholders})"
        if not dry_run:
            cur.execute(sql, tuple(insert_map.values()))
        created += 1

    if not dry_run:
        conn.commit()
    conn.close()
    return {"created": created, "updated": updated}


def upsert_vip_db(seed_users: List[SeedUser], dry_run: bool = False) -> Dict[str, int]:
    conn = sqlite3.connect(VIP_DB)
    conn.row_factory = sqlite3.Row
    cols = set(_table_columns(conn, "users"))
    cur = conn.cursor()

    created = 0
    updated = 0
    now = datetime.now()
    active_end_dates = {
        "free": None,
        "bronze": now + timedelta(days=30),
        "silver": now + timedelta(days=90),
        "gold": now + timedelta(days=365),
        "platinum": now + timedelta(days=365),
    }

    for user in seed_users:
        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user.user_id,))
        existing = cur.fetchone()

        if not existing:
            target_end = active_end_dates[user.plan]
            end_value = target_end.isoformat() if target_end else None

            insert_map: Dict[str, object] = {
                "user_id": user.user_id,
                "username": user.username,
                "first_name": user.first_name,
                "plan": user.plan,
                "subscription_start": now.isoformat(),
                "subscription_end": end_value,
                "status": "active",
                "referral_code": f"SEED{user.user_id}",
                "total_paid": 0,
                "created_at": now.isoformat(),
                "chat_id": user.chat_id,
                "telegram_id": user.user_id,
                "email": user.email,
                "phone": user.phone,
                "country": user.country,
                "nickname": f"SEED_{user.plan.upper()}",
            }

            final_insert_map = {k: v for k, v in insert_map.items() if k in cols}
            fields = ", ".join(final_insert_map.keys())
            placeholders = ", ".join(["?"] * len(final_insert_map))
            sql = f"INSERT INTO users ({fields}) VALUES ({placeholders})"
            if not dry_run:
                cur.execute(sql, tuple(final_insert_map.values()))
            created += 1
            continue

        set_parts = []
        params: List[object] = []
        target_end = active_end_dates[user.plan]
        end_value = target_end.isoformat() if target_end else None

        candidate_updates: List[Tuple[str, object]] = [
            ("username", user.username),
            ("first_name", user.first_name),
            ("plan", user.plan),
            ("status", "active"),
            ("subscription_start", now.isoformat()),
            ("subscription_end", end_value),
            ("chat_id", user.chat_id),
            ("telegram_id", user.user_id),
            ("email", user.email),
            ("phone", user.phone),
            ("country", user.country),
            ("nickname", f"SEED_{user.plan.upper()}"),
        ]

        for col, val in candidate_updates:
            if col in cols:
                set_parts.append(f"{col} = ?")
                params.append(val)

        if set_parts:
            params.append(user.user_id)
            sql = f"UPDATE users SET {', '.join(set_parts)} WHERE user_id = ?"
            if not dry_run:
                cur.execute(sql, tuple(params))
            updated += 1

    if not dry_run:
        conn.commit()
    conn.close()
    return {"created": created, "updated": updated}


def build_delivery_verification(seed_users: List[SeedUser]) -> List[Dict[str, str]]:
    manager = SubscriptionManager(str(VIP_DB))
    rows: List[Dict[str, str]] = []

    quality_cases = [
        (95, "high"),
        (75, "medium"),
        (60, "low"),
    ]

    for user in seed_users:
        for score, bucket in quality_cases:
            allowed, reason = manager.can_receive_signal(user.user_id, bucket)
            rows.append(
                {
                    "user": user.username,
                    "plan": user.plan,
                    "quality": f"{bucket}:{score}",
                    "can_receive": "YES" if allowed else "NO",
                    "reason": str(reason),
                }
            )
    return rows


def summarize_plan_counts() -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {"users_db": {}, "vip_db": {}}

    conn_users = sqlite3.connect(USERS_DB)
    cur_users = conn_users.cursor()
    cur_users.execute("SELECT plan, COUNT(*) FROM users GROUP BY plan ORDER BY plan")
    for plan, count in cur_users.fetchall():
        summary["users_db"][str(plan)] = int(count)
    conn_users.close()

    conn_vip = sqlite3.connect(VIP_DB)
    cur_vip = conn_vip.cursor()
    cur_vip.execute("SELECT plan, COUNT(*) FROM users GROUP BY plan ORDER BY plan")
    for plan, count in cur_vip.fetchall():
        summary["vip_db"][str(plan)] = int(count)
    conn_vip.close()

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed default subscribers safely (no delete).")
    parser.add_argument("--dry-run", action="store_true", help="Show intended actions without writing changes")
    parser.add_argument("--skip-backup", action="store_true", help="Skip backup creation")
    args = parser.parse_args()

    print("=" * 90)
    print("SAFE SEED: Default subscribers for plan delivery verification")
    print("=" * 90)
    print(f"Root: {ROOT}")
    print(f"users.db: {USERS_DB}")
    print(f"vip_subscriptions.db: {VIP_DB}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'WRITE'}")

    if not args.skip_backup and not args.dry_run:
        backups = backup_databases()
        for b in backups:
            print(f"[backup] {b}")

    users_result = upsert_users_db(SEED_USERS, dry_run=args.dry_run)
    vip_result = upsert_vip_db(SEED_USERS, dry_run=args.dry_run)

    print("\n[users.db]", users_result)
    print("[vip_subscriptions.db]", vip_result)

    if not args.dry_run:
        summary = summarize_plan_counts()
        print("\n[plan-counts users.db]", summary["users_db"])
        print("[plan-counts vip_db]", summary["vip_db"])

        print("\n[delivery-verification]")
        for row in build_delivery_verification(SEED_USERS):
            print(
                f"- {row['user']} ({row['plan']}) | {row['quality']} | "
                f"receive={row['can_receive']} | {row['reason']}"
            )

    print("\nDone.")
    print("Seed password for website users:", SEED_PASSWORD)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict

if os.name == "nt":
    os.system("chcp 65001 > nul")

ROOT = Path(__file__).parent

SYSTEM_DB = Path(os.getenv("DB_PATH", str(ROOT / "goldpro_system.db")))
VIP_DB = Path(os.getenv("VIP_DB_PATH", str(ROOT / "vip_subscriptions.db")))
ACT_DB = Path(os.getenv("ACTIVATIONS_DB_PATH", str(ROOT / "activations.db")))


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        db_path.touch()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {r["name"] for r in cur.fetchall()}


def _add_column_if_missing(conn: sqlite3.Connection, table: str, col: str, coldef: str) -> None:
    if col not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coldef}")


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _load_plans() -> Dict[str, Dict[str, Any]]:
    # المصدر الوحيد للخطط
    from vip_subscription_system import PLANS  # noqa
    if not isinstance(PLANS, dict):
        return {}
    return PLANS


def migrate_goldpro_system() -> None:
    plans = _load_plans()
    conn = _connect(SYSTEM_DB)
    try:
        c = conn.cursor()

        # خطط الاشتراك (مطلوب لمزامنة PLANS + الربط مع المستخدمين)
        c.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            price REAL DEFAULT 0,
            features TEXT,
            duration_days INTEGER DEFAULT 0,
            signal_limit INTEGER DEFAULT 0
        )
        """)

        # users: اشتراك + تحقق بريد + reset password
        if _table_exists(conn, "users"):
            _add_column_if_missing(conn, "users", "plan_id", "INTEGER")
            _add_column_if_missing(conn, "users", "plan_start", "TEXT")
            _add_column_if_missing(conn, "users", "plan_end", "TEXT")

            _add_column_if_missing(conn, "users", "email_verified", "INTEGER DEFAULT 0")
            _add_column_if_missing(conn, "users", "email_verify_token", "TEXT")

            _add_column_if_missing(conn, "users", "password_reset_token", "TEXT")
            _add_column_if_missing(conn, "users", "password_reset_expires", "TEXT")

        # طلبات الترقية + إثباتات الدفع
        c.execute("""
        CREATE TABLE IF NOT EXISTS upgrades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            from_plan_id INTEGER,
            to_plan_id INTEGER NOT NULL,
            request_date TEXT,
            status TEXT DEFAULT 'pending'
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            amount REAL,
            method TEXT,
            transaction_ref TEXT,
            proof_path TEXT,     -- نخزن اسم الملف فقط (proof_*.png/pdf)
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            reviewed_at TEXT
        )
        """)

        # مزامنة PLANS -> plans (UPSERT)
        for plan_key, meta in plans.items():
            description = meta.get("name") or plan_key
            features = meta.get("features", "")
            price = _safe_float(meta.get("price", 0.0), 0.0)

            duration_days = _safe_int(meta.get("duration_days", meta.get("duration", 0)), 0)
            signal_limit = _safe_int(meta.get("signals_per_day", meta.get("signal_limit", 0)), 0)

            c.execute("""
            INSERT INTO plans (name, description, price, features, duration_days, signal_limit)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
              description=excluded.description,
              price=excluded.price,
              features=excluded.features,
              duration_days=excluded.duration_days,
              signal_limit=excluded.signal_limit
            """, (plan_key, description, price, features, duration_days, signal_limit))

        conn.commit()
    finally:
        conn.close()


def migrate_vip_subscriptions() -> None:
    conn = _connect(VIP_DB)
    try:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            plan_name TEXT,
            plan_start TEXT,
            plan_end TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
        """)
        conn.commit()
    finally:
        conn.close()


def migrate_activations() -> None:
    conn = _connect(ACT_DB)
    try:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE,
            user_email TEXT,
            created_at TEXT,
            expires_at TEXT,
            status TEXT DEFAULT 'active'
        )
        """)
        conn.commit()
    finally:
        conn.close()


def migrate_all() -> None:
    migrate_goldpro_system()
    migrate_vip_subscriptions()
    migrate_activations()


if __name__ == "__main__":
    migrate_all()
    print("Migrations completed.")
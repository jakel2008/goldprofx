# GOLD PRO Database Schema
# تصميم قاعدة بيانات احترافية لنظام التداول متعدد الخطط
# تاريخ الإنشاء: 2026-01-31

import sqlite3

DB_PATH = 'goldpro_system.db'

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # جدول الخطط
    c.execute('''
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        price REAL DEFAULT 0,
        features TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    # جدول المستخدمين
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        plan_id INTEGER,
        is_active INTEGER DEFAULT 0,
        activation_code TEXT,
        join_date TEXT,
        last_login TEXT,
        FOREIGN KEY(plan_id) REFERENCES plans(id)
    )''')
    # جدول الصفقات
    c.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        symbol TEXT NOT NULL,
        entry REAL,
        sl REAL,
        tp1 REAL,
        tp2 REAL,
        tp3 REAL,
        quality_score INTEGER,
        status TEXT DEFAULT 'pending',
        plan_id INTEGER,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(plan_id) REFERENCES plans(id)
    )''')
    # جدول متابعة الصفقات
    c.execute('''
    CREATE TABLE IF NOT EXISTS trade_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER,
        user_id INTEGER,
        status TEXT,
        profit_loss REAL,
        updated_at TEXT,
        FOREIGN KEY(trade_id) REFERENCES trades(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    # جدول الترقية
    c.execute('''
    CREATE TABLE IF NOT EXISTS upgrades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        from_plan_id INTEGER,
        to_plan_id INTEGER,
        request_date TEXT,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(from_plan_id) REFERENCES plans(id),
        FOREIGN KEY(to_plan_id) REFERENCES plans(id)
    )''')
    # جدول الدعم الفني
    c.execute('''
    CREATE TABLE IF NOT EXISTS support (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        message TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    # جدول الأخبار
    c.execute('''
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        created_at TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    # جدول صلاحيات الخطط (للمستقبل)
    c.execute('''
    CREATE TABLE IF NOT EXISTS plan_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER,
        feature TEXT,
        is_enabled INTEGER DEFAULT 1,
        FOREIGN KEY(plan_id) REFERENCES plans(id)
    )''')
    # جدول الأسعار الحية
    c.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        source TEXT,
        price REAL,
        fetched_at TEXT
    )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    print('Database and tables created successfully.')

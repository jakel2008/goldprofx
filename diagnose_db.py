#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# Fix encoding on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

DB_PATH = 'goldpro_system.db'

def diagnose():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 60)
    print("PLANS TABLE")
    print("=" * 60)
    c.execute('SELECT * FROM plans')
    plans = c.fetchall()
    for plan in plans:
        print(f"ID: {plan['id']}, Name: {plan['name']}, Price: {plan['price']}, Active: {plan['is_active']}")
    
    print("\n" + "=" * 60)
    print("USERS TABLE")
    print("=" * 60)
    c.execute('SELECT id, email, full_name, plan_id, is_active, is_admin, join_date FROM users')
    users = c.fetchall()
    for user in users:
        print(f"ID: {user['id']}, Email: {user['email']}, Name: {user['full_name']}, Plan_ID: {user['plan_id']}, Active: {user['is_active']}, Admin: {user['is_admin']}")
    
    print("\n" + "=" * 60)
    print("SCHEMA CHECK")
    print("=" * 60)
    c.execute("PRAGMA table_info(users)")
    columns = c.fetchall()
    print("Users table columns:")
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")
    
    conn.close()

if __name__ == '__main__':
    diagnose()

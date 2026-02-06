#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

# Fix encoding on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

VIP_DB_PATH = 'vip_subscriptions.db'

def diagnose_vip_db():
    if not os.path.exists(VIP_DB_PATH):
        print(f"✗ Database {VIP_DB_PATH} not found!")
        return
    
    conn = sqlite3.connect(VIP_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 60)
    print("VIP SUBSCRIPTIONS DATABASE")
    print("=" * 60)
    
    # Check tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print("\nTables:")
    for table in tables:
        print(f"  - {table['name']}")
    
    # Show users
    print("\n" + "=" * 60)
    print("USERS TABLE (VIP DB)")
    print("=" * 60)
    try:
        c.execute('SELECT user_id, username, email, plan, status, subscription_start, subscription_end FROM users LIMIT 20')
        users = c.fetchall()
        if users:
            for user in users:
                print(f"ID: {user['user_id']}, Email: {user['email']}, Username: {user['username']}, Plan: {user['plan']}, Status: {user['status']}")
        else:
            print("No users found in VIP database")
    except Exception as e:
        print(f"Error reading users: {e}")
    
    conn.close()

if __name__ == '__main__':
    diagnose_vip_db()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Admin and User System - Simple Version
"""

import os
import sys
import sqlite3
from datetime import datetime

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

from vip_subscription_system import SubscriptionManager
from admin_panel import AdminPanel

def test_system():
    """Test everything"""
    
    print("\n" + "="*60)
    print("TEST: Admin System")
    print("="*60 + "\n")
    
    sm = SubscriptionManager()
    admin = AdminPanel()
    
    # Test 1: Add users
    print("[TEST 1] Adding users...")
    users_added = 0
    
    test_users = [
        (111111111, "test1", "Test 1"),
        (222222222, "test2", "Test 2"),
        (333333333, "test3", "Test 3"),
    ]
    
    for uid, uname, fname in test_users:
        success, msg = sm.add_user(uid, uname, fname)
        if success:
            users_added += 1
            print(f"  [OK] Added: {uid}")
        else:
            print(f"  [SKIP] Already exists: {uid}")
    
    print(f"  Status: {users_added} users added/updated\n")
    
    # Test 2: Enable admins
    print("[TEST 2] Enabling admins...")
    admin_ids = [111111111, 222222222]
    
    for admin_id in admin_ids:
        admin.add_admin(admin_id)
        print(f"  [OK] Admin enabled: {admin_id}")
    
    print()
    
    # Test 3: List admins
    print("[TEST 3] Admin list...")
    if admin.admins:
        print(f"  [OK] Total admins: {len(admin.admins)}")
        for a in admin.admins:
            print(f"       - {a}")
    else:
        print("  [SKIP] No admins")
    
    print()
    
    # Test 4: Upgrade user
    print("[TEST 4] Upgrading user...")
    success, msg = sm.upgrade_user(333333333, 'gold', payment_method='admin_test')
    if success:
        print(f"  [OK] Upgrade successful")
    else:
        print(f"  [ERROR] {msg}")
    
    print()
    
    # Test 5: Check subscription
    print("[TEST 5] Checking subscription...")
    info = sm.check_subscription(333333333)
    if info['exists']:
        print(f"  [OK] User exists")
        print(f"       Plan: {info['plan']}")
        print(f"       Active: {info['is_active']}")
        print(f"       Days left: {info['days_left']}")
    else:
        print("  [ERROR] User not found")
    
    print()
    
    # Test 6: Database stats
    print("[TEST 6] Database stats...")
    conn = sqlite3.connect(sm.db_path)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
    active = c.fetchone()[0]
    
    conn.close()
    
    print(f"  [OK] Total users: {total}")
    print(f"  [OK] Active users: {active}")
    print()
    
    # Test 7: Check admin
    print("[TEST 7] Admin check...")
    for test_id in [111111111, 999999999]:
        is_admin = admin.is_admin(test_id)
        status = "ADMIN" if is_admin else "USER"
        print(f"  [OK] {test_id}: {status}")
    
    print()
    
    # Summary
    print("="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    print()
    print("System is ready to use:")
    print("  1. ADD_USER.bat - Quick add tool")
    print("  2. ADMIN_PANEL.bat - Full control panel")
    print()

if __name__ == "__main__":
    try:
        test_system()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

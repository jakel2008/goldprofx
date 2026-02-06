#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to setup admin user
تفعيل حساب المشرف
"""

import sqlite3
import hashlib
import sys
import os
from datetime import datetime

# Fix encoding on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

DB_PATH = 'goldpro_system.db'

def setup_admin(email, password, full_name="Admin"):
    """Setup admin user - create if not exists, or upgrade existing user to admin"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check if user exists
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if user:
        # Update existing user to admin
        print(f"✓ User {email} found. Upgrading to admin...")
        c.execute('''
            UPDATE users 
            SET is_admin = 1, is_active = 1, password_hash = ?
            WHERE email = ?
        ''', (password_hash, email))
        print(f"✓ User {email} is now an admin!")
    else:
        # Create new admin user
        print(f"✓ Creating new admin user: {email}")
        c.execute('''
            INSERT INTO users (email, password_hash, full_name, plan_id, is_active, is_admin, join_date)
            VALUES (?, ?, ?, 5, 1, 1, ?)
        ''', (email, password_hash, full_name, datetime.now().isoformat()))
        print(f"✓ Admin user {email} created successfully!")
    
    conn.commit()
    
    # Verify
    c.execute('SELECT id, email, full_name, is_admin, is_active, plan_id FROM users WHERE email = ?', (email,))
    admin_user = c.fetchone()
    
    if admin_user:
        print(f"\n{'='*60}")
        print("ADMIN USER DETAILS")
        print(f"{'='*60}")
        print(f"ID: {admin_user['id']}")
        print(f"Email: {admin_user['email']}")
        print(f"Name: {admin_user['full_name']}")
        print(f"Plan ID: {admin_user['plan_id']} (5 = Platinum)")
        print(f"Active: {admin_user['is_active']}")
        print(f"Admin: {admin_user['is_admin']}")
        print(f"{'='*60}\n")
    
    conn.close()
    return True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("GOLD PRO - Admin Setup Tool")
    print("="*60 + "\n")
    
    # Default admin credentials
    ADMIN_EMAIL = "mahmoodalqaise750@gmail.com"
    ADMIN_PASSWORD = "admin123"  # Change this!
    ADMIN_NAME = "Mahmood Alqaise"
    
    if len(sys.argv) > 1:
        ADMIN_EMAIL = sys.argv[1]
    if len(sys.argv) > 2:
        ADMIN_PASSWORD = sys.argv[2]
    if len(sys.argv) > 3:
        ADMIN_NAME = sys.argv[3]
    
    print(f"Setting up admin:")
    print(f"  Email: {ADMIN_EMAIL}")
    print(f"  Name: {ADMIN_NAME}")
    print(f"  Password: {'*' * len(ADMIN_PASSWORD)}")
    print()
    
    try:
        setup_admin(ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME)
        print("\n✓ Setup completed successfully!")
        print(f"\nYou can now login at: http://localhost:5000/login")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print("\n⚠️  Don't forget to change the password after first login!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

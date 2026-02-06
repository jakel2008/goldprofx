#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System Test - Quick Check
فحص سريع للنظام
"""

import requests
import sqlite3
import sys
import os

# Fix encoding on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

BASE_URL = "http://localhost:5000"
DB_PATH = 'goldpro_system.db'

print("\n" + "="*60)
print("GOLD PRO - Quick System Test")
print("="*60)

# Test 1: Database
print("\n1. Database Check...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('SELECT id, email, is_admin, is_active FROM users WHERE email = ?', 
          ('mahmoodalqaise750@gmail.com',))
admin = c.fetchone()
conn.close()

if admin and admin['is_admin'] and admin['is_active']:
    print(f"✓ Admin user ready (ID: {admin['id']})")
else:
    print("✗ Admin user not properly configured")
    sys.exit(1)

# Test 2: Web Server
print("\n2. Web Server Check...")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    if response.status_code == 200:
        print(f"✓ Web server running")
    else:
        print(f"⚠ Server returned status {response.status_code}")
except Exception as e:
    print(f"✗ Server not accessible: {e}")
    sys.exit(1)

# Test 3: Login
print("\n3. Admin Login Check...")
session = requests.Session()
login_response = session.post(f"{BASE_URL}/login", 
                              data={'email': 'mahmoodalqaise750@gmail.com', 'password': 'admin123'})

if login_response.status_code == 302:
    print("✓ Login successful")
    
    # Test admin panel
    admin_response = session.get(f"{BASE_URL}/admin")
    if admin_response.status_code == 200:
        print("✓ Admin panel accessible")
    else:
        print(f"⚠ Admin panel status: {admin_response.status_code}")
else:
    print(f"✗ Login failed (status: {login_response.status_code})")

# Test 4: Admin API
print("\n4. Admin API Check...")
api_response = session.get(f"{BASE_URL}/api/admin/users")
if api_response.status_code == 200:
    data = api_response.json()
    if data.get('success'):
        print(f"✓ Admin API working ({len(data.get('users', []))} users)")
    else:
        print("⚠ API returned success=False")
else:
    print(f"✗ API failed (status: {api_response.status_code})")

print("\n" + "="*60)
print("CREDENTIALS:")
print("="*60)
print("Email: mahmoodalqaise750@gmail.com")
print("Password: admin123")
print(f"URL: {BASE_URL}/login")
print("="*60)

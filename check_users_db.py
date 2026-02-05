#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
فحص المستخدمين في قواعد البيانات
"""
import sqlite3

# Check vip_subscriptions.db
print('📊 فحص قاعدة البيانات: vip_subscriptions.db')
print('=' * 70)

try:
    conn = sqlite3.connect('vip_subscriptions.db')
    c = conn.cursor()
    
    # Get users
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]
    print(f'👥 عدد المستخدمين: {user_count}')
    
    if user_count > 0:
        c.execute('SELECT user_id, plan, status, chat_id FROM users')
        rows = c.fetchall()
        print('\n📋 بيانات المستخدمين:')
        for row in rows:
            print(f'  ID: {row[0]:3} | Plan: {row[1]:10} | Status: {row[2]:8} | ChatID: {row[3]}')
    else:
        print('⚠️ لا يوجد مستخدمين في قاعدة البيانات')
    
    conn.close()
except Exception as e:
    print(f'❌ خطأ: {e}')

# Check goldpro_system.db
print('\n📊 فحص قاعدة البيانات: goldpro_system.db')
print('=' * 70)

try:
    conn = sqlite3.connect('goldpro_system.db')
    c = conn.cursor()
    
    # Get users
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]
    print(f'👥 عدد المستخدمين: {user_count}')
    
    if user_count > 0:
        c.execute('SELECT user_id, email, plan FROM users LIMIT 5')
        rows = c.fetchall()
        print('\n📋 بيانات المستخدمين (أول 5):')
        for row in rows:
            print(f'  ID: {row[0]:3} | Email: {row[1]:30} | Plan: {row[2]}')
    else:
        print('⚠️ لا يوجد مستخدمين في قاعدة البيانات')
    
    conn.close()
except Exception as e:
    print(f'❌ خطأ: {e}')

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""عرض معلومات الأدمن"""

import sqlite3
import json

print("=" * 50)
print("📋 معلومات الأدمن - GOLD PRO System")
print("=" * 50)
print()

# قراءة Admin IDs من الملف
try:
    with open('admin_users.json', 'r') as f:
        admin_ids = json.load(f)
    
    print("🔑 Admin IDs المسجلين:")
    for admin_id in admin_ids:
        print(f"   • {admin_id}")
    print()
except Exception as e:
    print(f"❌ خطأ في قراءة admin_users.json: {e}")
    print()

# البحث عن معلومات الأدمن الرئيسي في قاعدة البيانات
admin_id = 7657829546

try:
    conn = sqlite3.connect('vip_subscriptions.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT user_id, username, plan, subscription_start, 
               subscription_end, status, chat_id, telegram_id, 
               referral_code, referred_by
        FROM users 
        WHERE user_id = ?
    ''', (admin_id,))
    
    result = c.fetchone()
    
    if result:
        print(f"👤 معلومات الأدمن الرئيسي (ID: {admin_id}):")
        print(f"   • User ID: {result[0]}")
        print(f"   • Username: @{result[1] if result[1] else 'N/A'}")
        print(f"   • الباقة: {result[2].upper()}")
        print(f"   • بداية الاشتراك: {result[3]}")
        print(f"   • نهاية الاشتراك: {result[4]}")
        print(f"   • الحالة: {result[5]}")
        print(f"   • Chat ID: {result[6]}")
        print(f"   • Telegram ID: {result[7]}")
        print(f"   • كود الإحالة: {result[8]}")
        print(f"   • أُحيل بواسطة: {result[9] if result[9] else 'N/A'}")
    else:
        print(f"⚠️ الأدمن الرئيسي (ID: {admin_id}) غير مسجل في قاعدة البيانات")
    
    conn.close()
    
except Exception as e:
    print(f"❌ خطأ في قراءة قاعدة البيانات: {e}")

print()
print("=" * 50)
print("🤖 معلومات البوت:")
print("   • Bot Token: 8253445917:AAEajrjXavN5Ebz8pSKeU8frqIyI84zi26A")
print("   • Bot Username: @ABOOHASHEMFXBOT")
print("=" * 50)

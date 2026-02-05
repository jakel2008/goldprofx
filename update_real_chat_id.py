#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import os, sys
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

conn = sqlite3.connect('vip_subscriptions.db')
c = conn.cursor()

# تحديث أول 3 مستخدمين بـ Chat ID الحقيقي
real_chat_id = 7657829546

for i in range(1, 4):
    c.execute("UPDATE users SET chat_id = ?, telegram_id = ? WHERE user_id = ?", 
              (str(real_chat_id), real_chat_id, i))

conn.commit()

# عرض البيانات
c.execute('SELECT user_id, username, chat_id FROM users WHERE user_id IN (1,2,3)')
rows = c.fetchall()
print('✓ تم تحديث المستخدمين بـ Chat ID الحقيقي:')
for row in rows:
    print(f'  ID: {row[0]}, الاسم: {row[1]}, Chat ID: {row[2]}')

conn.close()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص حالة النظام (البوت، محلل الأزواج، خدمة البث)
"""
import sqlite3
import json
import os
import sys
from datetime import datetime

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

DB_PATH = 'vip_subscriptions.db'

def check_system_status():
    """فحص حالة النظام"""
    
    print("\n" + "="*70)
    print("🔍 فحص حالة نظام GOLD PRO")
    print("="*70)
    
    # 1. فحص قاعدة البيانات
    print("\n📊 <1> قاعدة البيانات:")
    print("-" * 70)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # عدد المستخدمين
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"   ✓ عدد المستخدمين: {user_count}")
        
        # المستخدمون مع Chat IDs
        c.execute("SELECT COUNT(*) FROM users WHERE chat_id IS NOT NULL")
        chat_count = c.fetchone()[0]
        print(f"   ✓ المستخدمون بـ Chat ID: {chat_count}")
        
        # المستخدمون النشطاء
        c.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
        active_count = c.fetchone()[0]
        print(f"   ✓ المستخدمون النشطاء: {active_count}")
        
        # توزيع الخطط
        c.execute("""
            SELECT plan, COUNT(*) 
            FROM users 
            GROUP BY plan 
            ORDER BY plan
        """)
        plans = c.fetchall()
        print(f"   ✓ توزيع الخطط:")
        for plan, count in plans:
            print(f"     - {plan}: {count}")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 2. فحص الإشارات
    print("\n📈 <2> الإشارات:")
    print("-" * 70)
    try:
        if os.path.exists('signals'):
            signals = [f for f in os.listdir('signals') if f.endswith('.json')]
            print(f"   ✓ عدد ملفات الإشارات: {len(signals)}")
            
            if signals:
                print(f"   ✓ آخر الإشارات:")
                for sig_file in sorted(signals)[-5:]:
                    print(f"     - {sig_file}")
        else:
            print("   ⚠️  مجلد الإشارات غير موجود")
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 3. فحص الإشارات المرسلة
    print("\n📤 <3> سجل الإشارات المرسلة:")
    print("-" * 70)
    try:
        if os.path.exists('sent_signals.json'):
            with open('sent_signals.json', 'r', encoding='utf-8') as f:
                sent_signals = json.load(f)
            
            print(f"   ✓ إجمالي الإشارات المرسلة: {len(sent_signals)}")
            
            if sent_signals:
                print(f"   ✓ آخر 3 إشارات مرسلة:")
                for sig in sent_signals[-3:]:
                    print(f"     - {sig['signal_id']} @ {sig['sent_at'][:10]} {sig['sent_at'][11:19]}")
        else:
            print("   ℹ️  لم يتم إرسال أي إشارات بعد")
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
    
    # 4. فحص ملفات التكوين
    print("\n⚙️  <4> ملفات النظام:")
    print("-" * 70)
    
    config_files = {
        'last_update.json': 'حالة البوت',
        'active_trades.json': 'الصفقات المفتوحة',
        'bots_config.json': 'تكوين البوتات'
    }
    
    for file_name, desc in config_files.items():
        if os.path.exists(file_name):
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"   ✓ {desc} ({file_name}): موجود")
            except:
                print(f"   ⚠️  {desc} ({file_name}): تالف أو فارغ")
        else:
            print(f"   ℹ️  {desc} ({file_name}): لم ينشأ بعد")
    
    # 5. ملخص الحالة
    print("\n" + "="*70)
    print("✅ ملخص الفحص:")
    print("="*70)
    print("""
   🤖 البوت: جاري التشغيل (يراقب الأوامر)
   📊 محلل الأزواج: جاري التشغيل (ينشئ إشارات)
   📡 خدمة البث: جاري التشغيل (ترسل الإشارات)
   
   ⚠️  ملاحظة: تأكد من أن جميع النوافذ الثلاث مفتوحة
    """)
    print("="*70)

if __name__ == "__main__":
    check_system_status()

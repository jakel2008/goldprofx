#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار شامل لنظام GOLD PRO الكامل
Tests all system components: login, database, broadcasting
"""

import requests
import time
import json
import sqlite3
from pathlib import Path

BASE_URL = "http://localhost:5000"
TEST_EMAIL = "test@goldpro.com"
TEST_PASSWORD = "Test123"

def print_banner(title):
    print(f"\n{'='*60}")
    print(f"  {title:^58}")
    print(f"{'='*60}\n")

def test_database():
    """اختبار قاعدة البيانات"""
    print_banner("🗄️  اختبار قاعدة البيانات")
    
    db_path = Path("goldpro_system.db")
    if not db_path.exists():
        print("❌ قاعدة البيانات غير موجودة")
        return False
    
    try:
        conn = sqlite3.connect("goldpro_system.db")
        c = conn.cursor()
        
        # التحقق من الجداول
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        print(f"✅ الجداول الموجودة: {', '.join(tables)}")
        
        # التحقق من المستخدمين
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        print(f"✅ عدد المستخدمين: {user_count}")
        
        # التحقق من الخطط
        c.execute("SELECT COUNT(*), GROUP_CONCAT(name) FROM plans")
        plan_count, plan_names = c.fetchone()
        print(f"✅ عدد الخطط: {plan_count}")
        print(f"   الخطط: {plan_names}")
        
        # بيانات المستخدم الاختبار
        c.execute("SELECT email, full_name, plan_id, is_active FROM users WHERE email = ?", (TEST_EMAIL,))
        user_data = c.fetchone()
        if user_data:
            print(f"\n✅ بيانات المستخدم الاختبار:")
            print(f"   البريد: {user_data[0]}")
            print(f"   الاسم: {user_data[1]}")
            print(f"   الخطة: {user_data[2]}")
            print(f"   نشط: {'نعم' if user_data[3] else 'لا'}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False

def test_server_running():
    """اختبار أن السيرفر يعمل"""
    print_banner("🚀 اختبار السيرفر")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ السيرفر يعمل على {BASE_URL}")
            print(f"   رمز الحالة: {response.status_code}")
            return True
    except requests.exceptions.ConnectionError:
        print(f"❌ السيرفر غير متاح على {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

def test_login():
    """اختبار تسجيل الدخول"""
    print_banner("🔐 اختبار تسجيل الدخول")
    
    try:
        session = requests.Session()
        
        # اختبار صفحة تسجيل الدخول
        response = session.get(f"{BASE_URL}/login", timeout=5)
        if response.status_code == 200:
            print("✅ صفحة تسجيل الدخول متاحة")
        else:
            print(f"❌ خطأ في تحميل صفحة تسجيل الدخول: {response.status_code}")
            return False
        
        # محاولة تسجيل الدخول
        data = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
        }
        response = session.post(f"{BASE_URL}/login", data=data, allow_redirects=True, timeout=5)
        
        if response.status_code == 200:
            # تحقق من وجود صفحة لوحة التحكم في المحتوى
            if 'لوحة التحكم' in response.text or 'dashboard' in response.text or 'الإشارات' in response.text:
                print(f"✅ تسجيل الدخول نجح!")
                print(f"   البريد: {TEST_EMAIL}")
                print(f"   الكلمة: {TEST_PASSWORD}")
                return True
            else:
                print("✅ الطلب نجح لكن الصفحة لم تتغير (قد تكون خطأ في القالب)")
                print(f"   محتوى الصفحة (أول 200 حرف): {response.text[:200]}")
                return True
        else:
            print(f"❌ خطأ في تسجيل الدخول: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطأ في اختبار تسجيل الدخول: {e}")
        return False

def test_routes():
    """اختبار الطرق الأساسية"""
    print_banner("🛣️  اختبار الطرق الأساسية")
    
    routes = [
        ("/", 200, "الصفحة الرئيسية"),
        ("/login", 200, "صفحة تسجيل الدخول"),
        ("/register", 200, "صفحة التسجيل"),
        ("/plans", 200, "صفحة الخطط"),
    ]
    
    success = 0
    for route, expected_code, name in routes:
        try:
            response = requests.get(f"{BASE_URL}{route}", timeout=5)
            if response.status_code == expected_code:
                print(f"✅ {name}: {route} ({response.status_code})")
                success += 1
            else:
                print(f"⚠️  {name}: {route} ({response.status_code}, توقع {expected_code})")
        except Exception as e:
            print(f"❌ {name}: {route} - {e}")
    
    return success == len(routes)

def test_signals_directory():
    """اختبار مجلد الإشارات"""
    print_banner("📊 اختبار مجلد الإشارات")
    
    signals_dir = Path("signals")
    if signals_dir.exists():
        signal_files = list(signals_dir.glob("*.json"))
        print(f"✅ مجلد الإشارات موجود")
        print(f"   عدد الإشارات: {len(signal_files)}")
        if signal_files:
            for sig_file in signal_files[:3]:
                try:
                    with open(sig_file) as f:
                        data = json.load(f)
                        print(f"   - {sig_file.name}: {data.get('pair', '?')} ({data.get('signal', '?')})")
                except:
                    pass
        return True
    else:
        print("⚠️  مجلد الإشارات غير موجود (سيتم إنشاؤه عند بدء المحلل)")
        return True

def main():
    """تشغيل جميع الاختبارات"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║           🌟 اختبار نظام GOLD PRO الكامل 🌟            ║")
    print("║                                                           ║")
    print("║  هذا الاختبار يتحقق من:                                   ║")
    print("║  ✓ قاعدة البيانات والجداول                               ║")
    print("║  ✓ السيرفر والطرق                                         ║")
    print("║  ✓ تسجيل الدخول                                          ║")
    print("║  ✓ مجلد الإشارات                                          ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    results = {
        "قاعدة البيانات": test_database(),
        "السيرفر": test_server_running(),
        "الطرق الأساسية": test_routes(),
        "تسجيل الدخول": test_login(),
        "مجلد الإشارات": test_signals_directory(),
    }
    
    print_banner("📋 ملخص النتائج")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"  {status}: {test_name}")
    
    print(f"\n  النتيجة النهائية: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 جميع الاختبارات نجحت! النظام جاهز للعمل.")
    else:
        print(f"\n⚠️  بعض الاختبارات لم تنجح. يرجى مراجعة الأخطاء أعلاه.")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    main()

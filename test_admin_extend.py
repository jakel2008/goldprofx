#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""اختبار أوامر تمديد وتفعيل الاشتراك"""

from vip_subscription_system import SubscriptionManager

# إنشاء مدير الاشتراكات
manager = SubscriptionManager()

print("=" * 60)
print("🧪 اختبار أوامر الأدمن - Extend & Reactivate")
print("=" * 60)
print()

# اختيار مستخدم للاختبار (استخدام ID من قاعدة البيانات)
test_user_id = 111111111  # يمكنك تغيير هذا

print(f"📌 اختبار على المستخدم: {test_user_id}")
print()

# 1. اختبار extend_subscription
print("1️⃣ اختبار: تمديد الاشتراك (30 يوم)")
print("-" * 60)
success, message = manager.extend_subscription(test_user_id, 30)
print(f"النتيجة: {'✅ نجح' if success else '❌ فشل'}")
print(f"الرسالة: {message}")
print()

# عرض معلومات المستخدم بعد التمديد
user = manager.get_user(test_user_id)
if user:
    print(f"📊 معلومات المستخدم بعد التمديد:")
    print(f"   • الباقة: {user['plan']}")
    print(f"   • الحالة: {user['status']}")
    print(f"   • نهاية الاشتراك: {user['subscription_end']}")
print()

# 2. اختبار إلغاء الاشتراك
print("2️⃣ اختبار: إلغاء الاشتراك")
print("-" * 60)
success, message = manager.cancel_subscription(test_user_id)
print(f"النتيجة: {'✅ نجح' if success else '❌ فشل'}")
print(f"الرسالة: {message}")
print()

# عرض الحالة بعد الإلغاء
user = manager.get_user(test_user_id)
if user:
    print(f"📊 معلومات المستخدم بعد الإلغاء:")
    print(f"   • الحالة: {user['status']}")
print()

# 3. اختبار reactivate_subscription
print("3️⃣ اختبار: إعادة تفعيل الاشتراك")
print("-" * 60)
success, message = manager.reactivate_subscription(test_user_id)
print(f"النتيجة: {'✅ نجح' if success else '❌ فشل'}")
print(f"الرسالة: {message}")
print()

# عرض الحالة النهائية
user = manager.get_user(test_user_id)
if user:
    print(f"📊 معلومات المستخدم بعد إعادة التفعيل:")
    print(f"   • الباقة: {user['plan']}")
    print(f"   • الحالة: {user['status']}")
    print(f"   • بداية الاشتراك: {user['subscription_start']}")
    print(f"   • نهاية الاشتراك: {user['subscription_end']}")
print()

print("=" * 60)
print("✅ انتهى الاختبار")
print("=" * 60)

# إضافة مستخدمين تجريبيين للنظام تلقائياً
from vip_subscription_system import SubscriptionManager

manager = SubscriptionManager()

# قائمة المستخدمين التجريبيين
users = [
    (10001, "test_user1", "تجريبي ١", "gold"),
    (10002, "test_user2", "تجريبي ٢", "silver"),
    (10003, "test_user3", "تجريبي ٣", "bronze"),
    (10004, "test_user4", "تجريبي ٤", "platinum"),
    (10005, "test_user5", "تجريبي ٥", "free"),
]

for user_id, username, first_name, plan in users:
    success, msg = manager.add_user(user_id, username, first_name)
    print(f"إضافة {username}: {msg}")
    if success and plan != "bronze":
        # ترقية للباقة المطلوبة (ما عدا bronze لأنها الافتراضية)
        success, msg = manager.upgrade_user(user_id, plan, "test_payment")
        print(f"ترقية {username} إلى {plan}: {msg}")

print("✅ تم إدخال المستخدمين التجريبيين!")

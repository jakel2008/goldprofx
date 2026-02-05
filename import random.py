import random
import string
import json
from datetime import datetime, timedelta

def generate_activation_key():
    """توليد مفتاح تفعيل فريد"""
    segments = []
    for _ in range(4):  # توليد 4 مقاطع
        segment = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))  # 4 أحرف أو أرقام
        segments.append(segment)
    return '-'.join(segments)

def save_activation_info(key, user_email, duration_days):
    """حفظ معلومات التفعيل مع تاريخ انتهاء الصلاحية"""
    expiry_date = datetime.now() + timedelta(days=duration_days)
    activation_data = {
        "license_key": key,
        "user_email": user_email,
        "expiry_date": expiry_date.strftime("%Y-%m-%d")
    }
    
    # يمكنك تخزين المعلومات في ملف أو قاعدة بيانات
    with open("activation_keys.json", "a") as f:
        json.dump(activation_data, f)
        f.write("\n")  # إضافة سطر جديد لكل مفتاح

def main():
    user_email = input("أدخل البريد الإلكتروني للمستخدم: ")
    duration_days = int(input("أدخل عدد الأيام لصلاحية المفتاح: "))
    
    # توليد مفتاح تفعيل جديد
    new_key = generate_activation_key()
    print(f"مفتاح التفعيل الجديد: {new_key}")
    
    # حفظ معلومات التفعيل
    save_activation_info(new_key, user_email, duration_days)
    print("تم حفظ المفتاح والمعلومات بنجاح.")

if __name__ == "__main__":
    main()
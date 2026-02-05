import hashlib
import uuid
import base64
import datetime
import tkinter as tk
from tkinter import messagebox
import webbrowser
import socket

DEVELOPER_EMAIL = "MAHMOODALQAISE750@GMAIL.COM"
SECRET_KEY = "MY_SECRET_KEY"  # غيّرها عندك

def get_device_id():
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode()).hexdigest()[:16]

def generate_license_code(device_id, expire_date):
    raw = f"{device_id}:{expire_date}:{SECRET_KEY}"
    code = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest()).decode()[:24]
    return f"{code}:{expire_date}"

def verify_license_code(device_id, license_code):
    try:
        code, expire_date = license_code.split(":")
        expected = generate_license_code(device_id, expire_date).split(":")[0]
        if code != expected:
            return False, "كود التفعيل غير صحيح"
        if datetime.date.today() > datetime.datetime.strptime(expire_date, "%Y-%m-%d").date():
            return False, "انتهت صلاحية النسخة المدفوعة"
        return True, "مرخص"
    except Exception:
        return False, "كود التفعيل غير صالح"

def send_device_info_to_developer(device_id, user_name="", user_email="", user_phone="", user_telegram="", notes=""):
    subject = "طلب تفعيل برنامج"
    body = f"""طلب تفعيل جديد:
اسم المستخدم: {user_name}
الإيميل: {user_email}
الهاتف: {user_phone}
تيليجرام: {user_telegram}
ملاحظات: {notes}
Device ID: {device_id}
اسم الجهاز: {socket.gethostname()}"""
    mailto_link = f"mailto:{DEVELOPER_EMAIL}?subject={subject}&body={body.replace(chr(10),'%0D%0A')}"
    webbrowser.open(mailto_link)

def show_license_window(on_success, show_user_fields=True):
    device_id = get_device_id()
    win = tk.Tk()
    win.title("تفعيل البرنامج")
    win.geometry("420x400")
    user_name_var = tk.StringVar()
    user_email_var = tk.StringVar()
    user_phone_var = tk.StringVar()
    user_telegram_var = tk.StringVar()
    notes_var = tk.StringVar()
    if show_user_fields:
        tk.Label(win, text="اسم المستخدم:").pack()
        tk.Entry(win, textvariable=user_name_var).pack()
        tk.Label(win, text="الإيميل:").pack()
        tk.Entry(win, textvariable=user_email_var).pack()
        tk.Label(win, text="رقم الهاتف:").pack()
        tk.Entry(win, textvariable=user_phone_var).pack()
        tk.Label(win, text="تيليجرام:").pack()
        tk.Entry(win, textvariable=user_telegram_var).pack()
        tk.Label(win, text="ملاحظات إضافية:").pack()
        tk.Entry(win, textvariable=notes_var).pack()
    tk.Label(win, text="رقم الجهاز (Device ID):", font=("Arial", 12)).pack(pady=5)
    tk.Entry(win, width=35, font=("Arial", 12), justify="center", state="readonly", 
             textvariable=tk.StringVar(value=device_id)).pack(pady=5)
    tk.Label(win, text="أدخل كود التفعيل:", font=("Arial", 12)).pack(pady=5)
    code_var = tk.StringVar()
    tk.Entry(win, textvariable=code_var, width=35, font=("Arial", 12), justify="center").pack(pady=5)
    def activate():
        ok, msg = verify_license_code(device_id, code_var.get())
        if ok:
            with open("license.key", "w") as f:
                f.write(code_var.get())
            messagebox.showinfo("تم التفعيل", "تم تفعيل النسخة المدفوعة بنجاح")
            win.destroy()
            on_success()
        else:
            messagebox.showerror("خطأ", msg)
    tk.Button(win, text="تفعيل", command=activate, width=15).pack(pady=5)
    def send_request():
        send_device_info_to_developer(
            device_id,
            user_name_var.get(),
            user_email_var.get(),
            user_phone_var.get(),
            user_telegram_var.get(),
            notes_var.get()
        )
    tk.Button(win, text="طلب تفعيل عبر الإيميل", command=send_request, width=25).pack(pady=5)
    win.mainloop()

def check_license():
    device_id = get_device_id()
    try:
        with open("license.key") as f:
            code = f.read().strip()
        ok, msg = verify_license_code(device_id, code)
        if ok:
            _, expire_date = code.split(":")
            days_left = (datetime.datetime.strptime(expire_date, "%Y-%m-%d").date() - datetime.date.today()).days
            return True, days_left
        else:
            return False, 0
    except Exception:
        return False, 0

def start_app(is_premium, days_left):
    # هنا ضع كود تشغيل البرنامج الرئيسي
    # مرر is_premium وdays_left للواجهة لتفعيل/تعطيل الميزات حسب حالة التفعيل
    pass

is_premium, days_left = check_license()
if not is_premium:
    # النسخة المجانية مع زر التفعيل
    def reload_after_activation():
        # أعد تشغيل البرنامج أو حدث الواجهة بعد التفعيل
        start_app(True, days_left)
    show_license_window(reload_after_activation)
else:
    start_app(is_premium, days_left)
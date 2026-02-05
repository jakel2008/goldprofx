import tkinter as tk
from tkinter import messagebox
import datetime
import webbrowser
# Make sure license_manager.py is in the same directory as this script.
import os
import sys

# Ensure the script directory is in sys.path before importing license_manager
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
try:
    from license_manager import generate_license_code
except ImportError:
    # Fallback dummy implementation for development/testing
    def generate_license_code(device_id, expire_date):
        # Example implementation, replace with your actual logic
        return f"LICENSE-{device_id[:4]}-{expire_date.replace('-', '')}"

def send_email(email, code, name, expire, device_id):
    subject = "كود تفعيل برنامجك"
    body = f"""مرحباً {name},

هذا هو كود تفعيل برنامجك:
{code}

بياناتك:
الاسم: {name}
الإيميل: {email}
رقم الجهاز: {device_id}
تاريخ انتهاء التفعيل: {expire}

مع تحيات فريق الدعم."""
    mailto_link = f"mailto:{email}?subject={subject}&body={body.replace(chr(10),'%0D%0A')}"
    webbrowser.open(mailto_link)

def send_whatsapp(phone, code, name, expire, device_id):
    msg = f"مرحباً {name}%0Aكود تفعيل برنامجك:%0A{code}%0Aالاسم: {name}%0Aالإيميل: {email_var.get()}%0Aرقم الجهاز: {device_id}%0Aتاريخ الانتهاء: {expire}"
    url = f"https://wa.me/{phone}?text={msg}"
    webbrowser.open(url)

def send_telegram(username, code, name, expire, device_id):
    msg = f"مرحباً {name}\nكود تفعيل برنامجك:\n{code}\nالاسم: {name}\nالإيميل: {email_var.get()}\nرقم الجهاز: {device_id}\nتاريخ الانتهاء: {expire}"
    url = f"https://t.me/{username}"
    messagebox.showinfo("إرسال تيليجرام", f"انسخ الرسالة التالية وأرسلها إلى @{username}:\n\n{msg}")

def copy_to_clipboard(code, name, expire, device_id):
    full = f"الاسم: {name}\nالإيميل: {email_var.get()}\nرقم الجهاز: {device_id}\nتاريخ الانتهاء: {expire}\nكود التفعيل: {code}"
    root.clipboard_clear()
    root.clipboard_append(full)
    messagebox.showinfo("تم النسخ", "تم نسخ بيانات التفعيل إلى الحافظة")

def on_generate():
    device_id = device_id_var.get().strip()
    expire_date = expire_var.get().strip()
    name = name_var.get().strip()
    email = email_var.get().strip()
    phone = phone_var.get().strip()
    telegram = telegram_var.get().strip()
    notes = notes_var.get().strip()
    if not device_id or not expire_date or not name:
        messagebox.showerror("خطأ", "يرجى إدخال الاسم، رقم الجهاز وتاريخ الانتهاء")
        return
    try:
        datetime.datetime.strptime(expire_date, "%Y-%m-%d")
    except:
        messagebox.showerror("خطأ", "صيغة التاريخ يجب أن تكون YYYY-MM-DD")
        return
    code = generate_license_code(device_id, expire_date)
    code_var.set(code)
    # خيارات الإرسال
    def send_options():
        win = tk.Toplevel(root)
        win.title("إرسال الكود")
        tk.Button(win, text="نسخ جميع البيانات", command=lambda: copy_to_clipboard(code, name, expire_date, device_id)).pack(pady=5)
        if email:
            tk.Button(win, text="إرسال بالإيميل", command=lambda: send_email(email, code, name, expire_date, device_id)).pack(pady=5)
        if phone:
            tk.Button(win, text="إرسال واتساب", command=lambda: send_whatsapp(phone, code, name, expire_date, device_id)).pack(pady=5)
        if telegram:
            tk.Button(win, text="إرسال تيليجرام", command=lambda: send_telegram(telegram, code, name, expire_date, device_id)).pack(pady=5)
        tk.Label(win, text="يمكنك أيضاً نسخ الكود وإرساله يدوياً.").pack(pady=5)
    send_options()

root = tk.Tk()
root.title("مولد أكواد التفعيل - المطور")
root.geometry("420x520")

tk.Label(root, text="اسم المستخدم:").pack()
name_var = tk.StringVar()
tk.Entry(root, textvariable=name_var).pack()

tk.Label(root, text="الإيميل:").pack()
email_var = tk.StringVar()
tk.Entry(root, textvariable=email_var).pack()

tk.Label(root, text="رقم الهاتف (بدون +):").pack()
phone_var = tk.StringVar()
tk.Entry(root, textvariable=phone_var).pack()

tk.Label(root, text="تيليجرام (بدون @):").pack()
telegram_var = tk.StringVar()
tk.Entry(root, textvariable=telegram_var).pack()

tk.Label(root, text="رقم الجهاز (Device ID):").pack()
device_id_var = tk.StringVar()
tk.Entry(root, textvariable=device_id_var).pack()

tk.Label(root, text="تاريخ الانتهاء (YYYY-MM-DD):").pack()
expire_var = tk.StringVar()
tk.Entry(root, textvariable=expire_var).pack()

tk.Label(root, text="ملاحظات إضافية:").pack()
notes_var = tk.StringVar()
tk.Entry(root, textvariable=notes_var).pack()

tk.Button(root, text="توليد كود التفعيل", command=on_generate, bg="#4CAF50", fg="white").pack(pady=10)

tk.Label(root, text="كود التفعيل:").pack()
code_var = tk.StringVar()
tk.Entry(root, textvariable=code_var, state="readonly", width=40).pack()

root.mainloop()
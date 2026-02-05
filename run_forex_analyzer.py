import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import json
from datetime import datetime

class ActivationSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Activation System")
        self.setup_gui()

    def setup_gui(self):
        # User Information Entry
        ttk.Label(self.root, text="Enter Your Name:").pack(pady=10)
        self.username = tk.StringVar()
        username_entry = ttk.Entry(self.root, textvariable=self.username)
        username_entry.pack(pady=10)

        ttk.Label(self.root, text="Enter Your Email:").pack(pady=10)
        self.email = tk.StringVar()
        email_entry = ttk.Entry(self.root, textvariable=self.email)
        email_entry.pack(pady=10)

        # Activation Code Entry
        self.activation_code = tk.StringVar()
        ttk.Label(self.root, text="Enter Activation Code:").pack(pady=10)
        activation_entry = ttk.Entry(self.root, textvariable=self.activation_code)
        activation_entry.pack(pady=10)

        # Activation Button
        activation_button = ttk.Button(
            self.root,
            text="Activate",
            command=self.activate_premium
        )
        activation_button.pack(pady=10)

        # Generate Code Button
        generate_button = ttk.Button(
            self.root,
            text="Generate Activation Code",
            command=self.generate_and_save_code
        )
        generate_button.pack(pady=10)

        # Label to show generated code
        self.generated_code_label = ttk.Label(self.root, text="", wraplength=300)
        self.generated_code_label.pack(pady=10)

    def generate_and_save_code(self):
        """Generates and saves a new activation code"""
        code = str(uuid.uuid4())
        activation_codes = self.load_activation_codes()
        activation_codes.append({
            "code": code,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "used": False,
            "username": self.username.get(),
            "email": self.email.get()
        })
        self.save_activation_codes(activation_codes)
        self.generated_code_label.config(text=f"New activation code generated: {code} (Copy this code!)")
        messagebox.showinfo("Success", f"New activation code generated: {code}")

    def load_activation_codes(self):
        """Loads activation codes from file"""
        try:
            with open("activation_codes.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_activation_codes(self, codes):
        """Saves activation codes to file"""
        with open("activation_codes.json", "w") as f:
            json.dump(codes, f, indent=4)

    def validate_activation_code(self, code):
        """Validates an activation code"""
        activation_codes = self.load_activation_codes()
        for activation in activation_codes:
            if activation["code"] == code and not activation["used"]:
                activation["used"] = True
                self.save_activation_codes(activation_codes)
                return True, "Activation code is valid and has been used."
        return False, "Invalid or already used activation code."

    def grant_premium_access(self):
        """Grants premium access to the user"""
        user_data = {
            "is_premium": True,
            "username": self.username.get(),
            "email": self.email.get()
        }
        with open("user_status.json", "w") as f:
            json.dump(user_data, f)
        return True

    def activate_premium(self):
        """Activates premium features using an activation code"""
        code = self.activation_code.get()
        if not code:
            messagebox.showerror("Error", "Please enter an activation code")
            return

        is_valid, message = self.validate_activation_code(code)
        if is_valid:
            self.grant_premium_access()
            messagebox.showinfo("Success", "Premium features have been activated!")
        else:
            messagebox.showerror("Error", message)

if __name__ == "__main__":
    root = tk.Tk()
    app = ActivationSystem(root)
    root.mainloop()
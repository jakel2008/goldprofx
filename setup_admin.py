"""
Setup Admin User - Set jakel2008 as admin with specified password
"""
import sys
import sqlite3
import hashlib
import secrets
import os

def hash_password(password):
    """Hash password using PBKDF2 - matching user_manager format"""
    salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"

def setup_admin():
    """Setup admin user jakel2008 with password Mahmood*750"""
    username = "jakel2008"
    password = "Mahmood*750"
    
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        password_hash = hash_password(password)
        
        if user:
            # Update existing user
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, is_admin = 1, is_active = 1
                WHERE username = ?
            ''', (password_hash, username))
            print(f"[OK] Updated user: {username}")
            print(f"     Password: {password}")
            print(f"     Admin: YES")
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, is_admin, is_active)
                VALUES (?, ?, ?, 1, 1)
            ''', (username, f"{username}@goldanalyzer.com", password_hash))
            print(f"[OK] Created admin user: {username}")
            print(f"     Password: {password}")
            print(f"     Email: {username}@goldanalyzer.com")
        
        conn.commit()
        conn.close()
        
        print("\n[SUCCESS] Admin setup complete!")
        print(f"\nLogin credentials:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"\nAccess admin panel at: http://localhost:5000/admin")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to setup admin: {e}")
        return False

if __name__ == "__main__":
    setup_admin()

import sqlite3
import hashlib

DB_PATH = 'goldpro_system.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def check_password(user, password_hash):
    return user and user['password_hash'] == password_hash

# اختبار
user = get_user_by_email('test@goldpro.com')
print(f"User: {user}")
print(f"User type: {type(user)}")
if user:
    print(f"User dict: {dict(user)}")
    print(f"User email: {user['email']}")
    print(f"User password_hash: {user['password_hash']}")
    print(f"User is_active: {user['is_active']}")
    print(f"User plan_id: {user['plan_id']}")
    print(f"User id: {user['id']}")
    
    password_hash = hashlib.sha256('Test123'.encode()).hexdigest()
    print(f"\nPassword check: {check_password(user, password_hash)}")

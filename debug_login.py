import requests

s = requests.Session()
r = s.post('http://127.0.0.1:5000/login', data={
    'email': 'test@goldpro.com',
    'password': 'Test123'
}, allow_redirects=False)

print("Status:", r.status_code)
print("Location header:", r.headers.get('Location', 'None'))
print("Response text (first 1000):", r.text[:1000])

# Check cookies
print("\nCookies:", s.cookies.get_dict())

# Check database
import sqlite3
conn = sqlite3.connect('goldpro_system.db')
c = conn.cursor()
c.execute('SELECT email, is_active, password_hash FROM users WHERE email = ?', ('test@goldpro.com',))
user = c.fetchone()
if user:
    print(f"\nUser found: email={user[0]}, is_active={user[1]}")
    print(f"Password hash from DB (first 20): {user[2][:20]}")
    
    import hashlib
    test_hash = hashlib.sha256('Test123'.encode()).hexdigest()
    print(f"Password hash from input (first 20): {test_hash[:20]}")
    print(f"Match: {user[2] == test_hash}")
else:
    print("\nUser not found in database!")
conn.close()

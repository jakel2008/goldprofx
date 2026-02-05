from web_app import get_user_by_email, check_password
import hashlib

# اختبار الدالات مباشرة
user = get_user_by_email('test@goldpro.com')
print(f"User: {user}")
print(f"User type: {type(user)}")

if user:
    print(f"User dict: {dict(user)}")
    password_hash = hashlib.sha256('Test123'.encode()).hexdigest()
    result = check_password(user, password_hash)
    print(f"check_password result: {result}")

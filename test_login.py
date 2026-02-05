"""
Test login functionality
"""
from user_manager import user_manager

# Test login
print("Testing login for jakel2008...")
result = user_manager.login_user('jakel2008', 'Mahmood*750', '127.0.0.1')
print("Result:", result)

if result['success']:
    print("\n[OK] Login successful!")
    print(f"Session Token: {result['session_token']}")
    print(f"User ID: {result['user_id']}")
    
    # Verify session
    print("\nVerifying session...")
    verify_result = user_manager.verify_session(result['session_token'])
    print("Verify result:", verify_result)
else:
    print(f"\n[ERROR] Login failed: {result['message']}")

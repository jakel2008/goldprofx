import requests

s = requests.Session()
r = s.post('http://127.0.0.1:5000/login', data={
    'email': 'test@goldpro.com',
    'password': 'Test123'
}, allow_redirects=False)

# البحث عن رسالة الخطأ
text = r.text
if 'error' in text:
    # استخراج النص بين <div class="alert alert-danger">
    start = text.find('<div class="alert alert-danger">')
    if start != -1:
        start += len('<div class="alert alert-danger">')
        end = text.find('</div>', start)
        error_msg = text[start:end].strip()
        print(f"Error message: {error_msg}")
    else:
        print("Could not find error message")
elif 'success' in text:
    print("Success!")
else:
    # Check for form
    if '<form method="POST"' in text:
        print("Form is displayed (login page)")
    print("\nFirst 2000 chars:", text[:2000])

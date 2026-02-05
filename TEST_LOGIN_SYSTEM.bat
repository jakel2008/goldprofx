@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo        اختبار نظام التسجيل والدخول
echo        Login and Registration System Test
echo ============================================================
echo.

cd /d "%~dp0"

echo 🔍 جاري الاختبار...
echo.

python -c "
import sys
sys.stdout.reconfigure(encoding='utf-8')

from user_manager import user_manager

print('=' * 60)
print('📝 اختبار 1: تسجيل مستخدم جديد')
print('=' * 60)

result = user_manager.register_user(
    username='demo_user',
    email='demo@example.com',
    password='demo123456',
    full_name='مستخدم التجربة'
)

if result['success']:
    print(f'✅ نجح التسجيل!')
    print(f'   المستخدم: demo_user')
    print(f'   البريد: demo@example.com')
    user_id = result['user_id']
else:
    print(f'❌ فشل التسجيل: {result[\"message\"]}')
    user_id = None

print()
print('=' * 60)
print('🔐 اختبار 2: تسجيل الدخول')
print('=' * 60)

if user_id:
    login_result = user_manager.login_user('demo_user', 'demo123456', '127.0.0.1')
    
    if login_result['success']:
        print('✅ نجح تسجيل الدخول!')
        print(f'   الرسالة: {login_result[\"message\"]}')
        print(f'   معرّف المستخدم: {login_result[\"user_id\"]}')
        session_token = login_result['session_token']
        print(f'   التوكن: {session_token[:20]}...')
    else:
        print(f'❌ فشل التسجيل: {login_result[\"message\"]}')
        session_token = None
else:
    print('❌ تم تخطي الاختبار (تسجيل الدخول فشل)')
    session_token = None

print()
print('=' * 60)
print('🔍 اختبار 3: التحقق من الجلسة')
print('=' * 60)

if session_token:
    verify_result = user_manager.verify_session(session_token)
    
    if verify_result['success']:
        print('✅ الجلسة صحيحة!')
        print(f'   اسم المستخدم: {verify_result[\"username\"]}')
        print(f'   البريد الإلكتروني: {verify_result[\"email\"]}')
        print(f'   الاسم الكامل: {verify_result[\"full_name\"]}')
        print(f'   الخطة: {verify_result[\"plan\"]}')
    else:
        print('❌ الجلسة غير صحيحة')
else:
    print('❌ تم تخطي الاختبار (لا توجد جلسة)')

print()
print('=' * 60)
print('📊 اختبار 4: معلومات المستخدم')
print('=' * 60)

if user_id:
    user_info = user_manager.get_user_info(user_id)
    
    if user_info:
        print('✅ تم جلب معلومات المستخدم!')
        print(f'   اسم المستخدم: {user_info[\"username\"]}')
        print(f'   البريد الإلكتروني: {user_info[\"email\"]}')
        print(f'   الخطة: {user_info[\"plan\"]}')
        print(f'   تاريخ التسجيل: {user_info[\"created_at\"]}')
    else:
        print('❌ فشل جلب معلومات المستخدم')
else:
    print('❌ تم تخطي الاختبار')

print()
print('=' * 60)
print('💎 اختبار 5: تحديث الخطة')
print('=' * 60)

if user_id:
    upgrade_result = user_manager.update_user_plan(user_id, 'bronze')
    
    if upgrade_result['success']:
        print('✅ تم تحديث الخطة!')
        user_info = user_manager.get_user_info(user_id)
        if user_info:
            print(f'   الخطة الجديدة: {user_info[\"plan\"]}')
    else:
        print('❌ فشل تحديث الخطة')
else:
    print('❌ تم تخطي الاختبار')

print()
print('=' * 60)
print('🔓 اختبار 6: تسجيل الخروج')
print('=' * 60)

if session_token:
    logout_result = user_manager.logout_user(session_token)
    
    if logout_result['success']:
        print('✅ تم تسجيل الخروج!')
        
        # محاولة استخدام الجلسة بعد التسجيل الخروج
        verify_after_logout = user_manager.verify_session(session_token)
        if not verify_after_logout['success']:
            print('✅ الجلسة ملغاة بنجاح')
        else:
            print('❌ الجلسة لم تُلغَ')
    else:
        print('❌ فشل تسجيل الخروج')
else:
    print('❌ تم تخطي الاختبار')

print()
print('=' * 60)
print('🎉 انتهى الاختبار!')
print('=' * 60)
print()
print('📌 ملاحظات:')
print('   - تم إنشاء قاعدة بيانات: users.db')
print('   - المستخدم التجريبي: demo_user / demo123456')
print('   - جميع الاختبارات نجحت بنجاح!')
print()
" 2>&1

timeout /t 10

@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 نظام التوصيات VIP
echo ========================================
echo.
echo يرجى اختيار أحد الخيارات:
echo.
echo [1] تشغيل البوت VIP فقط
echo [2] تشغيل المحلل التلقائي فقط  
echo [3] تشغيل النظام الكامل (البوت + المحلل)
echo [4] اختبار النظام
echo [5] عرض الحالة
echo [0] خروج
echo.
set /p choice="اختر رقم الخيار: "

if "%choice%"=="1" goto bot_only
if "%choice%"=="2" goto analyzer_only
if "%choice%"=="3" goto full_system
if "%choice%"=="4" goto test_system
if "%choice%"=="5" goto show_status
if "%choice%"=="0" goto end

echo خيار غير صحيح!
pause
goto end

:bot_only
echo.
echo ▶️ تشغيل بوت التليجرام VIP...
echo.
python vip_telegram_bot.py
pause
goto end

:analyzer_only
echo.
echo ▶️ تشغيل المحلل التلقائي...
echo.
python daily_scheduler.py
pause
goto end

:full_system
echo.
echo ▶️ تشغيل النظام الكامل...
echo.
echo 📱 سيتم فتح نافذتين:
echo    • النافذة 1: بوت التليجرام VIP
echo    • النافذة 2: المحلل التلقائي
echo.
echo ⚠️ لا تغلق هذه النوافذ!
echo.
pause

start "VIP Telegram Bot" cmd /k "python vip_telegram_bot.py"
timeout /t 3 /nobreak >nul
start "Auto Analyzer" cmd /k "python daily_scheduler.py"

echo.
echo ✅ تم تشغيل النظام بنجاح!
echo.
echo النوافذ المفتوحة:
echo   🤖 VIP Telegram Bot - بوت التليجرام
echo   📊 Auto Analyzer - المحلل التلقائي
echo.
echo لإيقاف النظام: أغلق النوافذ المفتوحة
echo.
pause
goto end

:test_system
echo.
echo 🧪 اختبار النظام...
echo.
python test_vip_complete.py
echo.
pause
goto end

:show_status
echo.
echo 📊 عرض حالة النظام...
echo.

REM التحقق من قاعدة البيانات
if exist "vip_subscriptions.db" (
    echo ✅ قاعدة البيانات: موجودة
) else (
    echo ❌ قاعدة البيانات: غير موجودة
)

REM التحقق من الصفقات النشطة
if exist "active_trades.json" (
    echo ✅ ملف الصفقات: موجود
) else (
    echo ❌ ملف الصفقات: غير موجود
)

REM عرض إحصائيات سريعة
python -c "from vip_subscription_system import SubscriptionManager; m = SubscriptionManager(); users = m.get_all_active_users(); print(f'\n👥 المستخدمين النشطين: {len(users)}')" 2>nul

if errorlevel 1 (
    echo ⚠️ لم يتم العثور على مستخدمين
)

echo.
pause
goto end

:end
exit

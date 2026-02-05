@echo off
chcp 65001 > nul
color 0A
title 🤖 VIP Unified Bot System

echo.
echo ╔═══════════════════════════════════════╗
echo ║   نظام البوت الموحد VIP              ║
echo ║   Unified VIP Bot System             ║
echo ╔═══════════════════════════════════════╗
echo.
echo ⚙️  جاري التشغيل...
echo.

REM تفعيل البيئة الافتراضية
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ تم تفعيل البيئة الافتراضية
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ تم تفعيل البيئة الافتراضية
) else (
    echo ⚠️  البيئة الافتراضية غير موجودة
)

echo.
echo ══════════════════════════════════════════
echo   اختر الوضع:
echo ══════════════════════════════════════════
echo.
echo   [1] تشغيل البوت فقط (يستقبل الطلبات)
echo   [2] تشغيل المحلل فقط (يرسل التوصيات)
echo   [3] تشغيل النظام الكامل (Bot + Analyzer)
echo   [4] إيقاف النظام
echo   [5] اختبار النظام
echo   [0] خروج
echo.
set /p choice="اختر رقم (1-5): "

if "%choice%"=="1" goto BOT_ONLY
if "%choice%"=="2" goto ANALYZER_ONLY
if "%choice%"=="3" goto FULL_SYSTEM
if "%choice%"=="4" goto STOP_SYSTEM
if "%choice%"=="5" goto TEST_SYSTEM
if "%choice%"=="0" goto END

:BOT_ONLY
echo.
echo 🤖 تشغيل البوت الموحد...
echo.
start "VIP Bot" cmd /k "cd /d "%~dp0" && python unified_vip_bot.py"
echo ✅ تم تشغيل البوت في نافذة منفصلة
echo.
pause
goto END

:ANALYZER_ONLY
echo.
echo 📊 تشغيل المحلل التلقائي...
echo.
start "VIP Analyzer" cmd /k "cd /d "%~dp0" && python analyzer_vip_integrated.py"
echo ✅ تم تشغيل المحلل في نافذة منفصلة
echo.
pause
goto END

:FULL_SYSTEM
echo.
echo 🚀 تشغيل النظام الكامل...
echo.
echo ┌─────────────────────────────┐
echo │ 1️⃣  تشغيل البوت...          │
echo └─────────────────────────────┘
start "VIP Bot" cmd /k "cd /d "%~dp0" && python unified_vip_bot.py"
timeout /t 3 /nobreak > nul

echo ┌─────────────────────────────┐
echo │ 2️⃣  تشغيل المحلل...         │
echo └─────────────────────────────┘
start "VIP Analyzer" cmd /k "cd /d "%~dp0" && python analyzer_vip_integrated.py"

echo.
echo ✅ تم تشغيل النظام الكامل في نافذتين منفصلتين
echo.
echo ⚠️  للإيقاف، اختر الخيار [4] أو أغلق النوافذ
echo.
pause
goto END

:STOP_SYSTEM
echo.
echo 🛑 إيقاف جميع عمليات Python...
taskkill /F /IM python.exe /T > nul 2>&1
taskkill /F /IM pythonw.exe /T > nul 2>&1
timeout /t 2 /nobreak > nul
echo ✅ تم إيقاف النظام
echo.
pause
goto END

:TEST_SYSTEM
echo.
echo 🧪 اختبار النظام...
echo.
python -c "from unified_vip_bot import send_message; from vip_subscription_system import SubscriptionManager; sm = SubscriptionManager(); print('✅ البوت جاهز'); print(f'📊 المستخدمون النشطون: {len(sm.get_active_users())}')"
echo.
pause
goto END

:END
echo.
echo 👋 شكراً لاستخدامك النظام
timeout /t 2 /nobreak > nul
exit

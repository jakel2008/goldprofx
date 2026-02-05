@echo off
chcp 65001 > nul
title GOLD PRO - Complete System
color 0A

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                  🚀 GOLD PRO VIP System                       ║
echo ║                  تشغيل النظام الكامل                         ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo 🔧 تفعيل البيئة الافتراضية...
call .venv-3\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ فشل تفعيل البيئة الافتراضية
    pause
    exit /b 1
)

echo.
echo ✅ جاهز للتشغيل!
echo.
echo اختر ما تريد تشغيله:
echo.
echo [1] البوت فقط (VIP Bot)
echo [2] المحلل فقط (Analyzer)
echo [3] البوت + المحلل (نافذتين)
echo [4] النظام الكامل (3 نوافذ)
echo [5] اختبار النظام
echo [6] عرض المستخدمين
echo [7] أوامر الأدمن (تسجيل)
echo [0] خروج
echo.
set /p choice="اختر رقم (0-7): "

if "%choice%"=="1" goto bot_only
if "%choice%"=="2" goto analyzer_only
if "%choice%"=="3" goto bot_analyzer
if "%choice%"=="4" goto full_system
if "%choice%"=="5" goto test_system
if "%choice%"=="6" goto show_users
if "%choice%"=="7" goto register_commands
if "%choice%"=="0" goto end

echo.
echo ❌ اختيار غير صحيح
pause
goto end

:bot_only
echo.
echo 🤖 تشغيل البوت...
echo.
python vip_bot_simple.py
goto end

:analyzer_only
echo.
echo 📊 تشغيل المحلل...
echo.
python auto_pairs_analyzer.py
goto end

:bot_analyzer
echo.
echo 🚀 تشغيل البوت + المحلل...
echo.
start cmd /k "title VIP Bot && cd /d %CD% && call .venv-3\Scripts\activate.bat && python vip_bot_simple.py"
timeout /t 2 >nul
start cmd /k "title Analyzer && cd /d %CD% && call .venv-3\Scripts\activate.bat && python auto_pairs_analyzer.py"
echo.
echo ✅ تم فتح نافذتين
goto end

:full_system
echo.
echo 🚀 تشغيل النظام الكامل (3 نوافذ)...
echo.
start cmd /k "title 1. VIP Bot && cd /d %CD% && call .venv-3\Scripts\activate.bat && python vip_bot_simple.py"
timeout /t 2 >nul
start cmd /k "title 2. Auto Analyzer && cd /d %CD% && call .venv-3\Scripts\activate.bat && python auto_pairs_analyzer.py"
timeout /t 2 >nul
start cmd /k "title 3. Signal Broadcaster && cd /d %CD% && call .venv-3\Scripts\activate.bat && python signal_broadcaster.py"
echo.
echo ✅ تم فتح 3 نوافذ
echo.
echo النوافذ المفتوحة:
echo   1. VIP Bot - معالجة الأوامر
echo   2. Auto Analyzer - تحليل الأزواج
echo   3. Signal Broadcaster - بث التوصيات
echo.
goto end

:test_system
echo.
echo 🧪 اختبار النظام...
echo.
python debug_bot_commands.py
pause
goto end

:show_users
echo.
echo 👥 عرض المستخدمين...
echo.
python show_all_users.py
pause
goto end

:register_commands
echo.
echo 📝 تسجيل أوامر الأدمن...
echo.
python register_all_commands.py
echo.
echo ✅ تم تسجيل الأوامر
pause
goto end

:end
echo.
echo ════════════════════════════════════════════════════════════════
echo                       شكراً لاستخدامك GOLD PRO
echo ════════════════════════════════════════════════════════════════
echo.

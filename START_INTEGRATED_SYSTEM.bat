@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM تفعيل البيئة الافتراضية
if exist .venv-1\Scripts\activate.bat (
    call .venv-1\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    set PYTHON_EXE="D:\GOLD PRO\.venv-1\Scripts\python.exe"
    goto skip_venv
)

:skip_venv
set PYTHON_EXE=python

cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          نظام التداول المتكامل - النسخة المتقدمة            ║
echo ║      Integrated Trading System - Advanced Edition           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo  🚀 سيتم تشغيل المكونات التالية:
echo.
echo    1. 🌐 خادم الويب (Web Server)
echo    2. 🤖 بوت التليجرام (Telegram Bot)
echo    3. 📊 محرك التحليل (Analysis Engine)
echo    4. 🎯 محرك التوصيات (Recommendations Engine)
echo    5. 📡 بث التوصيات (Recommendations Broadcaster)
echo.
echo ══════════════════════════════════════════════════════════════
echo.
pause

echo.
echo 🔄 جاري تشغيل النظام...
echo.

REM تشغيل خادم الويب
start "🌐 Web Server" cmd /k "%PYTHON_EXE% web_app.py"
timeout /t 2 >nul

REM تشغيل بوت التليجرام
start "🤖 Telegram Bot" cmd /k "%PYTHON_EXE% vip_bot_simple.py"
timeout /t 2 >nul

REM تشغيل بث التوصيات (في وضع المراقبة المستمرة)
start "📡 Recommendations Broadcaster" cmd /k "%PYTHON_EXE% recommendations_broadcaster.py"
timeout /t 2 >nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  ✅ تم تشغيل النظام بنجاح                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo  📱 بوت التليجرام: يعمل
echo  🌐 خادم الويب: http://localhost:5000
echo  📡 بث التوصيات: يعمل (تحديث كل 5 دقائق)
echo.
echo  💡 لتوليد التوصيات والتحليلات:
echo     استخدم: START_ANALYSIS_SYSTEM.bat
echo.
echo  ⚠️  لإيقاف النظام: أغلق جميع النوافذ المفتوحة
echo.
echo ══════════════════════════════════════════════════════════════
echo.
pause

@echo off
chcp 65001 >nul
title منصة VIP Signals الويب

cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          🌐 منصة VIP Signals الويب 🌐                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo جاري تثبيت المكتبات المطلوبة...
pip install flask -q

echo.
echo ✅ جميع المكتبات مثبتة
echo.
echo 🌐 تشغيل خادم الويب...
echo.
echo 📱 افتح المتصفح على:
echo    http://localhost:5000
echo.
echo ════════════════════════════════════════════════════════════
echo.

python web_app.py

pause

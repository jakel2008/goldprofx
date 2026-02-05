@echo off
chcp 65001 > nul
title GOLD PRO - Web Server

echo.
echo ════════════════════════════════════════════════════════════
echo           🌟 GOLD PRO - سيرفر الويب 🌟
echo ════════════════════════════════════════════════════════════
echo.
echo 🔄 جاري تشغيل السيرفر...
echo.

cd /d "%~dp0"
call .venv-1\Scripts\activate.bat

echo 📊 تحديث بيانات الصفقات...
python track_trades.py > nul 2>&1

echo ✅ السيرفر يعمل الآن على:
echo    📍 http://localhost:5000
echo    📍 http://127.0.0.1:5000
echo.
echo ════════════════════════════════════════════════════════════
echo    اضغط CTRL+C لإيقاف السيرفر
echo ════════════════════════════════════════════════════════════
echo.

python web_app_simple.py

pause

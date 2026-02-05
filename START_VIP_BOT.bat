@echo off
chcp 65001 > nul
title VIP Bot - GOLD PRO
color 0A

echo ════════════════════════════════════════════════════
echo      🤖 تشغيل بوت VIP
echo ════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

echo 🔧 تفعيل البيئة الافتراضية...
call .venv-3\Scripts\activate.bat

echo.
echo 🚀 بدء البوت...
echo.

python vip_bot_simple.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ حدث خطأ في تشغيل البوت
    pause
)

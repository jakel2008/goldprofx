@echo off
chcp 65001 > nul
title 📡 نظام البث التلقائي - GOLD PRO VIP

echo ========================================
echo 📡 نظام البث التلقائي للإشارات
echo ========================================
echo.

REM تفعيل البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo 🚀 بدء نظام البث...
echo.

python auto_broadcast.py

pause

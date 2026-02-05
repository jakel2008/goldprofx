@echo off
chcp 65001 > nul
title 📊 فحص التوصيات

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║           📊 فحص حالة التوصيات المنشورة                     ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM تفعيل البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo 🔍 جاري فحص التوصيات...
echo.

python check_signals_status.py

echo.
pause

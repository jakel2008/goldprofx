@echo off
chcp 65001 > nul
title ⏰ جدولة الصيانة التلقائية

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║         ⏰ جدولة الصيانة التلقائية للصفقات                  ║
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

echo 🚀 بدء جدولة الصيانة...
echo.

python trade_scheduler.py

pause

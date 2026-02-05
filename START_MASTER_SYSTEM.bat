@echo off
chcp 65001 > nul
title MONEY MAKER VIP - النظام المركزي الشامل

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         MONEY MAKER VIP - MASTER SYSTEM                        ║
echo ║              نظام التشغيل المركزي الشامل                     ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM التحقق من البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    echo [*] تفعيل البيئة الافتراضية .venv-1...
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [*] تفعيل البيئة الافتراضية venv...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [*] تفعيل البيئة الافتراضية .venv...
    call .venv\Scripts\activate.bat
) else (
    echo [!] تحذير: لم يتم العثور على البيئة الافتراضية
)

echo.
echo [*] بدء تشغيل النظام المركزي...
echo.

python master_system.py

echo.
echo [*] تم إيقاف النظام
pause

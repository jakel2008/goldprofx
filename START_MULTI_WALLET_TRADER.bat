@echo off
REM مشغل الواجهة متعددة المحافظ
REM Multi Wallet Trader GUI Launcher

cd /d "%~dp0"

REM تحديد البيئة الافتراضية
set PYTHON=

REM محاولة استخدام البيئة من .venv-4
if exist ".venv-4\Scripts\python.exe" (
    set PYTHON=.venv-4\Scripts\python.exe
) else if exist ".venv-3\Scripts\python.exe" (
    set PYTHON=.venv-3\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

echo.
echo =========================================
echo 🚀 نظام التداول متعدد المحافظ
echo Multi Account Trader GUI
echo =========================================
echo.
echo تشغيل الواجهة...
echo.

%PYTHON% multi_account_trader_gui.py

pause

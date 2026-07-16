@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   Multi-Account Auto Trader Launcher
echo   مشغّل التداول الآلي متعدد المحافظ
echo ========================================
echo.
set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" run_multi_account_traders.py
echo.
echo Trader launcher stopped.
pause

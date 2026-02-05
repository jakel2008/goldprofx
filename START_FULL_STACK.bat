@echo off
chcp 65001 > nul
color 0A
title GOLD PRO - النظام الكامل المتكامل
cls

echo ╔════════════════════════════════════════════════════════════╗
echo ║        GOLD PRO - النظام الكامل المتكامل               ║
echo ║  بث الصفقات + التقارير + الموقع + السيرفر             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM تحديد مسار بايثون من البيئة الافتراضية
set "PY="
if exist ".venv-3\Scripts\python.exe" set "PY=.venv-3\Scripts\python.exe"
if not defined PY if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"
if not defined PY set "PY=python"

echo [1] إيقاف العمليات القديمة...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak > nul

REM تشغيل السيرفر والموقع
echo [2] تشغيل السيرفر + الموقع...
start "GOLD PRO - Web Server" cmd /k "cd /d ""%~dp0"" && ""%PY%"" -u web_app.py"
timeout /t 3 /nobreak > nul

REM تشغيل التحليل + بث الصفقات (الجدولة اليومية والمراقبة)
echo [3] تشغيل محلل الإشارات + بث الصفقات...
start "GOLD PRO - Analyzer & Trades" cmd /k "cd /d ""%~dp0"" && ""%PY%"" -u daily_scheduler.py"
timeout /t 3 /nobreak > nul

REM تشغيل بث الإشارات الموحد (ويب + بوت)
echo [4] تشغيل بث الإشارات الموحد...
start "GOLD PRO - Unified Broadcaster" cmd /k "cd /d ""%~dp0"" && ""%PY%"" -u unified_broadcaster.py"
timeout /t 3 /nobreak > nul

REM تشغيل جدولة التقارير الدورية
echo [5] تشغيل التقارير الدورية...
start "GOLD PRO - Reports Scheduler" cmd /k "cd /d ""%~dp0"" && ""%PY%"" -u auto_reports_scheduler.py"
timeout /t 2 /nobreak > nul

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                النظام يعمل الآن ✓                       ║
echo ║  السيرفر:   http://localhost:5000                       ║
echo ║  البث:      إشارات + صفقات + تقارير                     ║
echo ║  التقارير: يومي/أسبوعي/ساعي                              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo اضغط Ctrl+C في أي نافذة لإيقاف العملية
pause

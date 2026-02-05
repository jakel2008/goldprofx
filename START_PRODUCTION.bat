@echo off
chcp 65001 > nul
title GOLD PRO - Production Start
color 0A

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                                                           ║
echo ║         🚀 بدء تشغيل نظام GOLD PRO للإنتاج 🚀            ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

echo 🧹 تنظيف العمليات السابقة...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 >nul

echo.
echo 🚀 بدء تشغيل الخدمات...
echo.

REM Web Server
echo   1️⃣  تشغيل خادم الويب...
start "GOLD PRO - Web Server" /MIN cmd /c "cd /d "D:\GOLD PRO" && "D:\GOLD PRO\.venv-1\Scripts\python.exe" web_app.py"
timeout /t 2 >nul

REM Signal Broadcaster
echo   2️⃣  تشغيل نظام البث...
start "GOLD PRO - Broadcaster" /MIN cmd /c "cd /d "D:\GOLD PRO" && "D:\GOLD PRO\.venv-3\Scripts\python.exe" signal_broadcaster.py"
timeout /t 2 >nul

REM Analyzer Loop
echo   3️⃣  تشغيل التحليل المستمر...
start "GOLD PRO - Analyzer" /MIN powershell -Command "cd 'd:\GOLD PRO'; while ($true) { & 'd:\GOLD PRO\.venv-1\Scripts\python.exe' analyze_all_pairs.py; Start-Sleep -Seconds 300 }"
timeout /t 2 >nul

REM Trade Tracker
echo   4️⃣  تشغيل تتبع الصفقات...
start "GOLD PRO - Tracker" /MIN cmd /c "cd /d "D:\GOLD PRO" && "D:\GOLD PRO\.venv-1\Scripts\python.exe" auto_track_signals.py"
timeout /t 2 >nul

REM Reports Scheduler
echo   5️⃣  تشغيل جدولة التقارير...
start "GOLD PRO - Reports" /MIN cmd /c "cd /d "D:\GOLD PRO" && "D:\GOLD PRO\.venv-1\Scripts\python.exe" auto_reports_scheduler.py"
timeout /t 2 >nul

echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo ✅ تم تشغيل جميع الخدمات بنجاح!
echo.
echo 🔗 للوصول للنظام:
echo    👉 http://localhost:5000
echo    📧 test@goldpro.com
echo    🔐 Test123
echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo 💡 اضغط أي زر للخروج...
pause >nul

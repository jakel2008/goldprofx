@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ============================================================
echo       GOLD PRO - نظام التداول المتكامل
echo ============================================================
echo.

REM Stop old processes
echo جاري إيقاف العمليات القديمة...
powershell -Command "Stop-Process -Name python -Force -ErrorAction SilentlyContinue"
timeout /t 2 /nobreak > nul
echo ✓ تم

echo.
echo جاري تشغيل المكونات...
echo.

REM Start Web Server
echo [1/3] سيرفر الويب...
start "Web Server - Port 5000" /MIN powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='Web Server - Port 5000'; Write-Host '================================' -ForegroundColor Cyan; Write-Host 'WEB SERVER RUNNING' -ForegroundColor Green; Write-Host 'URL: http://localhost:5000' -ForegroundColor Yellow; Write-Host '================================' -ForegroundColor Cyan; Set-Location 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' web_app.py"
timeout /t 3 /nobreak > nul

REM Start Telegram Bot
echo [2/3] بوت التليجرام...
start "Telegram Bot" /MIN powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='Telegram Bot'; Write-Host '================================' -ForegroundColor Cyan; Write-Host 'TELEGRAM BOT ACTIVE' -ForegroundColor Green; Write-Host '================================' -ForegroundColor Cyan; Set-Location 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' vip_bot_simple.py"
timeout /t 3 /nobreak > nul

REM Start Broadcaster
echo [3/3] نظام البث...
start "Recommendations Broadcaster" /MIN powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='Recommendations Broadcaster'; Write-Host '================================' -ForegroundColor Cyan; Write-Host 'BROADCASTER MONITORING' -ForegroundColor Yellow; Write-Host 'Checking every 5 minutes' -ForegroundColor White; Write-Host '================================' -ForegroundColor Cyan; Set-Location 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' recommendations_broadcaster.py"

echo.
echo ============================================================
echo ✅ تم تشغيل جميع المكونات بنجاح!
echo ============================================================
echo.
echo المكونات النشطة:
echo   1. سيرفر الويب: http://localhost:5000
echo   2. بوت التليجرام: يعمل
echo   3. نظام البث: يراقب كل 5 دقائق
echo.
echo ============================================================
timeout /t 3 /nobreak > nul
start http://localhost:5000
pause

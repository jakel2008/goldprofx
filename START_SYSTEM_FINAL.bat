@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ============================================================
echo       تشغيل النظام المتكامل - GOLD PRO VIP System
echo ============================================================
echo.
echo سيتم تشغيل المكونات التالية:
echo   1. سيرفر الويب (Web Server)
echo   2. بوت التليجرام (Telegram Bot)
echo   3. نظام البث (Recommendations Broadcaster)
echo.
echo ============================================================
pause

REM Start Web Server
start "🌐 Web Server" /MIN powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='🌐 WEB SERVER - Port 5000'; chcp 65001 > $null; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; Write-Host '🌐 WEB SERVER RUNNING' -ForegroundColor Green; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; Write-Host 'URL: http://localhost:5000' -ForegroundColor Yellow; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' web_app.py"

REM Wait before starting next component
timeout /t 3 /nobreak > nul

REM Start Telegram Bot
start "🤖 Telegram Bot" /MIN powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='🤖 TELEGRAM BOT'; chcp 65001 > $null; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; Write-Host '🤖 TELEGRAM BOT ACTIVE' -ForegroundColor Green; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' vip_bot_simple.py"

REM Wait before starting next component
timeout /t 3 /nobreak > nul

REM Start Broadcaster
start "📤 Broadcaster" /MIN powershell -NoExit -Command "$host.UI.RawUI.WindowTitle='📤 RECOMMENDATIONS BROADCASTER'; chcp 65001 > $null; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; Write-Host '📤 BROADCASTER MONITORING' -ForegroundColor Yellow; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; Write-Host 'Checking every 5 minutes...' -ForegroundColor White; Write-Host '=' -NoNewline -ForegroundColor Cyan; Write-Host '='*60 -ForegroundColor Cyan; cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' recommendations_broadcaster.py"

echo.
echo ============================================================
echo ✅ تم تشغيل جميع المكونات بنجاح!
echo ============================================================
echo.
echo 🌐 سيرفر الويب: http://localhost:5000
echo 🤖 بوت التليجرام: يعمل في الخلفية
echo 📤 نظام البث: يراقب كل 5 دقائق
echo.
echo ============================================================
pause

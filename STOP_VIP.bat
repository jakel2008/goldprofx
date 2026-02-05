@echo off
chcp 65001 >nul

echo ========================================
echo ⏹️ إيقاف نظام VIP
echo ========================================
echo.
echo ⚠️ سيتم إيقاف جميع عمليات Python...
echo.
pause

taskkill /F /IM python.exe /T
timeout /t 2 /nobreak >nul

echo.
echo ✅ تم إيقاف النظام بنجاح!
echo.
pause

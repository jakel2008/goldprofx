@echo off
chcp 65001 > nul
cls

echo.
echo ============================================================
echo.
echo     بوت VIP مع أوامر إدارية
echo     VIP Bot with Admin Commands
echo.
echo ============================================================
echo.
echo جاري تشغيل البوت...
echo.

python "%~dp0vip_bot_admin.py"

echo.
pause

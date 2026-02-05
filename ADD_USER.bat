@echo off
chcp 65001 > nul
cls

echo.
echo ============================================================
echo.
echo     اداة اضافة مستخدم سريعة
echo     Quick User Addition Tool
echo.
echo ============================================================
echo.

python "%~dp0ADD_USER_SIMPLE.py"

echo.
pause

@echo off
chcp 65001 > nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║       📊 لوحة التحكم التفاعلية للصفقات                  ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM تفعيل البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo ✅ تشغيل اللوحة التفاعلية...
echo.

python interactive_dashboard.py

pause

@echo off
chcp 65001 >nul
cls

echo.
echo ============================================================
echo     📡 نظام البث الموحد
echo        Unified Broadcasting System
echo ============================================================
echo.

cd /d "%~dp0"

REM تفعيل البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    echo 🔧 تفعيل البيئة الافتراضية...
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo 🔧 تفعيل البيئة الافتراضية...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo 🔧 تفعيل البيئة الافتراضية...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️ تحذير: لم يتم العثور على البيئة الافتراضية
    echo.
)

echo.
echo ▶️  تشغيل البث الموحد...
echo     (كل 60 ثانية)
echo.
python unified_broadcaster.py

pause

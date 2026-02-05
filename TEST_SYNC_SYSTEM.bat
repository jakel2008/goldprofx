@echo off
chcp 65001 >nul
cls

echo.
echo ============================================================
echo     🧪 اختبار نظام المزامنة الموحدة
echo        Unified Synchronization System Test
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
echo ▶️  تشغيل اختبار نظام المزامنة...
echo.
python test_sync_complete.py

echo.
echo ============================================================
echo.
pause

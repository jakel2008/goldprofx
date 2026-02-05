@echo off
chcp 65001 > nul
color 0A

echo.
echo ========================================
echo 📡 نظام بث الإشارات التلقائي
echo ========================================
echo.

REM تفعيل البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ البيئة الافتراضية غير موجودة
    pause
    exit /b 1
)

echo ▶️ بدء نظام البث...
echo.

python signal_broadcaster.py

if errorlevel 1 (
    echo.
    echo ❌ حدث خطأ في تشغيل نظام البث
    pause
)

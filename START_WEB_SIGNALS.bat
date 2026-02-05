@echo off
chcp 65001 > nul
title 🌐 تشغيل صفحة الويب للإشارات

echo ================================
echo 🌐 تشغيل صفحة الويب للإشارات
echo ================================
echo.

REM Activate virtual environment
if exist ".venv-1\Scripts\activate.bat" (
    echo 🔧 تفعيل البيئة الافتراضية...
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo 🔧 تفعيل البيئة الافتراضية...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo 🔧 تفعيل البيئة الافتراضية...
    call .venv\Scripts\activate.bat
)

echo.
echo 📊 عرض النتائج الحالية...
python test_web_signals.py

echo.
echo ================================
echo 🚀 بدء تشغيل الخادم...
echo ================================
echo.
echo 🌐 افتح المتصفح على:
echo    http://localhost:5000/signals
echo.
echo 💡 لإيقاف الخادم: اضغط Ctrl+C
echo ================================
echo.

python web_app.py

pause

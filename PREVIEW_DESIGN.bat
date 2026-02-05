@echo off
chcp 65001 > nul
title 🎨 معاينة التصميم الجديد

echo ════════════════════════════════════════════════
echo 🎨 معاينة التصميم المحسّن لصفحة الإشارات
echo ════════════════════════════════════════════════
echo.

REM Activate virtual environment
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo 📊 عرض ملخص التحسينات...
echo.
python preview_design.py

echo.
echo ════════════════════════════════════════════════
echo 💡 هل تريد تشغيل صفحة الويب الآن؟
echo ════════════════════════════════════════════════
echo.
echo [Y] نعم - تشغيل الويب الآن
echo [N] لا - الخروج
echo.

choice /C YN /N /M "اختيارك: "

if errorlevel 2 goto :end
if errorlevel 1 goto :startweb

:startweb
echo.
echo 🚀 بدء تشغيل صفحة الويب...
echo.
start cmd /k "title 🌐 خادم الويب && python web_app.py"
timeout /t 3 > nul
echo.
echo ════════════════════════════════════════════════
echo ✅ تم تشغيل الخادم!
echo ════════════════════════════════════════════════
echo.
echo 🌐 افتح المتصفح على:
echo    http://localhost:5000/signals
echo.
echo 💡 النصائح:
echo    • راقب العداد التنازلي في الزاوية السفلية
echo    • مرر بالفأرة على البطاقات لرؤية التأثيرات
echo    • انتظر التحديث التلقائي كل 30 ثانية
echo    • راقب ظهور البطاقات التدريجي
echo.
echo ════════════════════════════════════════════════

:end
pause

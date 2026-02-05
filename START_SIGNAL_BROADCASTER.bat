@echo off
chcp 65001 >nul
title نظام بث الإشارات التلقائي

echo.
echo ========================================
echo 📢 نظام بث الإشارات التلقائي
echo ========================================
echo.
echo يقوم هذا البرنامج بـ:
echo   ✅ قراءة الإشارات من مجلد signals
echo   ✅ حساب جودة كل إشارة
echo   ✅ إرسالها للمشتركين حسب خططهم
echo   ✅ تجنب إعادة إرسال نفس الإشارة
echo.
echo ========================================
echo.

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️ لم يتم العثور على بيئة افتراضية
)

python signal_broadcaster.py

if errorlevel 1 (
    echo.
    echo ❌ خطأ في تشغيل نظام البث
    pause
) else (
    echo.
    echo ✅ تم الإيقاف
)

pause

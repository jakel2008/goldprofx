@echo off
chcp 65001 > nul
title النظام الموحد للتداول والتقارير

echo.
echo ═══════════════════════════════════════════════════════════════
echo         🚀 النظام الموحد للتداول والتقارير
echo         Unified Trading ^& Reporting System
echo ═══════════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

echo 🔍 جاري التحقق من البيئة الافتراضية...
if exist .venv\Scripts\activate.bat (
    echo ✅ تم العثور على البيئة الافتراضية
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    echo ✅ تم العثور على البيئة الافتراضية
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ لم يتم العثور على البيئة الافتراضية
    echo 📦 جاري تثبيت المكتبات المطلوبة...
    pip install schedule
)

echo.
echo 🚀 جاري تشغيل النظام...
echo.

python unified_trading_system.py

if errorlevel 1 (
    echo.
    echo ❌ حدث خطأ أثناء التشغيل
    pause
) else (
    echo.
    echo ✅ تم إيقاف النظام بنجاح
)

pause

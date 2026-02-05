@echo off
chcp 65001 > nul
title 🔬 المحلل العميق - 5 دقائق

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║        🔬 نظام التحليل العميق المستمر - 5 دقائق          ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 🔄 تفعيل البيئة الافتراضية...
if exist .venv-1\Scripts\activate.bat (
    call .venv-1\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  تحذير: لم يتم العثور على البيئة الافتراضية
)

echo.
echo ⚡ بدء المحلل العميق...
echo.

python deep_analyzer_5min.py

pause

@echo off
chcp 65001 >nul
title إدارة صلاحيات المشرفين - Admin Management

echo.
echo ════════════════════════════════════════════════════════════
echo    🛡️  إدارة صلاحيات المشرفين - Admin Management Tool
echo ════════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

REM تفعيل البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  تحذير: لم يتم العثور على البيئة الافتراضية
    echo.
)

REM تشغيل أداة إدارة الأدمن
python grant_admin.py

echo.
pause

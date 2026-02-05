@echo off
chcp 65001 >nul
title اختبار النظام الكامل

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python test_system.py

pause

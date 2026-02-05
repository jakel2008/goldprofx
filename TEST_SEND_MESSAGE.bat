@echo off
chcp 65001 >nul
title اختبار إرسال رسالة

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python test_send_message.py

pause

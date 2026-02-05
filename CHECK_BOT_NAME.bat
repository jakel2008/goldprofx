@echo off
chcp 65001 >nul
title معلومات البوت

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python check_bot_name.py

pause

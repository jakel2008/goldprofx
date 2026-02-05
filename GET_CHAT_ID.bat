@echo off
chcp 65001 >nul
title الحصول على Chat ID

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python get_chat_id.py

pause

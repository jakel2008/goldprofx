@echo off
REM Auto-start continuous_auto_trader.py at Windows startup
REM This script ensures the auto trader runs 24/7

cd /d "D:\GOLD PRO"

REM Kill any existing instances to prevent duplicates
taskkill /IM python.exe /FI "WINDOWTITLE eq continuous_auto_trader.py" /F 2>nul

REM Wait a second
timeout /t 1 /nobreak

REM Start the auto trader
"D:\GOLD PRO\venv\Scripts\python.exe" continuous_auto_trader.py

REM If it exits, restart it
goto restart

:restart
timeout /t 5 /nobreak
goto start_trader

:start_trader
"D:\GOLD PRO\venv\Scripts\python.exe" continuous_auto_trader.py
goto restart

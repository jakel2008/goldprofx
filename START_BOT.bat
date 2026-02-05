@echo off
chcp 65001 > nul
color 0A
title VIP Bot System

echo.
echo ╔════════════════════════════════╗
echo ║   VIP Bot System - Quick Start ║
echo ╚════════════════════════════════╝
echo.

REM تفعيل البيئة
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo.
echo Select an option:
echo.
echo [1] Run VIP Bot (Receive user commands)
echo [2] Run Analyzer (Send signals)
echo [3] Run Both
echo [4] Stop All
echo [0] Exit
echo.

set /p choice="Choose [0-4]: "

if "%choice%"=="1" goto BOT
if "%choice%"=="2" goto ANALYZER
if "%choice%"=="3" goto BOTH
if "%choice%"=="4" goto STOP
if "%choice%"=="0" goto END

:BOT
echo.
echo Starting VIP Bot...
start "VIP Bot" cmd /k "cd /d "%~dp0" && python vip_bot_simple.py"
echo Bot started in new window
pause
goto END

:ANALYZER
echo.
echo Starting Analyzer...
start "VIP Analyzer" cmd /k "cd /d "%~dp0" && python analyzer_vip_integrated.py"
echo Analyzer started in new window
pause
goto END

:BOTH
echo.
echo Starting both services...
start "VIP Bot" cmd /k "cd /d "%~dp0" && python vip_bot_simple.py"
timeout /t 2 /nobreak > nul
start "VIP Analyzer" cmd /k "cd /d "%~dp0" && python analyzer_vip_integrated.py"
echo Both services started
pause
goto END

:STOP
echo.
echo Stopping all Python processes...
taskkill /F /IM python.exe /T 2> nul
echo Stopped
pause
goto END

:END
echo Goodbye!
timeout /t 1 /nobreak > nul
exit

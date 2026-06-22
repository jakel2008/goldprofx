@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

set "PY=d:\GOLD PRO\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=d:\GOLD PRO\.venv-3\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Python interpreter not found.
  pause
  exit /b 1
)

echo Starting auto trader health check loop (every 5 minutes)...
start "Auto Trader Healthcheck" cmd /k ""%PY%" -u auto_trader_healthcheck.py --interval-sec 300 --window-min 10"

echo Healthcheck started.
endlocal

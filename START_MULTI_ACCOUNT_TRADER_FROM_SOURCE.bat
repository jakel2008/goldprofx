@echo off
chcp 65001 >nul
cd /d %~dp0
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" run_multi_account_traders.py --registry multi_account_config.json
pause

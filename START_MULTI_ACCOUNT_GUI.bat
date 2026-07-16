@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=.venv-3\Scripts\python.exe"
if not exist "%PY%" set "PY=.venv-5\Scripts\python.exe"
if not exist "%PY%" set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" multi_account_trader_gui.py

endlocal
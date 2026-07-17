@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=.venv-3\Scripts\python.exe"
if not exist "%PY%" set "PY=.venv-5\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
set "MT5_WALLET_CONFIG=%~dp0accounts\account3\wallet.json"
set "AUTO_TRADER_ACCOUNT_ID=account3"
set "AUTO_TRADER_USE_MT5_MARKET_DATA=1"
set "AUTO_TRADER_REQUIRE_MT5_MARKET_DATA=1"
set "ENABLE_MT5_MARKET_DATA=1"
set "MT5_MARKET_DATA_MODE=mt5_only"
"%PY%" btc_fibonacci_grid_trader.py --config accounts\account3\strategy_btc_fibonacci_grid_v1.json --once
pause

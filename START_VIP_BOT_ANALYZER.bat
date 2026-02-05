@echo off
chcp 65001 > nul
cd /d "D:\GOLD PRO"

echo ╔════════════════════════════════════════════╗
echo ║   VIP Signal Bot with Forex Analyzer      ║
echo ║   بوت الإشارات VIP مع محلل الفوركس       ║
echo ╚════════════════════════════════════════════╝
echo.

:: Activate virtual environment
call ".venv-1\Scripts\Activate.ps1" 2>nul || call ".venv\Scripts\Activate.ps1"

echo [✓] Environment activated
echo [✓] Starting VIP Bot with Analyzer...
echo.
echo Commands available in bot:
echo   /analyze        - Show analysis menu
echo   /analyze_eurusd - Analyze EUR/USD
echo   /analyze_gbpusd - Analyze GBP/USD
echo   /analyze_xauusd - Analyze Gold
echo   /analyze_btcusd - Analyze Bitcoin
echo.
echo Press Ctrl+C to stop
echo ════════════════════════════════════════════
echo.

python vip_bot_simple.py

pause

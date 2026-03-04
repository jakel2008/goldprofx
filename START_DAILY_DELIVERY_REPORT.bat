@echo off
chcp 65001 > nul
title GOLD PRO - Daily Delivery CSV Scheduler

echo ================================================================
echo   GOLD PRO - Daily Delivery CSV Scheduler
echo ================================================================
echo.
echo This will start the periodic reports scheduler:
echo - Hourly summary
echo - Daily report
echo - Daily delivery CSV export
echo.
echo Press Ctrl+C to stop.
echo.

cd /d "%~dp0"
"C:\Users\Discovery PC\AppData\Local\Programs\Python\Python313\python3.13t.exe" auto_reports_scheduler.py

echo.
echo Scheduler stopped.
pause

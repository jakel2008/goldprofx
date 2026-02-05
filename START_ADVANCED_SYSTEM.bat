@echo off
chcp 65001 > nul
title 🧠 النظام المتقدم مع AI

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║      🧠 تشغيل النظام المتقدم مع الذكاء الاصطناعي      ║
echo ╚════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

call .venv-1\Scripts\activate.bat

echo [%TIME%] 🚀 بدء التحليل المتقدم...
echo.

python integrated_analyzer.py --continuous

pause

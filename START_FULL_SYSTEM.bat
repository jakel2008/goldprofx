@echo off
chcp 65001 > nul
color 0A
title تشغيل النظام الكامل - GOLD PRO
cls

echo ╔════════════════════════════════════════════════════╗
echo ║         نظام GOLD PRO الكامل                    ║
echo ║      تشغيل: سيرفر + محلل + بث                   ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM تفعيل البيئة الافتراضية
echo [1] تفعيل البيئة الافتراضية...
call .venv-3\Scripts\activate.bat
echo.

REM قتل أي عمليات python قديمة
echo [2] إيقاف العمليات القديمة...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak

REM فتح نافذة 1: السيرفر
echo [3] فتح نافذة 1: السيرفر...
start "GOLD PRO - Web Server" cmd /k "python -u web_app.py"
timeout /t 3 /nobreak

REM فتح نافذة 2: محلل الإشارات
echo [4] فتح نافذة 2: محلل الإشارات...
start "GOLD PRO - Signal Analyzer" cmd /k "python -u auto_pairs_analyzer.py"
timeout /t 2 /nobreak

REM فتح نافذة 3: بث الإشارات
echo [5] فتح نافذة 3: بث الإشارات...
start "GOLD PRO - Signal Broadcaster" cmd /k "python -u signal_broadcaster.py"
timeout /t 2 /nobreak

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║              النظام قيد التشغيل ✓                ║
echo ║                                                    ║
echo ║  السيرفر:   http://localhost:5000               ║
echo ║  المحلل:   يعمل في الخلفية                       ║
echo ║  البث:     يراقب الإشارات الجديدة                  ║
echo ║                                                    ║
echo ║  بيانات اختبار:                                   ║
echo ║  البريد: test@goldpro.com                        ║
echo ║  الكلمة: Test123                                 ║
echo ║                                                   ║
echo ╚════════════════════════════════════════════════════╝
echo.
echo اضغط Ctrl+C في أي نافذة لإيقاف العملية
pause

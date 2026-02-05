@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 🚀 تشغيل سريع - نظام VIP
echo ========================================
echo.
echo ▶️ تشغيل النظام الكامل...
echo.

REM إيقاف أي عمليات python قديمة
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

REM تشغيل البوت
start "🤖 VIP Bot" cmd /k "title VIP Telegram Bot && python vip_telegram_bot.py"
timeout /t 3 /nobreak >nul

REM تشغيل المحلل
start "📊 Analyzer" cmd /k "title Auto Analyzer && python daily_scheduler.py"

echo.
echo ✅ تم تشغيل النظام!
echo.
echo النوافذ المفتوحة:
echo   • 🤖 VIP Telegram Bot
echo   • 📊 Auto Analyzer
echo.
echo 💡 نصائح:
echo   • لا تغلق النوافذ المفتوحة
echo   • ستبدأ التوصيات خلال الساعة الأولى
echo   • استخدم /start في بوت التليجرام للتسجيل
echo.
pause

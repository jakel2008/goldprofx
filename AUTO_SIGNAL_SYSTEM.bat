@echo off
chcp 65001 > nul
color 0B

echo.
echo ========================================
echo 🚀 نظام الإشارات الكامل - تحليل عميق
echo ========================================
echo.
echo سيتم تشغيل:
echo   1. 🔬 المحلل العميق (كل 5 دقائق)
echo   2. 📡 نظام بث الإشارات
echo   3. 🤖 بوت التليجرام VIP
echo   4. ⏰ جدولة الصيانة الذكية
echo.
echo ========================================
echo.

REM تفعيل البيئة الافتراضية
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ البيئة الافتراضية غير موجودة
    pause
    exit /b 1
)

echo ▶️ تشغيل المحلل العميق (5 دقائق)...
start "🔬 Deep Analyzer 5min" cmd /k "python deep_analyzer_5min.py"
timeout /t 2 /nobreak > nul

echo ▶️ تشغيل نظام البث الموحد (ويب + بوت)...
start "📡 Unified Broadcaster" cmd /k "python unified_broadcaster.py"
timeout /t 2 /nobreak > nul

echo ▶️ تشغيل بوت VIP...
start "🤖 VIP Bot" cmd /k "python vip_bot_simple.py"
timeout /t 2 /nobreak > nul

echo ▶️ تشغيل جدولة الصيانة الذكية...
start "⏰ Trade Scheduler" cmd /k "python trade_scheduler.py"
timeout /t 2 /nobreak > nul

echo.
echo ✅ تم تشغيل جميع الأنظمة!
echo.
echo 💡 نصائح:
echo   • لا تغلق النوافذ المفتوحة
echo   • التحليل العميق كل 5 دقائق
echo   • الإشارات تُرسل تلقائياً للمشتركين
echo   • الصيانة التلقائية تعمل 24/7
echo   • استخدم /start في البوت للتسجيل
echo.
echo اضغط أي مفتاح للخروج...
pause > nul

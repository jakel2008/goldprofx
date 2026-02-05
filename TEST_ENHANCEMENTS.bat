@echo off
chcp 65001 > nul
title 🎨 اختبار التحسينات الجديدة

echo ════════════════════════════════════════════════════════
echo 🎨 اختبار التحسينات المتقدمة لعرض الأسعار
echo ════════════════════════════════════════════════════════
echo.

REM Activate virtual environment
if exist ".venv-1\Scripts\activate.bat" (
    call .venv-1\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo 🔍 المرحلة 1: اختبار جلب الأسعار من Yahoo Finance
echo ────────────────────────────────────────────────────────
python test_price_fetch.py
echo.
pause

cls
echo ════════════════════════════════════════════════════════
echo 📊 المرحلة 2: اختبار العرض المحسّن
echo ════════════════════════════════════════════════════════
echo.
python test_enhanced_display.py
echo.
pause

cls
echo ════════════════════════════════════════════════════════
echo ✨ التحسينات الجديدة المطبقة:
echo ════════════════════════════════════════════════════════
echo.
echo  1. 🎨 قسم مقارنة الأسعار (الدخول ↔️ الحالي)
echo     • سعر الدخول بخلفية رمادية
echo     • سعر الحالي بخلفية خضراء/حمراء
echo     • سهم متحرك بينهما
echo.
echo  2. 💰 عرض النقاط بحجم كبير (36px)
echo     • نبض وتوهج للأرباح
echo     • اهتزاز وتنبيه للخسائر
echo     • ظلال عميقة وحدود بيضاء
echo.
echo  3. 📊 شريط تقدم متطور (40px)
echo     • تدرج ثلاثي الألوان متحرك
echo     • انتقال سلس (0.8s)
echo     • ظلال وحدود محسّنة
echo.
echo  4. ⚡ خلفية تفاعلية
echo     • تدرج برتقالي دافئ
echo     • أيقونة متحركة نابضة
echo     • ظلال عميقة (8px-30px)
echo.
echo  5. ✨ 6 رسوم متحركة جديدة
echo     • pulse-icon: نبض الأيقونة
echo     • blink-price: وميض السعر
echo     • bounce-arrow: ارتداد السهم
echo     • pulse-profit: نبض الأرباح
echo     • shake-loss: اهتزاز الخسائر
echo     • gradient-shift: تحرك التدرج
echo.
echo ════════════════════════════════════════════════════════
echo 🚀 هل تريد تشغيل صفحة الويب الآن؟
echo ════════════════════════════════════════════════════════
echo.
echo [Y] نعم - شاهد التحسينات مباشرة
echo [N] لا - الخروج
echo.

choice /C YN /N /M "اختيارك: "

if errorlevel 2 goto :end
if errorlevel 1 goto :startweb

:startweb
cls
echo.
echo ════════════════════════════════════════════════════════
echo 🌐 تشغيل خادم الويب...
echo ════════════════════════════════════════════════════════
echo.
start cmd /k "title 🌐 GOLD PRO Web Server && python web_app.py"
timeout /t 3 > nul
echo.
echo ✅ تم تشغيل الخادم!
echo.
echo 🌐 افتح المتصفح على:
echo    ┌─────────────────────────────────────┐
echo    │  http://localhost:5000/signals      │
echo    └─────────────────────────────────────┘
echo.
echo 💡 لاحظ التحسينات:
echo    ✓ مقارنة الأسعار (دخول ↔️ حالي)
echo    ✓ النقاط بحجم كبير ونابضة
echo    ✓ شريط تقدم متحرك بـ3 ألوان
echo    ✓ أيقونة ⚡ نابضة في الخلفية
echo    ✓ سهم متحرك بين الأسعار
echo.
echo 📖 للمزيد من التفاصيل:
echo    • PRICE_DISPLAY_GUIDE.md
echo    • DESIGN_IMPROVEMENTS.md
echo.
echo ════════════════════════════════════════════════════════

:end
pause

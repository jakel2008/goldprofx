@echo off
REM تشغيل سريع للتحليل الآن
REM ========================

echo.
echo 🚀 تشغيل التحليل الشامل...
echo.

cd /d "d:\GOLD PRO"

echo ⏳ جاري التحليل (قد يستغرق 30-60 ثانية)...
echo.

"d:\GOLD PRO\venv\Scripts\python.exe" auto_pairs_analyzer.py

echo.
echo.
echo ✅ انتهى التحليل!
echo.
echo 📱 تحقق من Telegram للرسائل
echo.
pause

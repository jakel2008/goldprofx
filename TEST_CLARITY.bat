@echo off
chcp 65001 > nul
color 0A
cls

echo ╔════════════════════════════════════════════════════════════╗
echo ║        🎯 اختبار وضوح الأرقام على صفحة الإشارات         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📌 التحسينات المطبقة:
echo    ✓ حجم الخط للأسعار: 42px (كبير جداً)
echo    ✓ حجم خط النقاط: 48px (أكبر)
echo    ✓ الأرقام بخط سميك 900 (الأسمك)
echo    ✓ حدود بيضاء سميكة 4px
echo    ✓ ظلال قوية للأسعار
echo    ✓ تأثير وميض للسعر الحالي
echo    ✓ أسهم كبيرة 60px
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

REM تفعيل البيئة الافتراضية
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo 🔍 اختبار في Terminal...
echo.
python TEST_CLARITY_FIX.py

echo.
echo ═══════════════════════════════════════════════════════════════
echo.
echo 🌐 لمشاهدة الصفحة في المتصفح:
echo    1. شغّل: START_WEB_SIGNALS.bat
echo    2. افتح: http://localhost:5000/signals
echo.
echo 📚 للمزيد من المعلومات:
echo    اقرأ ملف: CLARITY_FIX_GUIDE.md
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

pause

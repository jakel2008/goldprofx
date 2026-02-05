@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM تفعيل البيئة الافتراضية
if exist .venv-1\Scripts\activate.bat (
    call .venv-1\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    set PYTHON_EXE="D:\GOLD PRO\.venv-1\Scripts\python.exe"
    goto skip_venv
)

:skip_venv
set PYTHON_EXE=python

:menu
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          نظام التحليل والتوصيات المتقدم                     ║
echo ║       Advanced Analysis & Recommendations System             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo  📊 التحليل الشامل:
echo    1. تحليل زوج محدد (جميع الاستراتيجيات)
echo    2. تحليل جميع الأزواج المختارة
echo.
echo  🎯 التوصيات:
echo    3. توليد توصيات (أفضل نقاط الدخول)
echo    4. إعداد تفضيلات التوصيات
echo.
echo  ⚙️  الإعدادات:
echo    5. عرض الأزواج المتاحة
echo    6. اختيار الأزواج المفضلة
echo.
echo  🚀 التشغيل التلقائي:
echo    7. تشغيل التحليل + التوصيات معاً
echo    8. تشغيل نظام المراقبة المستمر
echo.
echo  0. خروج
echo.
echo ══════════════════════════════════════════════════════════════
echo.

set /p choice="اختر رقم الخيار: "

if "%choice%"=="1" goto analysis_single
if "%choice%"=="2" goto analysis_all
if "%choice%"=="3" goto recommendations
if "%choice%"=="4" goto setup_rec
if "%choice%"=="5" goto show_pairs
if "%choice%"=="6" goto select_pairs
if "%choice%"=="7" goto run_both
if "%choice%"=="8" goto monitor
if "%choice%"=="0" goto end

echo.
echo ❌ خيار غير صحيح!
timeout /t 2 >nul
goto menu

:analysis_single
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  تحليل زوج محدد                             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
%PYTHON_EXE% analysis_engine.py
echo.
pause
goto menu

:analysis_all
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              تحليل جميع الأزواج المختارة                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo جاري تحليل الأزواج...
echo.
%PYTHON_EXE% -c "from analysis_engine import AnalysisEngine; from recommendations_engine import ALL_AVAILABLE_PAIRS; engine = AnalysisEngine(); [engine.analyze_symbol(s, t, '1h') for cat in ['forex_major', 'metals', 'crypto'] for s, t in ALL_AVAILABLE_PAIRS.get(cat, {}).items()]"
echo.
echo ✅ تم التحليل!
pause
goto menu

:recommendations
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  توليد التوصيات                             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
%PYTHON_EXE% recommendations_engine.py
echo.
pause
goto menu

:setup_rec
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              إعداد تفضيلات التوصيات                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
%PYTHON_EXE% recommendations_engine.py setup
echo.
pause
goto menu

:show_pairs
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  الأزواج المتاحة                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
%PYTHON_EXE% -c "from recommendations_engine import ALL_AVAILABLE_PAIRS; [print(f'\n{cat.upper()}:\n  ' + '\n  '.join(f'{i}. {s}' for i, s in enumerate(pairs.keys(), 1))) for cat, pairs in ALL_AVAILABLE_PAIRS.items()]"
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo المجموع الكلي للأزواج المتاحة:
%PYTHON_EXE% -c "from recommendations_engine import ALL_AVAILABLE_PAIRS; print(f'  🎯 {sum(len(p) for p in ALL_AVAILABLE_PAIRS.values())} زوج')"
echo.
pause
goto menu

:select_pairs
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              اختيار الأزواج المفضلة                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo هذا الخيار سيفتح ملف التفضيلات للتعديل اليدوي
echo.
echo الملف: user_preferences.json
echo.
pause
notepad user_preferences.json
goto menu

:run_both
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           تشغيل التحليل والتوصيات معاً                      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 جاري التشغيل...
echo.

start "📊 محرك التحليل" cmd /k "%PYTHON_EXE% -u analysis_engine.py"
timeout /t 2 >nul
start "🎯 محرك التوصيات" cmd /k "%PYTHON_EXE% -u recommendations_engine.py"

echo.
echo ✅ تم تشغيل النظامين في نوافذ منفصلة!
echo.
pause
goto menu

:monitor
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              نظام المراقبة المستمر                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🔄 سيتم تحليل الأزواج كل ساعة وتوليد التوصيات
echo.
echo جاري التشغيل...
echo.

start "🔄 المراقبة المستمرة" cmd /k "%PYTHON_EXE% -c \"import time; from datetime import datetime; from recommendations_engine import RecommendationsEngine; from analysis_engine import AnalysisEngine; rec_engine = RecommendationsEngine(); ana_engine = AnalysisEngine(); print('🚀 نظام المراقبة المستمر'); print('='*60); [exec('print(f\\\"\\n⏰ [{datetime.now()}] جاري الفحص...\\\"); rec_engine.scan_all_pairs(); print(\\\"✅ تم الفحص\\\"); time.sleep(3600)') for _ in iter(int, 1)]\""

echo.
echo ✅ تم تشغيل نظام المراقبة!
echo.
pause
goto menu

:end
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo            شكراً لاستخدام النظام
echo            Thank you for using the system
echo.
echo ══════════════════════════════════════════════════════════════
echo.
timeout /t 2 >nul
exit

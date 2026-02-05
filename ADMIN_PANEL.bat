@echo off
chcp 65001 > nul
cls

echo.
echo ============================================================
echo.
echo  لوحة التحكم الإدارية - VIP Bot Admin Panel
echo.
echo ============================================================
echo.
echo اختر ما تريد:
echo.
echo [1] فتح لوحة التحكم الكاملة (Full Admin Panel)
echo [2] دليل سريع للإضافة وتفعيل الأدمن (Quick Guide)
echo [3] عرض قائمة الأدمن (List Admins)
echo [4] اختبار النظام (Test System)
echo [0] خروج (Exit)
echo.
echo ============================================================
echo.

set /p choice="اختر خيار (0-4): "

if "%choice%"=="1" (
    echo.
    echo جاري فتح لوحة التحكم...
    python "%~dp0admin_panel.py"
    pause
) else if "%choice%"=="2" (
    echo.
    echo جاري فتح الدليل السريع...
    python "%~dp0quick_start_admin.py"
    pause
) else if "%choice%"=="3" (
    echo.
    echo جاري عرض قائمة الأدمن...
    python -c "from admin_panel import AdminPanel; admin = AdminPanel(); admin.list_admins()"
    pause
) else if "%choice%"=="4" (
    echo.
    echo جاري اختبار النظام...
    python "%~dp0test_admin_system.py"
    pause
) else if "%choice%"=="0" (
    echo وداعا!
    exit /b 0
) else (
    echo.
    echo اختيار غير صحيح!
    pause
    goto start
)

goto end

:end
echo.
echo انتهى!
echo.
pause

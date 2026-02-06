# ═══════════════════════════════════════════════════════════════════════
#          طريقة بسيطة للتشغيل التلقائي (بدون صلاحيات المسؤول)
# ═══════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "🚀 إعداد التشغيل التلقائي للنظام" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$VBSPath = "d:\GOLD PRO\start_auto_scheduler_silent.vbs"
$StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath = "$StartupFolder\GoldAnalyzer.lnk"

Write-Host "📋 الخطوات:" -ForegroundColor Yellow
Write-Host ""

# الخطوة 1: التحقق من الملفات
Write-Host "✓ التحقق من الملفات المطلوبة..." -ForegroundColor Cyan
if (!(Test-Path $VBSPath)) {
    Write-Host "❌ خطأ: ملف VBS غير موجود" -ForegroundColor Red
    Write-Host "   المسار: $VBSPath" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ الملفات موجودة" -ForegroundColor Green
Write-Host ""

# الخطوة 2: إنشاء اختصار في Startup
Write-Host "✓ إنشاء اختصار في مجلد Startup..." -ForegroundColor Cyan

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$VBSPath`""
$Shortcut.WorkingDirectory = "d:\GOLD PRO"
$Shortcut.Description = "Gold Analyzer - نظام التحليل التلقائي"
$Shortcut.Save()

Write-Host "  ✅ تم إنشاء الاختصار" -ForegroundColor Green
Write-Host "  📁 المسار: $ShortcutPath" -ForegroundColor Gray
Write-Host ""

# الخطوة 3: التأكيد
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ تم الإعداد بنجاح!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 ماذا بعد؟" -ForegroundColor Yellow
Write-Host "   • عند إعادة تشغيل الكمبيوتر، سيبدأ النظام تلقائياً"
Write-Host "   • سيرسل تحليل 5 دقائق لجميع الأزواج كل ساعة"
Write-Host "   • سيرسل تحليل شامل يومياً الساعة 22:00 UTC"
Write-Host ""
Write-Host "🔧 لإزالة التشغيل التلقائي:" -ForegroundColor Yellow
Write-Host "   احذف الملف: $ShortcutPath"
Write-Host ""

$response = Read-Host "هل تريد تشغيل النظام الآن (بدون انتظار إعادة التشغيل)؟ (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "🚀 جاري تشغيل النظام..." -ForegroundColor Green
    Write-Host ""
    
    Start-Process -FilePath "wscript.exe" -ArgumentList "`"$VBSPath`"" -WindowStyle Hidden
    
    Start-Sleep -Seconds 2
    Write-Host "✅ تم بدء التشغيل في الخلفية" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 تحقق من Telegram خلال دقيقتين لاستلام أول تحليل" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "ℹ️  ملاحظة: النظام يعمل الآن ويرسل كل ساعة تلقائياً" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✨ شكراً لاستخدام Gold Analyzer!" -ForegroundColor Green
Write-Host ""

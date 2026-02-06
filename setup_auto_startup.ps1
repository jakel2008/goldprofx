# سكريبت PowerShell لإنشاء مهمة تلقائية في Windows Task Scheduler
# يجعل النظام يبدأ تلقائياً عند تشغيل Windows

$TaskName = "GoldAnalyzerAutoScheduler"
$TaskDescription = "تشغيل نظام التحليل التلقائي لجميع الأزواج كل ساعة"
$ScriptPath = "d:\GOLD PRO\start_auto_scheduler_silent.vbs"

# التحقق من وجود المهمة وحذفها إن وجدت
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "⚠️  المهمة موجودة مسبقاً - سيتم استبدالها" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# إنشاء Action (تشغيل VBS)
$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$ScriptPath`""

# إنشاء Trigger (عند تسجيل الدخول)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# إنشاء Settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# تسجيل المهمة
Register-ScheduledTask -TaskName $TaskName `
    -Description $TaskDescription `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -User $env:USERNAME `
    -RunLevel Highest

Write-Host ""
Write-Host "✅ تم إنشاء المهمة التلقائية بنجاح!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 التفاصيل:" -ForegroundColor Cyan
Write-Host "   اسم المهمة: $TaskName"
Write-Host "   التشغيل: عند تسجيل الدخول لـ Windows"
Write-Host "   الوظيفة: إرسال تحليل 5 دقائق كل ساعة + تحليل يومي 22:00 UTC"
Write-Host ""
Write-Host "🔧 الأوامر المفيدة:" -ForegroundColor Yellow
Write-Host "   • لإيقاف المهمة: Disable-ScheduledTask -TaskName '$TaskName'"
Write-Host "   • لتفعيلها مرة أخرى: Enable-ScheduledTask -TaskName '$TaskName'"
Write-Host "   • لحذفها: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
Write-Host "   • لتشغيلها الآن: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "ℹ️  سيبدأ النظام تلقائياً عند إعادة تشغيل الكمبيوتر" -ForegroundColor Cyan
Write-Host ""

# سؤال المستخدم إذا كان يريد تشغيل المهمة الآن
$response = Read-Host "هل تريد تشغيل النظام الآن؟ (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "🚀 جاري تشغيل النظام..." -ForegroundColor Green
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
    Write-Host "✅ تم بدء التشغيل" -ForegroundColor Green
    Write-Host ""
    Write-Host "📱 تحقق من Telegram لاستلام التحليلات" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "✨ تم الإعداد بنجاح!" -ForegroundColor Green

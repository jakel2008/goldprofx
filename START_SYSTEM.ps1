# GOLD PRO - تشغيل النظام المتكامل
# Integrated System Launcher

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "      GOLD PRO - VIP Trading System" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "سيتم تشغيل المكونات التالية:`n" -ForegroundColor Yellow
Write-Host "  1. 🌐 سيرفر الويب (Web Server)" -ForegroundColor White
Write-Host "  2. 🤖 بوت التليجرام (Telegram Bot)" -ForegroundColor White
Write-Host "  3. 📤 نظام البث (Broadcaster)`n" -ForegroundColor White

$response = Read-Host "هل تريد المتابعة؟ (y/n)"

if ($response -ne 'y') {
    Write-Host "`n❌ تم الإلغاء" -ForegroundColor Red
    exit
}

# Set encoding
chcp 65001 > $null

# Change to project directory
cd "D:\GOLD PRO"

Write-Host "`n🚀 جاري التشغيل...`n" -ForegroundColor Cyan

# Start Web Server
Write-Host "[1/3] تشغيل سيرفر الويب..." -ForegroundColor Yellow
$webCmd = "chcp 65001 > `$null; Write-Host '='*70 -ForegroundColor Cyan; Write-Host '🌐 WEB SERVER - RUNNING' -ForegroundColor Green; Write-Host '='*70 -ForegroundColor Cyan; Write-Host 'URL: http://localhost:5000' -ForegroundColor Yellow; Write-Host '='*70 -ForegroundColor Cyan; cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' web_app.py"
Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoExit", "-Command", $webCmd
Start-Sleep -Seconds 2

# Start Telegram Bot
Write-Host "[2/3] تشغيل بوت التليجرام..." -ForegroundColor Yellow
$botCmd = "chcp 65001 > `$null; Write-Host '='*70 -ForegroundColor Cyan; Write-Host '🤖 TELEGRAM BOT - ACTIVE' -ForegroundColor Green; Write-Host '='*70 -ForegroundColor Cyan; cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' vip_bot_simple.py"
Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoExit", "-Command", $botCmd
Start-Sleep -Seconds 2

# Start Broadcaster
Write-Host "[3/3] تشغيل نظام البث..." -ForegroundColor Yellow
$broadcastCmd = "chcp 65001 > `$null; Write-Host '='*70 -ForegroundColor Cyan; Write-Host '📤 BROADCASTER - MONITORING' -ForegroundColor Yellow; Write-Host '='*70 -ForegroundColor Cyan; Write-Host 'Monitoring every 5 minutes...' -ForegroundColor White; Write-Host '='*70 -ForegroundColor Cyan; cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' recommendations_broadcaster.py"
Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoExit", "-Command", $broadcastCmd

Start-Sleep -Seconds 3

# Show status
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "✅ تم تشغيل النظام بنجاح!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "المكونات النشطة:" -ForegroundColor Yellow
Write-Host "  🌐 سيرفر الويب: http://localhost:5000" -ForegroundColor White
Write-Host "  🤖 بوت التليجرام: يعمل في الخلفية" -ForegroundColor White
Write-Host "  📤 نظام البث: يراقب التوصيات كل 5 دقائق`n" -ForegroundColor White

Write-Host "============================================================`n" -ForegroundColor Cyan

$processes = Get-Process python -ErrorAction SilentlyContinue
Write-Host "عدد العمليات النشطة: $($processes.Count)`n" -ForegroundColor Cyan

Write-Host "اضغط أي مفتاح للخروج..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

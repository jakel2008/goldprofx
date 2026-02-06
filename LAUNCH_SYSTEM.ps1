# GOLD PRO - System Launcher

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "      GOLD PRO - VIP Trading System" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

$response = Read-Host "Start all components? (y/n)"

if ($response -ne 'y') {
    Write-Host "`nCancelled" -ForegroundColor Red
    exit
}

cd "D:\GOLD PRO"

Write-Host "`nStarting system...`n" -ForegroundColor Cyan

# Web Server
Write-Host "[1/3] Starting Web Server..." -ForegroundColor Yellow
Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoExit", "-Command", "cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' web_app.py"
Start-Sleep -Seconds 2

# Telegram Bot
Write-Host "[2/3] Starting Telegram Bot..." -ForegroundColor Yellow
Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoExit", "-Command", "cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' vip_bot_simple.py"
Start-Sleep -Seconds 2

# Broadcaster
Write-Host "[3/3] Starting Broadcaster..." -ForegroundColor Yellow
Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoExit", "-Command", "cd 'D:\GOLD PRO'; & 'D:/GOLD PRO/.venv-1/Scripts/python.exe' recommendations_broadcaster.py"

Start-Sleep -Seconds 3

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "System started successfully!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Active components:" -ForegroundColor Yellow
Write-Host "  - Web Server: http://localhost:5000" -ForegroundColor White
Write-Host "  - Telegram Bot: Running" -ForegroundColor White
Write-Host "  - Broadcaster: Monitoring every 5 minutes`n" -ForegroundColor White

$processes = Get-Process python -ErrorAction SilentlyContinue
Write-Host "Active processes: $($processes.Count)`n" -ForegroundColor Cyan

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

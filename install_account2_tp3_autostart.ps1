$ErrorActionPreference = 'Stop'

$TaskName = 'GOLD_PRO_Account2_TP3_AutoTrader'
$Workspace = 'D:\GOLD PRO'
$StartupScript = Join-Path $Workspace 'start_account2_tp3_trader.ps1'

if (-not (Test-Path $StartupScript)) {
    throw "Startup script not found: $StartupScript"
}

$Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartupScript`"" -WorkingDirectory $Workspace
$LogonTrigger = New-ScheduledTaskTrigger -AtLogOn
$RepeatTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description 'Starts and watches GOLD PRO account2 TP3 auto trader after Windows login.' `
    -Action $Action `
    -Trigger @($LogonTrigger, $RepeatTrigger) `
    -Settings $Settings `
    -User $env:USERNAME `
    -RunLevel Highest | Out-Null

Write-Host "Created scheduled task: $TaskName" -ForegroundColor Green
Write-Host "Task starts account2 TP3 trader at logon and checks every 5 minutes." -ForegroundColor Cyan
Write-Host "Manual start command:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Disable command:" -ForegroundColor Yellow
Write-Host "  Disable-ScheduledTask -TaskName '$TaskName'"
Write-Host "Remove command:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"

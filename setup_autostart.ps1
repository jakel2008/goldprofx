# PowerShell script to set up automatic startup of auto_trader_startup.bat
# Run this with: powershell -NoProfile -ExecutionPolicy Bypass -File setup_autostart.ps1

$batchFile = "D:\GOLD PRO\auto_trader_startup.bat"
$startupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$shortcutPath = [System.IO.Path]::Combine($startupFolder, "GOLD_PRO_AutoTrader.lnk")

# Create shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $batchFile
$Shortcut.WorkingDirectory = "D:\GOLD PRO"
$Shortcut.WindowStyle = 7  # Hidden window
$Shortcut.Save()

Write-Host "✓ Auto-trader startup shortcut created at: $shortcutPath"
Write-Host "✓ Auto trader will now start automatically when Windows boots."
Write-Host ""
Write-Host "To verify it's working:"
Write-Host "1. Open Task Scheduler"
Write-Host "2. Look for GOLD_PRO_AutoTrader in Startup folder"
Write-Host ""
Write-Host "To manually trigger: Just run this batch file:"
Write-Host "  $batchFile"

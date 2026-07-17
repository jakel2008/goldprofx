# Auto Trader 24/7 Setup Guide

## Current Status
✓ Continuous auto trader is configured and tested
✓ Account connected: 262972266 (Exness-MT5Trial16)
✓ Live trade executed successfully (Deal #1334962123)
✓ AutoTrading enabled in MT5

## To Enable 24/7 Automatic Operation

### Option 1: Manual (Recommended for First Test)
Run this command in PowerShell:
```powershell
& "D:\GOLD PRO\venv\Scripts\python.exe" continuous_auto_trader.py
```
Keep the terminal open. The script will run indefinitely.

### Option 2: Automatic Startup (Windows Startup)
Run this PowerShell command as Administrator:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\GOLD PRO\setup_autostart.ps1"
```

This will:
- Create a startup shortcut in Windows Startup folder
- Auto-start the auto trader when you boot Windows
- Run hidden in background

### Option 3: Windows Task Scheduler (Manual)
1. Press `Win+R`, type `taskschd.msc`, press Enter
2. Click "Create Task" → Name it "GOLD PRO Auto Trader"
3. Trigger: "At startup"
4. Action: Run program
   - Program: `D:\GOLD PRO\venv\Scripts\python.exe`
   - Arguments: `continuous_auto_trader.py`
   - Start in: `D:\GOLD PRO`
5. Conditions: Check "Wake computer"
6. Save and enable

## Configuration Files

### mt5_wallet_config.json
- Login: 262972266
- Server: Exness-MT5Trial16
- Auto symbols: [US30, EURUSD, GBPUSD, XAUUSD, BTCUSD, USDJPY]
- AutoTrading: Enabled ✓

### auto_trading_user_config.json
- enabled: true
- dry_run: false (Live trading mode)
- scan_every_sec: 60
- max_open_positions: 3

## Monitoring

Check if auto trader is running:
```powershell
Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.CommandLine -match "continuous_auto_trader"}
```

View recent signals:
```powershell
Get-Content "D:\GOLD PRO\auto_trading_runtime_state.json" | ConvertFrom-Json | ForEach-Object {$_.last_trade_at | Format-Table}
```

## Important Notes

⚠️ Keep MT5 open with AutoTrading enabled
⚠️ Ensure network connection is stable
⚠️ Check account balance regularly
⚠️ Review open positions daily

## Test Results Summary

| Component | Status | Details |
|-----------|--------|---------|
| Render Web Server | ✓ | Working on Linux |
| Local MT5 Bridge | ✓ | Connected to account |
| Live Order Execution | ✓ | Deal #1334962123 (BUY XAUUSD 0.01) |
| Auto Trader Process | ✓ | Running PID 43800 |
| Account Balance | ✓ | 8336.6 USD available |

## Troubleshooting

If auto trader stops:
1. Check if MT5 crashed
2. Verify network connectivity
3. Check Windows Event Viewer for Python errors
4. Restart the batch file: `auto_trader_startup.bat`

If trades aren't executing:
1. Verify AutoTrading is ON in MT5 (green icon)
2. Check `auto_trading_user_config.json` settings
3. View error logs in terminal output

@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

set "PY=d:\GOLD PRO\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=d:\GOLD PRO\.venv-3\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] Python interpreter not found.
  pause
  exit /b 1
)

echo [1/3] Stopping existing auto trader processes...
powershell -NoProfile -Command "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*continuous_auto_trader.py*' }; foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }; Write-Host ('Stopped: ' + ($procs | Measure-Object | Select-Object -ExpandProperty Count))"

echo [2/3] Starting auto trader with persisted config/state...
powershell -NoProfile -Command "$py = '%PY%'; $args = '-u continuous_auto_trader.py --config auto_trading_user_config.json --state auto_trading_runtime_state.json'; Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory (Get-Location).Path -RedirectStandardOutput 'auto_trader_live.out.log' -RedirectStandardError 'auto_trader_live.err.log'; Start-Sleep -Seconds 2"

echo [3/3] Verifying running process...
powershell -NoProfile -Command "$rows = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*continuous_auto_trader.py*' } | Select-Object ProcessId,ParentProcessId,CreationDate; if ($rows) { $rows | Format-Table -AutoSize } else { Write-Host 'FAILED_TO_START'; exit 1 }"

echo Done.
endlocal

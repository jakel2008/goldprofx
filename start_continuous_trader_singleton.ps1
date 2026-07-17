$ErrorActionPreference = 'SilentlyContinue'

$workspace = 'D:\GOLD PRO'
$pythonPrimary = Join-Path $workspace '.venv-3\Scripts\python.exe'
$pythonFallback = Join-Path $workspace 'venv\Scripts\python.exe'
$traderScript = Join-Path $workspace 'continuous_auto_trader.py'
$logFile = Join-Path $workspace 'auto_trader_startup.log'
$stdoutLog = Join-Path $workspace 'auto_trader_stdout.log'
$stderrLog = Join-Path $workspace 'auto_trader_stderr.log'

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $logFile -Value "[$timestamp] $Message" -Encoding UTF8
}

function Run-Main {
    $pythonExe = $pythonPrimary
    if (-not (Test-Path $pythonExe)) {
        $pythonExe = $pythonFallback
    }

    if (-not (Test-Path $pythonExe)) {
        Write-Log 'Python executable was not found. Startup aborted.'
        return 1
    }

    if (-not (Test-Path $traderScript)) {
        Write-Log 'continuous_auto_trader.py was not found. Startup aborted.'
        return 1
    }

    $running = Get-CimInstance Win32_Process |
        Where-Object { $_.Name -match '^python(\.exe)?$' -and $_.CommandLine -match 'continuous_auto_trader\.py' } |
        Sort-Object CreationDate

    if ($running.Count -ge 1) {
        $pids = ($running | ForEach-Object { $_.ProcessId }) -join ','
        Write-Log "Trader already running. PIDs=$pids"
        return 0
    }

    Start-Process -FilePath $pythonExe -ArgumentList "`"$traderScript`"" -WorkingDirectory $workspace -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
    Start-Sleep -Seconds 2

    $verify = Get-CimInstance Win32_Process |
        Where-Object { $_.Name -match '^python(\.exe)?$' -and $_.CommandLine -match 'continuous_auto_trader\.py' }

    if ($verify.Count -ge 1) {
        $firstPid = ($verify | Sort-Object CreationDate | Select-Object -First 1 -ExpandProperty ProcessId)
        Write-Log "Trader started successfully PID=$firstPid"
        return 0
    }

    if (Test-Path $stderrLog) {
        $lastErr = (Get-Content $stderrLog -Tail 5) -join ' | '
        if (-not [string]::IsNullOrWhiteSpace($lastErr)) {
            Write-Log "Last stderr: $lastErr"
        }
    }

    Write-Log 'Trader failed to start.'
    return 1
}

$mutex = New-Object System.Threading.Mutex($false, 'Global\GOLDPRO_AutoTrader_SingletonStartup')
$gotLock = $mutex.WaitOne(0)

if (-not $gotLock) {
    Write-Log 'Startup script skipped because another startup instance is running.'
    exit 0
}

try {
    $code = Run-Main
}
finally {
    $mutex.ReleaseMutex() | Out-Null
    $mutex.Dispose()
}

exit $code

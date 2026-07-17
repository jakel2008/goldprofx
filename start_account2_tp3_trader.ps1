$ErrorActionPreference = 'SilentlyContinue'

$Workspace = 'D:\GOLD PRO'
$PythonCandidates = @(
    (Join-Path $Workspace '.venv-3\Scripts\python.exe'),
    (Join-Path $Workspace '.venv-5\Scripts\python.exe'),
    (Join-Path $Workspace 'venv\Scripts\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
    'python'
)
$TraderScript = Join-Path $Workspace 'continuous_auto_trader.py'
$ConfigPath = Join-Path $Workspace 'accounts\account2_bitcoin\config.json'
$WalletPath = Join-Path $Workspace 'accounts\account2_bitcoin\wallet.json'
$StatePath = Join-Path $Workspace 'accounts\account2_bitcoin\runtime_state.json'
$LogDir = Join-Path $Workspace 'accounts\account2_bitcoin'
$StartupLog = Join-Path $LogDir 'account2_tp3_autostart.log'
$StdoutLog = Join-Path $LogDir 'account2_tp3_trader.out.log'
$StderrLog = Join-Path $LogDir 'account2_tp3_trader.err.log'
$LockPath = Join-Path $Workspace 'continuous_auto_trader.account2_bitcoin.lock'

function Write-StartupLog {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $StartupLog -Value "[$timestamp] $Message" -Encoding UTF8
}

function Resolve-Python {
    foreach ($Candidate in $PythonCandidates) {
        if ($Candidate -eq 'python') {
            $cmd = Get-Command python -ErrorAction SilentlyContinue
            if ($cmd) { return $cmd.Source }
            continue
        }
        if (Test-Path $Candidate) { return $Candidate }
    }
    return ''
}

function Get-Account2TraderProcess {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match '^python(\.exe)?$' -and
            $_.CommandLine -match 'continuous_auto_trader\.py' -and
            $_.CommandLine -match 'account2_bitcoin'
        } |
        Sort-Object CreationDate
}

function Clear-StaleLockIfNeeded {
    if (-not (Test-Path $LockPath)) { return }
    $lockPidText = (Get-Content $LockPath -ErrorAction SilentlyContinue | Select-Object -First 1)
    $lockPid = 0
    [void][int]::TryParse([string]$lockPidText, [ref]$lockPid)
    if ($lockPid -le 0) {
        Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
        Write-StartupLog 'Removed unreadable stale account2 lock.'
        return
    }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$lockPid" -ErrorAction SilentlyContinue
    if (-not $process -or $process.CommandLine -notmatch 'continuous_auto_trader\.py') {
        Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
        Write-StartupLog "Removed stale account2 lock for PID=$lockPid."
    }
}

function Start-Account2Trader {
    if (-not (Test-Path $Workspace)) { return 1 }
    if (-not (Test-Path $TraderScript)) {
        Write-StartupLog "Missing trader script: $TraderScript"
        return 1
    }
    if (-not (Test-Path $ConfigPath)) {
        Write-StartupLog "Missing config: $ConfigPath"
        return 1
    }
    if (-not (Test-Path $WalletPath)) {
        Write-StartupLog "Missing wallet: $WalletPath"
        return 1
    }

    $pythonExe = Resolve-Python
    if ([string]::IsNullOrWhiteSpace($pythonExe)) {
        Write-StartupLog 'Python executable not found.'
        return 1
    }

    $running = @(Get-Account2TraderProcess)
    if ($running.Count -gt 0) {
        $pids = ($running | ForEach-Object { $_.ProcessId }) -join ','
        Write-StartupLog "Account2 trader already running. PIDs=$pids"
        return 0
    }

    Clear-StaleLockIfNeeded

    $env:AUTO_TRADER_ACCOUNT_ID = 'account2_bitcoin'
    $env:MT5_WALLET_CONFIG = $WalletPath
    $env:AUTO_TRADER_USE_MT5_MARKET_DATA = '1'
    $env:AUTO_TRADER_REQUIRE_MT5_MARKET_DATA = '1'
    $env:ENABLE_MT5_MARKET_DATA = '1'
    $env:MT5_MARKET_DATA_MODE = 'mt5_only'
    $env:PYTHONUTF8 = '1'

    $args = @(
        '-u',
        ('"' + $TraderScript + '"'),
        '--config', ('"' + $ConfigPath + '"'),
        '--state', ('"' + $StatePath + '"'),
        '--wallet-config', ('"' + $WalletPath + '"'),
        '--account-id', 'account2_bitcoin'
    ) -join ' '

    Write-StartupLog "Starting account2 TP3 trader with $pythonExe"
    Start-Process -FilePath $pythonExe -ArgumentList $args -WorkingDirectory $Workspace -WindowStyle Hidden -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog
    Start-Sleep -Seconds 3

    $verify = @(Get-Account2TraderProcess)
    if ($verify.Count -gt 0) {
        $pids = ($verify | ForEach-Object { $_.ProcessId }) -join ','
        Write-StartupLog "Started account2 trader successfully. PIDs=$pids"
        return 0
    }

    $err = ''
    if (Test-Path $StderrLog) {
        $err = (Get-Content $StderrLog -Tail 8 -ErrorAction SilentlyContinue) -join ' | '
    }
    Write-StartupLog "Failed to start account2 trader. $err"
    return 1
}

$mutex = New-Object System.Threading.Mutex($false, 'Global\GOLDPRO_Account2_TP3_AutoTrader')
$gotLock = $mutex.WaitOne(0)
if (-not $gotLock) {
    Write-StartupLog 'Skipped because another account2 autostart instance is running.'
    exit 0
}

try {
    $exitCode = Start-Account2Trader
}
finally {
    $mutex.ReleaseMutex() | Out-Null
    $mutex.Dispose()
}

exit $exitCode

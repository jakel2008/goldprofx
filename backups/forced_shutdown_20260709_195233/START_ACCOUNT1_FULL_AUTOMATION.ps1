$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

function Stop-MatchingProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Pattern
    )

    Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -match $Pattern } |
        ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
                Write-Host "Stopped PID $($_.ProcessId): $($_.CommandLine)"
            } catch {
                Write-Warning "Could not stop PID $($_.ProcessId): $($_.Exception.Message)"
            }
        }
}

Stop-MatchingProcess 'site_signal_generator_runner\.py.*account1_gold'
Stop-MatchingProcess 'auto_trader_watchdog\.py.*account1_gold'
Stop-MatchingProcess 'continuous_auto_trader\.py.*account1_gold'
Stop-MatchingProcess 'mt5_trade_guardian\.py.*account1_gold'

$lock = Join-Path $PSScriptRoot "continuous_auto_trader.account1_gold.lock"
if (Test-Path $lock) {
    Remove-Item $lock -Force
    Write-Host "Removed stale account1_gold trader lock"
}

Start-Process -FilePath $python -ArgumentList @(
    "-u",
    "site_signal_generator_runner.py",
    "--config",
    "accounts/account1_gold/config.json",
    "--interval-seconds",
    "45"
) -WorkingDirectory $PSScriptRoot

Start-Process -FilePath $python -ArgumentList @(
    "-u",
    "auto_trader_watchdog.py",
    "--config",
    "accounts/account1_gold/config.json",
    "--state",
    "accounts/account1_gold/runtime_state.json",
    "--wallet-config",
    "accounts/account1_gold/wallet.json",
    "--account-id",
    "account1_gold",
    "--restart-delay",
    "5"
) -WorkingDirectory $PSScriptRoot

Start-Process -FilePath $python -ArgumentList @(
    "-u",
    "mt5_trade_guardian.py",
    "--config",
    "accounts/account1_gold/config.json",
    "--wallet-config",
    "accounts/account1_gold/wallet.json",
    "--account-id",
    "account1_gold",
    "--interval-sec",
    "10"
) -WorkingDirectory $PSScriptRoot

Write-Host "account1_gold automation started: signal generator, trader watchdog, and trade guardian."
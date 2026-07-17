param(
    [Parameter(Mandatory = $true)]
    [string]$AccountId,

    [string]$StrategyConfig = "accounts\strategy_gold_pro_tp_split_legacy_strong_signal_v1.json",

    [string]$AccountDir = ""
)

$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($AccountDir)) {
    $AccountDir = Join-Path "accounts" $AccountId
}

$python = ".\.venv-5\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "C:\Users\Discovery PC\AppData\Local\Programs\Python\Python313\python.exe"
}
if (-not (Test-Path $python)) {
    $python = "python"
}

$configPath = $StrategyConfig
$statePath = Join-Path $AccountDir "runtime_state.json"
$walletPath = Join-Path $AccountDir "wallet.json"

foreach ($requiredPath in @($configPath, $walletPath)) {
    if (-not (Test-Path $requiredPath)) {
        throw "Missing required file: $requiredPath"
    }
}

$env:AUTO_TRADER_ACCOUNT_ID = $AccountId
$env:PYTHONUTF8 = "1"

Write-Host "Starting GOLD_PRO legacy strong-signal strategy"
Write-Host "AccountId: $AccountId"
Write-Host "Strategy:  $configPath"
Write-Host "State:     $statePath"
Write-Host "Wallet:    $walletPath"

& $python -u continuous_auto_trader.py --config $configPath --state $statePath --wallet-config $walletPath --account-id $AccountId
exit $LASTEXITCODE
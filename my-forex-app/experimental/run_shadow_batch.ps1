param(
    [string]$Symbols = "XAUUSD,EURUSD,GBPUSD,BTCUSD",
    [string]$Intervals = "5m,15m,30m,1h,4h,1d",
    [string]$OutputDir = "experimental/reports",
    [string]$HistoryPath = "experimental/reports/shadow_history.jsonl",
    [int]$WeeklyLookbackDays = 7,
    [int]$MinutesToEvent = 0,
    [string]$Impact = "low",
    [double]$Surprise = 0
)

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$argsList = @(
    "experimental/run_shadow_batch.py",
    "--symbols", $Symbols,
    "--intervals", $Intervals,
    "--output-dir", $OutputDir,
    "--history-path", $HistoryPath,
    "--weekly-lookback-days", "$WeeklyLookbackDays",
    "--impact", $Impact,
    "--surprise", "$Surprise"
)

if ($MinutesToEvent -ne 0) {
    $argsList += @("--minutes-to-event", "$MinutesToEvent")
}

python @argsList

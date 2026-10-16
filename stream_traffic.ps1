# ==============================================================================
# Aegis AI Fraud Ops - Real-World Live Traffic Generator
# Runs in a separate terminal while the system is running.
# Usage:
#   .\stream_traffic.ps1
#   .\stream_traffic.ps1 -FraudRatio 0.20 -Tps 1.0 -Count 500
# ==============================================================================

param(
    [double]$Delay = 2.5,
    [double]$FraudRatio = 0.15,
    [int]$Count = 0
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$python = if (Test-Path "$scriptDir\.venv\Scripts\python.exe") {
    "$scriptDir\.venv\Scripts\python.exe"
} else {
    "python"
}

$argsList = @(
    "simulation/src/aegis_sim/stream_live_traffic.py",
    "--delay", "$Delay",
    "--fraud-ratio", "$FraudRatio"
)

if ($Count -gt 0) {
    $argsList += "--count"
    $argsList += "$Count"
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "       Aegis Live Traffic Streamer (Human Paced: 2-3s Delay)      " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "Pacing Interval:  ~$Delay seconds per transaction (Poisson randomized)" -ForegroundColor Yellow
Write-Host "Fraud Ratio:      $([math]::Round($FraudRatio * 100))% (triggers live Gemini AI reasoning)" -ForegroundColor Yellow
Write-Host "Target Endpoint:  http://localhost:8080/v1/transactions:analyze" -ForegroundColor Green
Write-Host "SOC Dashboard:    http://localhost:5173" -ForegroundColor Cyan
Write-Host "Press Ctrl+C anytime to stop streaming without killing the backend." -ForegroundColor DarkGray
Write-Host "==================================================================" -ForegroundColor Cyan

& $python @argsList

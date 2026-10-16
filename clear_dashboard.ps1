# ==============================================================================
# Aegis AI Fraud Ops - Clear Past Checked Data & Reset Dashboard (PowerShell)
# Usage:
#   .\clear_dashboard.ps1
# ==============================================================================

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$python = if (Test-Path "$scriptDir\.venv\Scripts\python.exe") {
    "$scriptDir\.venv\Scripts\python.exe"
} else {
    "python"
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "   Aegis AI Fraud Ops - Reset Dashboard & Purge Past Data        " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Cyan

& $python "$scriptDir\scripts\clean_past_data.py"

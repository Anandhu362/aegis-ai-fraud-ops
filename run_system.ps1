# ==============================================================================
# Aegis AI Fraud Ops - One-Command System Launcher (PowerShell)
# Usage:
#   .\run_system.ps1
#   .\run_system.ps1 -Traffic      (boots entire system + live transaction generator)
# ==============================================================================

param(
    [switch]$Traffic,
    [switch]$NoFrontend,
    [double]$FraudRatio = 0.15
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$python = if (Test-Path "$scriptDir\.venv\Scripts\python.exe") {
    "$scriptDir\.venv\Scripts\python.exe"
} else {
    "python"
}

$passArgs = @()
if ($Traffic) {
    $passArgs += "--traffic"
    $passArgs += "--fraud-ratio"
    $passArgs += "$FraudRatio"
}
if ($NoFrontend) {
    $passArgs += "--no-frontend"
}

& $python "$scriptDir\run_system.py" @passArgs

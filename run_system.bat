@echo off
REM ==============================================================================
REM Aegis AI Fraud Ops - One-Click System Launcher (Windows Batch)
REM Launches Actuator, Agent Engine, API Gateway, and React Dashboard concurrently.
REM ==============================================================================

cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run_system.py %*
) else (
    python run_system.py %*
)
pause

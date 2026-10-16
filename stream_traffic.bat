@echo off
REM ==============================================================================
REM Aegis AI Fraud Ops - Stream Traffic Runner (Windows Batch)
REM ==============================================================================

cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe simulation\src\aegis_sim\stream_live_traffic.py --delay 2.5 --fraud-ratio 0.15 %*
) else (
    python simulation\src\aegis_sim\stream_live_traffic.py --delay 2.5 --fraud-ratio 0.15 %*
)
pause

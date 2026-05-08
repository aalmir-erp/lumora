@echo off
REM Run the local agent on Windows. Reads ..\.env for config.
cd /d "%~dp0\.."
python -m local_agent.agent
pause

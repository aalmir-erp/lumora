@echo off
REM Lumora Scraper — local agent installer for Windows (cmd.exe friendly)
REM Double-click to run.

echo [install] checking python...
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not in PATH. Install from https://www.python.org/downloads/ first.
  pause
  exit /b 1
)

cd /d "%~dp0"

echo [install] pip install local agent deps...
python -m pip install --upgrade pip
if errorlevel 1 goto fail
python -m pip install -r requirements.txt
if errorlevel 1 goto fail

echo [install] playwright install chrome...
python -m playwright install chrome
if errorlevel 1 goto fail

if not exist "..\.env" (
  echo.
  for /f "tokens=*" %%t in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set TOKEN=%%t
  echo Generated LOCAL_AGENT_TOKEN: %TOKEN%
  echo Add this SAME value to your GitHub repo secret AND Railway service vars.
  echo.
  set /p SERVER=Enter SCRAPER_SERVER_URL (e.g. wss://scraper-production.up.railway.app):
  set /p AGENT=Enter AGENT_ID (default %COMPUTERNAME%):
  if "%AGENT%"=="" set AGENT=%COMPUTERNAME%
  (
    echo SCRAPER_SERVER_URL=%SERVER%
    echo LOCAL_AGENT_TOKEN=%TOKEN%
    echo AGENT_ID=%AGENT%
  ) > "..\.env"
  echo [install] wrote ..\.env
)

echo.
echo [install] DONE. To run the agent:
echo   cd ..
echo   python -m local_agent.agent
echo.
pause
exit /b 0

:fail
echo [install] FAILED
pause
exit /b 1

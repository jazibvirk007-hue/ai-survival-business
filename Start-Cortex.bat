@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ================================================
echo          TJ CORTEX LOCAL STARTUP
 echo ================================================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Cortex is not installed yet. Running the installer...
  call "%~dp0Install-Cortex.bat"
  if errorlevel 1 exit /b 1
)

echo Checking Cortex startup modules...
.venv\Scripts\python.exe -c "import ai_ceo, cortex_v95_orchestrator; print('Cortex core: OK')"
if errorlevel 1 (
  echo Cortex core validation failed. Run Install-Cortex.bat again.
  pause
  exit /b 1
)

 echo Starting Cortex Command Center...
start "TJ Cortex Command Center" /b "%~dp0.venv\Scripts\python.exe" "%~dp0cortex_dashboard.py"

timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8080/"

echo Cortex Command Center launch requested.
exit /b 0

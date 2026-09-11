@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ================================================
echo          TJ CORTEX LOCAL INSTALLER
echo ================================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
) else (
  where python >nul 2>&1
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    echo Python 3 is required but was not found.
    echo Install Python 3.11+ and run this installer again.
    pause
    exit /b 1
  )
)

%PY% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo Cortex requires Python 3.11 or newer.
  %PY% --version
  pause
  exit /b 1
)

echo [1/4] Creating isolated Cortex environment...
if not exist ".venv\Scripts\python.exe" (
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)

echo [2/4] Verifying Python runtime...
.venv\Scripts\python.exe -c "import sys; print('Python', sys.version.split()[0])"
if errorlevel 1 goto :fail

 echo [3/4] Validating Cortex Python source...
.venv\Scripts\python.exe -m compileall -q .
if errorlevel 1 goto :fail
.venv\Scripts\python.exe -c "import ai_ceo, cortex_v95_orchestrator"
if errorlevel 1 goto :fail

 echo [4/4] Preparing local configuration...
if not exist ".env.example" (
  >.env.example echo # Optional Cortex AI configuration
  >>.env.example echo # TJ_CORTEX_AI_MODE=local
  >>.env.example echo # TJ_CORTEX_AI_BASE_URL=http://127.0.0.1:11434/v1
  >>.env.example echo # TJ_CORTEX_AI_MODEL=local-model
  >>.env.example echo # API credentials must remain in your machine environment, never in source control.
)

if not exist "data" mkdir data
if not exist "logs" mkdir logs

 echo.
echo ================================================
echo       CORTEX INSTALLATION READY
 echo ================================================
echo.
echo Source validation: OK
echo Local environment: OK
echo.
echo Double-click Start-Cortex.bat to launch the Command Center.
echo.
pause
exit /b 0

:fail
echo.
echo ================================================
echo      CORTEX INSTALLATION CHECK FAILED
 echo ================================================
echo.
echo No source files were modified by the installer.
echo Review the message above and run the installer again after fixing the issue.
echo.
pause
exit /b 1

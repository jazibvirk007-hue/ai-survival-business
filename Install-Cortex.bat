@echo off
setlocal
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
    echo Install Python 3.11+ from the official Python website and run this installer again.
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

echo [1/3] Creating isolated Cortex environment...
if not exist ".venv\Scripts\python.exe" (
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)

echo [2/3] Checking Cortex modules...
.venv\Scripts\python.exe -c "import ai_ceo, cortex_v95_orchestrator, cortex_dashboard"
if errorlevel 1 goto :fail

echo [3/3] Creating local configuration template...
if not exist ".env.example" (
  >.env.example echo # Optional Cortex AI configuration
  >>.env.example echo # TJ_CORTEX_AI_MODE=local
  >>.env.example echo # TJ_CORTEX_AI_BASE_URL=http://127.0.0.1:11434/v1
  >>.env.example echo # TJ_CORTEX_AI_MODEL=local-model
  >>.env.example echo # API credentials must remain in your machine's environment, never in source control.
)

echo.
echo ================================================
echo       CORTEX INSTALLATION READY
 echo ================================================
echo.
echo Use Start-Cortex.bat to launch the local Command Center.
echo.
pause
exit /b 0

:fail
echo.
echo Cortex installation check failed.
echo No source files were modified by the installer.
echo.
pause
exit /b 1

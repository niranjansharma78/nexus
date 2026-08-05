@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Nexus
cd /d "%~dp0"
set "PYTHON_CMD="
py -3.14 -c "import sys; print(sys.version)" >nul 2>&1
if %errorlevel%==0 set "PYTHON_CMD=py -3.14"
if not defined PYTHON_CMD (
  python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,14) else 1)" >nul 2>&1
  if %errorlevel%==0 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo [ERROR] Python 3.14 was not found.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [NEXUS] Creating Python 3.14 virtual environment...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :failed
)
call ".venv\Scripts\activate.bat"
python --version
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :failed
python -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto :failed
python scripts\doctor.py
if errorlevel 1 goto :failed
if exist "seed.py" python seed.py
if errorlevel 1 goto :failed
echo [NEXUS] Starting at http://127.0.0.1:8010
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
goto :eof
:failed
echo [ERROR] Nexus could not start.
python scripts\doctor.py --report nexus_diagnostic.txt >nul 2>&1
echo Share nexus_diagnostic.txt.
pause
exit /b 1

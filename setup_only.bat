@echo off
setlocal
cd /d "%~dp0"
py -3.14 -m venv .venv
if errorlevel 1 (
  echo Python 3.14 was not found through the Windows py launcher.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install --upgrade -r requirements.txt
python scripts\doctor.py --report nexus_diagnostic.txt
echo Setup completed. Run run.bat to start Nexus.
pause

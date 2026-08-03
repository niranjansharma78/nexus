@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Nexus virtual environment not found.
  exit /b 1
)
.venv\Scripts\python -m pip install pytest
.venv\Scripts\python -m pytest

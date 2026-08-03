@echo off
setlocal
cd /d "%~dp0\.."
if exist ".venv" rmdir /s /q ".venv"
if exist "nexus_diagnostic.txt" del /q "nexus_diagnostic.txt"
echo Old environment removed. Run setup_only.bat or run.bat.
pause

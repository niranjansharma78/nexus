@echo off
setlocal
cd /d %~dp0

set /p BACKEND_IP=Enter backend PC IP, for example 192.168.0.115: 
if "%BACKEND_IP%"=="" exit /b 1

flutter run -d RZCW920TGKL --dart-define=NEXUS_API_URL=http://%BACKEND_IP%:8010

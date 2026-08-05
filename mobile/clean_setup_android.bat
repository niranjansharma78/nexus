@echo off
setlocal
cd /d %~dp0

if exist android rmdir /s /q android
if exist build rmdir /s /q build
if exist .dart_tool rmdir /s /q .dart_tool

flutter create --platforms=android .
if errorlevel 1 exit /b 1

flutter pub get
if errorlevel 1 exit /b 1

flutter analyze
if errorlevel 1 exit /b 1

flutter test
if errorlevel 1 exit /b 1

echo.
echo Nexus Mobile v1.2 is ready.

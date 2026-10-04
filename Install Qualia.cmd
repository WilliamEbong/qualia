@echo off
rem Double-click to install or update Qualia. See README "Get started".
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-qualia.ps1"
echo.
pause

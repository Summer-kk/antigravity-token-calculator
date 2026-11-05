@echo off
chcp 65001 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0restart_dashboard.ps1"
pause

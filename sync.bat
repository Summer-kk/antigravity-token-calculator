@echo off
pwsh -ExecutionPolicy Bypass -File "%~dp0sync.ps1"
if %errorlevel% neq 0 powershell -ExecutionPolicy Bypass -File "%~dp0sync.ps1"

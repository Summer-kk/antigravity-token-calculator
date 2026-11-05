@echo off
chcp 65001 >nul
where py >nul 2>nul && (set "PYTHON_EXE=py") || (set "PYTHON_EXE=python")
"%PYTHON_EXE%" "%~dp0analyze_tokens_by_project.py" %*

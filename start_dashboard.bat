@echo off
chcp 65001 >nul
echo ======================================================
echo  正在启动 Antigravity Token 统计仪表盘后台服务...
echo  服务地址: http://127.0.0.1:5899/
echo  提示: 您可以直接在 Antigravity 界面内通过内置侧窗打开!
echo ======================================================

where py >nul 2>nul && (set "PYTHON_EXE=py") || (set "PYTHON_EXE=python")

"%PYTHON_EXE%" "%~dp0sidecars\token-dashboard\server.py" %*

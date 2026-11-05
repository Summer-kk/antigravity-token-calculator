@echo off
chcp 65001 >nul
echo 正在扫描 Antigravity 本地全量对话与项目 Token 消耗...

where py >nul 2>nul && (set "PYTHON_EXE=py") || (set "PYTHON_EXE=python")

"%PYTHON_EXE%" "%~dp0update_dashboard.py"
call "%~dp0sync.bat"
echo [完成] 侧边栏仪表盘数据已全量更新并同步！
pause

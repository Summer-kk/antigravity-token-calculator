#!/usr/bin/env bash
# Antigravity Token Calculator Sidecar Launcher
echo "======================================================"
echo " 正在启动 Antigravity Token 统计仪表盘后台服务..."
echo " 服务地址: http://127.0.0.1:5899/"
echo " 提示: 可直接在 Antigravity 界面内通过内置侧窗打开"
echo "======================================================"

PYTHON_EXE="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_EXE="python"
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
"$PYTHON_EXE" "$DIR/sidecars/token-dashboard/server.py" "$@"

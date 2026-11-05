$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    $pythonExe = "python"
}

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " 正在启动 Antigravity Token 统计仪表盘后台服务..." -ForegroundColor Green
Write-Host " 服务地址: http://127.0.0.1:5899/" -ForegroundColor Cyan
Write-Host " 提示: 可直接在 Antigravity 界面内通过内置侧窗打开" -ForegroundColor Yellow
Write-Host "======================================================" -ForegroundColor Cyan
& $pythonExe "$PSScriptRoot\sidecars\token-dashboard\server.py" @args

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 正在重置并重启 Antigravity Token 统计仪表盘服务..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. 清理本地缓存并重新聚合
Write-Host "正在全量重新扫描双端数据..." -ForegroundColor Yellow
& py "$PSScriptRoot\update_dashboard.py"

# 2. 同步全局插件
Write-Host "正在同步最新代码至全局插件目录..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "sync.ps1")

Write-Host "✅ Token 统计插件服务重置与同步完成！" -ForegroundColor Green

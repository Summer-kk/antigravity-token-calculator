$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$src = $PSScriptRoot
$dst = Join-Path $HOME ".gemini\config\plugins\token-calculator"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " 🚀 Antigravity 插件实时自动热同步监听器已启动!" -ForegroundColor Green
Write-Host " 源目录: $src" -ForegroundColor Gray
Write-Host " 目标目录: $dst" -ForegroundColor Gray
Write-Host " 提示: 只要在工作区修改或保存任何文件，将自动毫秒级同步到全局插件！" -ForegroundColor Yellow
Write-Host "======================================================" -ForegroundColor Cyan

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $src
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$syncAction = {
    param($source, $event)
    $name = $event.Name
    if ($name -match "__pycache__|\.git|sync_to_global|watch_and_sync") { return }
    Start-Sleep -Milliseconds 100
    robocopy "$src\." "$dst\." /E /XD __pycache__ .git /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 自动同步变更: $name" -ForegroundColor DarkCyan
}

Register-ObjectEvent $watcher 'Changed' -Action $syncAction | Out-Null
Register-ObjectEvent $watcher 'Created' -Action $syncAction | Out-Null
Register-ObjectEvent $watcher 'Deleted' -Action $syncAction | Out-Null
Register-ObjectEvent $watcher 'Renamed' -Action $syncAction | Out-Null

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Unregister-Event -SourceIdentifier *
    $watcher.Dispose()
}

$src = $PSScriptRoot
$dst = Join-Path $HOME ".gemini\config\plugins\token-calculator"
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }
robocopy "$src" "$dst" /E /XD __pycache__ .git /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
Write-Host "✅ 全局插件已同步更新至: $dst" -ForegroundColor Green

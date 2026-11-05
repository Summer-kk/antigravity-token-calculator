$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    $pythonExe = "python"
}

& $pythonExe "$PSScriptRoot\analyze_tokens_by_project.py" @args

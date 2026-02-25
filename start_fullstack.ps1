$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$venvPython = ".venv\Scripts\python.exe"
$pythonCmd = "python"

if (Test-Path $venvPython) {
    $venvHasDjango = $false
    try {
        & $venvPython -c "import django" *> $null
        $venvHasDjango = ($LASTEXITCODE -eq 0)
    } catch {
        $venvHasDjango = $false
    }

    if ($venvHasDjango) {
        $pythonCmd = $venvPython
    } else {
        Write-Host "Virtual environment found but Django is not installed there. Falling back to system python." -ForegroundColor Yellow
    }
}

Write-Host "Starting Django backend on http://127.0.0.1:8000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot'; & '$pythonCmd' backend\manage.py runserver 127.0.0.1:8000"

Write-Host "Starting React frontend on http://127.0.0.1:5173 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot\frontend'; npm run dev -- --host 127.0.0.1"

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5173"

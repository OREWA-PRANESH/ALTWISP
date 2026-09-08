$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    py -m venv (Join-Path $ProjectRoot "venv")
}

& $Python -m pip install -r (Join-Path $ProjectRoot "requirements-local.txt")
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements-dev.txt")
Push-Location (Join-Path $ProjectRoot "src")
try {
    & $Python -m PyInstaller --clean --noconfirm ALTWISP.spec
}
finally {
    Pop-Location
}

Write-Host "Built: $ProjectRoot\src\dist\ALTWISP.exe"

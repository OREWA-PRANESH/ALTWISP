$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Venv = Join-Path $Root '.venv-worker'
$Python = Join-Path $Venv 'Scripts\python.exe'
$Requirements = Join-Path $Root 'requirements-worker.txt'

if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create worker environment' }
}

& $Python -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw 'Failed to install worker dependencies' }
& $Python -m PyInstaller --noconfirm --clean --onefile --console --name altwisp-worker --distpath (Join-Path $Root 'native\dist') --workpath (Join-Path $Root 'native\build') --specpath (Join-Path $Root 'native') (Join-Path $Root 'native\agent.py')
if ($LASTEXITCODE -ne 0) { throw 'Failed to package native worker' }

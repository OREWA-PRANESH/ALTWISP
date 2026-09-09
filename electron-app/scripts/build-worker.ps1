$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Parent = Split-Path -Parent $Root
$Python = Join-Path $Parent 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = Join-Path $Parent 'ALTWISP\venv\Scripts\python.exe'
}
& $Python -m PyInstaller --noconfirm --clean --onefile --console --name altwisp-worker --distpath (Join-Path $Root 'native\dist') --workpath (Join-Path $Root 'native\build') --specpath (Join-Path $Root 'native') (Join-Path $Root 'native\agent.py')

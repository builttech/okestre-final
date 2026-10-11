param([string]$Python = ".venv\Scripts\python.exe")
$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $PSScriptRoot
Push-Location $projectDirectory
try {
    & $Python -m PyInstaller --noconfirm --clean --windowed --onedir --name OkestreLocal `
        --distpath outputs/okestre-local --workpath outputs/okestre-local/build `
        --specpath outputs/okestre-local --hidden-import pystray._win32 --hidden-import win32crypt `
        --collect-submodules websockets okestre-local.py
    if ($LASTEXITCODE -ne 0) { throw "Falha ao empacotar Okestre Local." }
    Write-Output "Aplicativo: $projectDirectory\outputs\okestre-local\OkestreLocal\OkestreLocal.exe"
} finally {
    Pop-Location
}

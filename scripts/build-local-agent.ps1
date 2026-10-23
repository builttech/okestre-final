param([string]$Python = ".venv\Scripts\python.exe")
$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $PSScriptRoot
Push-Location $projectDirectory
try {
    $canonicalExecutable = [IO.Path]::GetFullPath((Join-Path $projectDirectory 'outputs/okestre-local/OkestreLocal/OkestreLocal.exe'))
    $activeLocal = Get-Process OkestreLocal -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $canonicalExecutable }
    if ($activeLocal) { throw "Saia do Okestre Local pela bandeja antes de atualizar a pasta oficial. O perfil em LOCALAPPDATA sera preservado." }
    & $Python -m PyInstaller --noconfirm --clean --windowed --onedir --name OkestreLocal `
        --distpath outputs/okestre-local --workpath outputs/okestre-local/build `
        --specpath outputs/okestre-local --hidden-import pystray._win32 --hidden-import win32crypt `
        --collect-submodules websockets okestre-local.py
    if ($LASTEXITCODE -ne 0) { throw "Falha ao empacotar Okestre Local." }
    Copy-Item -LiteralPath LOCAL_AGENT.md -Destination outputs/okestre-local/OkestreLocal/LEIA-ME.md
    Compress-Archive -Path outputs/okestre-local/OkestreLocal -DestinationPath outputs/okestre-local/OkestreLocal-Windows-x64.zip -Force
    Write-Output "Aplicativo: $projectDirectory\outputs\okestre-local\OkestreLocal\OkestreLocal.exe"
} finally {
    Pop-Location
}

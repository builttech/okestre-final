param([string]$Python = ".venv\Scripts\python.exe")
$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $PSScriptRoot
Push-Location $projectDirectory
try {
    & $Python -m PyInstaller --noconfirm --windowed --onedir --name OkestreDesktop `
        --distpath outputs/okestre-desktop --workpath outputs/okestre-desktop/build --specpath outputs/okestre-desktop `
        --collect-all webview --collect-all pythonnet --collect-all clr_loader `
        --hidden-import webview.platforms.winforms --hidden-import win32crypt `
        --add-data "$projectDirectory/okestre_desktop/ui;okestre_desktop/ui" `
        --add-data "$projectDirectory/gitide_server/static/er-diagram.html;gitide_server/static" `
        --add-data "$projectDirectory/gitide_server/static/er-diagram.css;gitide_server/static" `
        --add-data "$projectDirectory/gitide_server/static/er-diagram.js;gitide_server/static" `
        --add-data "$projectDirectory/gitide_server/static/vendor;gitide_server/static/vendor" okestre-desktop.py
    if ($LASTEXITCODE -ne 0) { throw "Falha ao empacotar Okestre Desktop." }
    Copy-Item DESKTOP.md outputs/okestre-desktop/OkestreDesktop/LEIA-ME.md
    Compress-Archive -Path outputs/okestre-desktop/OkestreDesktop -DestinationPath outputs/okestre-desktop/OkestreDesktop-Windows.zip -Force
    Write-Output "Aplicativo: $projectDirectory\outputs\okestre-desktop\OkestreDesktop\OkestreDesktop.exe"
} finally { Pop-Location }

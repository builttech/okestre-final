param([string]$Python = ".venv\Scripts\python.exe", [string]$OutputDirectory = "outputs/okestre-desktop")
$ErrorActionPreference = "Stop"
$projectDirectory = Split-Path -Parent $PSScriptRoot
Push-Location $projectDirectory
try {
    $dataArguments = @()
    Get-ChildItem -LiteralPath $projectDirectory -File -Filter '*.md' | ForEach-Object {
        $dataArguments += @('--add-data', ($_.FullName + ';.'))
    }
    & $Python -m PyInstaller --noconfirm --windowed --onedir --name OkestreDesktop `
        --distpath $OutputDirectory --workpath outputs/okestre-desktop/build --specpath $OutputDirectory `
        --collect-all webview --collect-all pythonnet --collect-all clr_loader `
        --collect-data mcp --collect-all markitdown --collect-all magika --collect-all openai `
        --collect-all pypdfium2 --collect-all pypdfium2_raw --collect-data docx `
        --hidden-import webview.platforms.winforms --hidden-import win32crypt `
        --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols.http.auto `
        --hidden-import uvicorn.protocols.websockets.auto --hidden-import uvicorn.lifespan.on `
        --hidden-import psycopg2 --hidden-import pymysql --hidden-import pglast `
        --add-data "$projectDirectory/okestre_desktop/ui;okestre_desktop/ui" `
        --add-data "$projectDirectory/gitide_server/static;gitide_server/static" `
        --add-data "$projectDirectory/gitide_server/templates;gitide_server/templates" @dataArguments okestre-desktop.py
    if ($LASTEXITCODE -ne 0) { throw "Falha ao empacotar Okestre Desktop completo." }
    Copy-Item DESKTOP.md "$OutputDirectory/OkestreDesktop/LEIA-ME.md"
    Compress-Archive -Path "$OutputDirectory/OkestreDesktop" -DestinationPath "$OutputDirectory/OkestreDesktop-Windows.zip" -Force
    Write-Output "Aplicativo: $OutputDirectory/OkestreDesktop/OkestreDesktop.exe"
} finally { Pop-Location }

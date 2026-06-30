@echo off
setlocal

set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%gitide_sync.py" %*

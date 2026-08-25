$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$env:PYTHONIOENCODING = "utf-8:replace"
$env:PYTHONUTF8 = "1"
$env:PYTHONLEGACYWINDOWSSTDIO = "0"
$env:FLET_CLI_NO_RICH_OUTPUT = "1"
$env:NO_COLOR = "1"
$env:TERM = "dumb"

& "$ProjectRoot\env\Scripts\python.exe" "$PSScriptRoot\crear_instalador.py" 4
exit $LASTEXITCODE

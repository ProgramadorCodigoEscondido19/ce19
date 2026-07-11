$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot

$env:PYTHONIOENCODING = "utf-8:replace"
$env:PYTHONUTF8 = "1"
$env:PYTHONLEGACYWINDOWSSTDIO = "0"
$env:FLET_CLI_NO_RICH_OUTPUT = "1"
$env:NO_COLOR = "1"
$env:TERM = "dumb"

$log = Join-Path $PSScriptRoot "build_windows.log"
"Inicio build Windows: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $log

$argsFlet = @(
    "build",
    "windows",
    "--project",
    "codigo_escondido_19",
    "--artifact",
    "CODIGO ESCONDIDO 19",
    "--product",
    "CODIGO ESCONDIDO 19",
    "--description",
    "Aplicacion Codigo Escondido 19",
    "--company",
    "CODIGO ESCONDIDO 19",
    "--org",
    "com.flet",
    "--bundle-id",
    "com.flet.app_ce_19",
    "--android-adaptive-icon-background",
    "#71106F",
    "--splash-color",
    "#71106F",
    "--splash-dark-color",
    "#71106F",
    "--build-version",
    "1.0.0",
    "--exclude",
    "datos/audios_biblia",
    "--no-rich-output",
    "--yes",
    "--skip-flutter-doctor"
)

& "$PSScriptRoot\env\Scripts\flet.exe" @argsFlet 2>&1 | Tee-Object -FilePath $log -Append
$code = $LASTEXITCODE

"Fin build Windows: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | Codigo: $code" | Tee-Object -FilePath $log -Append
exit $code

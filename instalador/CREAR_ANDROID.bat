@echo off
cd /d "%~dp0\.."
"%~dp0..\env\Scripts\flet.exe" build apk ^
 --project codigo_escondido_19 ^
 --artifact "CODIGO ESCONDIDO 19" ^
 --product "CODIGO ESCONDIDO 19" ^
 --description "Aplicacion Codigo Escondido 19" ^
 --company "CODIGO ESCONDIDO 19" ^
 --org com.flet ^
 --bundle-id com.flet.app_ce_19 ^
 --android-adaptive-icon-background "#71106F" ^
 --splash-color "#71106F" ^
 --splash-dark-color "#71106F" ^
 --build-version 1.8 ^
 --no-rich-output ^
 --yes ^
 --skip-flutter-doctor ^
 --cleanup-app ^
 --exclude .git .github .venv env build dist dist_windows release backups logs storage instalador __pycache__ "*.pyc" README.md .gitignore "CODIGO-ESCONDIDO-19-*.apk" "CODIGO-ESCONDIDO-19-*.zip" datos/exportaciones datos/historial.json datos/guardados.json datos/carpetas.json datos/config_tiempo.json datos/analisis_colores_historial.json datos/historial_referencias_biblia.json datos/favoritos_biblia.json datos/notas_biblia.json datos/resaltados_biblia.json datos/ultima_lectura_biblia.json
pause

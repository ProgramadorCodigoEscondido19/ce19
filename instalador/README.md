# Instalador

Esta carpeta contiene los accesos para crear instaladores de la app.

- `CREAR_ANDROID.bat`: crea directamente el APK de Android.
- `CREAR_WINDOWS.bat`: crea directamente el paquete de Windows.

El paquete de macOS se construye en un equipo Mac mediante el flujo manual
`.github/workflows/macos-release.yml` de GitHub Actions.

Los archivos generados quedan fuera de esta carpeta, en las salidas normales de Flet:

- Android: `CODIGO-ESCONDIDO-19-Android.apk`
- Windows: `dist_windows` y `CODIGO-ESCONDIDO-19-Windows.zip`

La version final se mantiene en `1.9`. El numero tecnico de compilacion de
Android se genera automaticamente y no modifica la version visible de la app.

Nota: Windows necesita Visual Studio Build Tools con desarrollo de escritorio en C++.

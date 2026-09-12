# Instalador

Esta carpeta contiene los accesos para crear instaladores de la app.

- `CREAR_ANDROID.bat`: crea directamente el APK de Android.
- `CREAR_WINDOWS.bat`: crea directamente el paquete de Windows.

Los instaladores terminados quedan en `Para_compartir/`:

- Android: `CODIGO-ESCONDIDO-19-Android-v1.9.apk`
- Windows: `CODIGO-ESCONDIDO-19-Windows-v1.9.zip`

La versión se lee de `APP_VERSION` en `ui/tema.py`. El número técnico de compilación de
Android se genera automaticamente y no modifica la version visible de la app.

Nota: Windows necesita Visual Studio Build Tools con desarrollo de escritorio en C++.

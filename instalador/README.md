# Instalador

Esta carpeta contiene los accesos para crear instaladores de la app.

- `CREAR_INSTALADOR.bat`: abre un menu para elegir Android o Windows.
- `CREAR_ANDROID.bat`: crea directamente el APK de Android.
- `CREAR_WINDOWS.bat`: crea directamente el paquete de Windows.

Los archivos generados quedan fuera de esta carpeta, en las salidas normales de Flet:

- Android: `build/apk`
- Windows: `build/windows`, `dist_windows` y `CODIGO-ESCONDIDO-19-Windows-v1.9.zip`

Nota: Windows necesita Visual Studio Build Tools con desarrollo de escritorio en C++.

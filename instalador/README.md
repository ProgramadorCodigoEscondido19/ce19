# Instalador

Esta carpeta contiene los accesos para crear instaladores de la app.

- `CREAR_INSTALADOR.bat`: abre un menu para elegir Android o Windows.
- `CREAR_ANDROID.bat`: crea directamente el APK de Android.
- `CREAR_WINDOWS.bat`: crea directamente el paquete de Windows.

Los archivos generados quedan fuera de esta carpeta, en las salidas normales de Flet:

- Android: `build/apk`
- Windows: `build/windows`, `dist_windows` y `CODIGO-ESCONDIDO-19-Windows-2026-08-28.zip`

La version final se mantiene en `1.9`. El nombre del paquete usa
`APP_UPDATE_DATE`, definida en `ui/tema.py`.

En Android, esa fecha tambien se convierte en el numero interno de
compilacion (`2026-08-30` se convierte en `20260830`).
La herramienta nativa recibe `1.9.0` por compatibilidad con Flet, aunque la
aplicacion continua mostrando `1.9` al usuario.

Nota: Windows necesita Visual Studio Build Tools con desarrollo de escritorio en C++.

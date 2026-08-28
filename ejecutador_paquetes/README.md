# Ejecutador de paquetes

Esta carpeta contiene accesos separados para crear los paquetes descargables de la app.

- `CREAR_PAQUETES.bat`: permite crear Android, Windows o ambos.
- `CREAR_ANDROID.bat`: crea solo el APK de Android.
- `CREAR_WINDOWS.bat`: crea solo el ZIP de Windows.

Salidas esperadas:

- Android: `CODIGO-ESCONDIDO-19-Android-2026-08-28.apk`
- Windows: `CODIGO-ESCONDIDO-19-Windows-2026-08-28.zip`

La version de la app permanece en `1.9`. Antes de crear una actualizacion,
cambie `APP_UPDATE_DATE` en `ui/tema.py` por la fecha de publicacion.

Publique una nueva Release con una etiqueta como
`actualizacion-2026-08-30` y adjunte los dos paquetes generados. Android usa
la fecha como numero interno de compilacion para permitir instalar el APK
sobre una edicion anterior de la misma version `1.9`.

El ejecutador reutiliza `instalador/crear_instalador.py`, que contiene las validaciones del paquete.
Windows requiere Visual Studio Build Tools con desarrollo de escritorio en C++.

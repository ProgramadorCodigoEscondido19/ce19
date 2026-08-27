# Ejecutador de paquetes

Esta carpeta contiene accesos separados para crear los paquetes descargables de la app.

- `CREAR_PAQUETES.bat`: permite crear Android, Windows o ambos.
- `CREAR_ANDROID.bat`: crea solo el APK de Android.
- `CREAR_WINDOWS.bat`: crea solo el ZIP de Windows.

Salidas esperadas:

- Android: `CODIGO-ESCONDIDO-19-Android-v1.9.apk`
- Windows: `CODIGO-ESCONDIDO-19-Windows-v1.9.zip`

El ejecutador reutiliza `instalador/crear_instalador.py`, que contiene las validaciones del paquete.
Windows requiere Visual Studio Build Tools con desarrollo de escritorio en C++.

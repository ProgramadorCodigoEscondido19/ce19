@echo off
cd /d "%~dp0\.."
"%~dp0..\env\Scripts\python.exe" "%~dp0crear_paquetes.py" windows
pause

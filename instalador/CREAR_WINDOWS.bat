@echo off
cd /d "%~dp0\.."
"%~dp0..\env\Scripts\python.exe" "%~dp0crear_instalador.py" 4
pause

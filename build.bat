@echo off
cd /d "%~dp0"
echo Building DISENO_SUBESTACIONES.exe ...
pyinstaller --onefile --console --name "DISENO_SUBESTACIONES" ^
    --add-data "templates;templates" --add-data "static;static" ^
    --add-data "modulos;modulos" ^
    --collect-data matplotlib --collect-data numpy --collect-data scipy ^
    desktop.py
echo.
echo Done! .exe is in dist\DISENO_SUBESTACIONES.exe
pause

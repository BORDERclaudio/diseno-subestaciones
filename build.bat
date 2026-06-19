@echo off
cd /d "%~dp0"
echo Building DISENO_SUBESTACIONES.exe ...

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "DISENO_SUBESTACIONES" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "modulos;modulos" ^
    --add-data ".gitignore;." ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.loops.auto ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import jinja2.ext ^
    --hidden-import matplotlib.backends.backend_agg ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import numpy.core.multiarray ^
    --hidden-import scipy._lib.messagestream ^
    --hidden-import sqlalchemy.sql.default_comparator ^
    --hidden-import bcrypt ^
    --hidden-import jwt ^
    --collect-data matplotlib ^
    --collect-data numpy ^
    --collect-data scipy ^
    desktop.py

echo.
echo Done! The .exe is in the dist\ folder
pause

@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -m reaper_text_project
) else (
    python -m reaper_text_project
)

if not %errorlevel%==0 (
    echo.
    echo Error al abrir la GUI.
    echo Si es la primera vez, instala dependencias con:
    echo   pip install -e .
    pause
)

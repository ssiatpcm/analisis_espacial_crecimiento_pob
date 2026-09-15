@echo off
REM =====================================================================
REM  SETUP.bat — Ejecutar UNA vez dentro de la carpeta del repositorio
REM  Crea todas las carpetas y archivos del proyecto automaticamente.
REM  Anaconda Prompt: .\SETUP.bat
REM =====================================================================

echo.
echo === Creando estructura de carpetas ===
echo.

mkdir pages         2>nul
mkdir utils         2>nul
mkdir data\raw      2>nul
mkdir data\processed 2>nul
mkdir data\shapes   2>nul
mkdir notebooks     2>nul
mkdir tests         2>nul
mkdir assets        2>nul
mkdir .streamlit    2>nul

echo Carpetas creadas correctamente.
echo.

REM --- Placeholders para carpetas vacias (git no versiona carpetas vacias) ---
echo. > data\raw\.gitkeep
echo. > data\processed\.gitkeep
echo. > data\shapes\.gitkeep
echo. > pages\.gitkeep
echo. > notebooks\.gitkeep
echo. > assets\.gitkeep

REM --- Archivo de tests ---
echo. > tests\__init__.py

echo === Estructura lista ===
echo.
echo Siguiente paso: crear el entorno conda con:
echo.
echo   conda env create -f environment.yml
echo.
echo Luego activarlo con:
echo.
echo   conda activate ssiat-crecimiento
echo.
pause

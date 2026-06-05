@echo off
chcp 65001 >nul
cd /d "%~dp0"
python "%~dp0converter_para_jpeg.py"
if errorlevel 1 (
    echo.
    echo Nao foi possivel abrir o conversor.
    echo Leia LEIA-ME.txt ou rode instalar.bat primeiro.
    pause
)

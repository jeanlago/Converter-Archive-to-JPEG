@echo off
chcp 65001 >nul
echo ========================================
echo   CONVERSOR PARA JPEG - INSTALACAO
echo   Feito por Jean, irma de Thalyta backoffice
echo ========================================
echo.
echo Este passo instala o que o conversor precisa.
echo So precisa fazer isso UMA VEZ no computador.
echo.
echo Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"
echo.
if errorlevel 1 (
    echo ERRO na instalacao.
    echo.
    echo Verifique se o Python esta instalado:
    echo https://www.python.org/downloads/
    echo.
    echo Na instalacao, marque "Add Python to PATH".
) else (
    echo Pronto! Agora pode abrir converter_para_jpeg.bat
    echo Leia LEIA-ME.txt para instrucoes completas.
)
echo.
pause

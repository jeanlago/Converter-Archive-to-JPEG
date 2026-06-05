@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ========================================
echo   MONTAR EXECUTAVEL - CONVERSOR JPEG
echo   Feito por Jean, irma de Thalyta Marins backoffice
echo ========================================
echo.

python -c "import struct; print('Build deste PC:', struct.calcsize('P') * 8, 'bits')" 2>nul
echo O executavel so funciona em Windows 64 bits.
echo.

echo [0/3] Preparando ambiente...
taskkill /IM ConversorParaJPEG.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

set "BUILD_ROOT=%TEMP%\conversor_jpeg_build"
set "DIST_BUILD=%BUILD_ROOT%\dist"
set "WORK_BUILD=%BUILD_ROOT%\build"
set "EXE_SAIDA=%~dp0dist\ConversorParaJPEG.exe"
set "ZIP_SAIDA=%~dp0dist\ConversorParaJPEG.zip"

if exist "%BUILD_ROOT%" rmdir /S /Q "%BUILD_ROOT%" 2>nul
mkdir "%BUILD_ROOT%" 2>nul

echo.
echo [1/3] Instalando ferramentas de build...
python -m pip install --upgrade pip
python -m pip install pyinstaller pillow
if errorlevel 1 (
    echo.
    echo ERRO: nao foi possivel instalar as dependencias.
    echo Verifique se o Python esta instalado e no PATH.
    pause
    exit /b 1
)

echo.
echo [2/3] Gerando executavel unico (pode demorar alguns minutos)...
echo Build temporario em: %BUILD_ROOT%
python -m PyInstaller --noconfirm ^
    --distpath "%DIST_BUILD%" ^
    --workpath "%WORK_BUILD%" ^
    "%~dp0ConversorParaJPEG.spec"

if errorlevel 1 (
    echo.
    echo ERRO: falha ao montar o executavel.
    echo.
    echo Dicas:
    echo - Feche o ConversorParaJPEG se estiver aberto
    echo - Feche a pasta dist no Explorer
    echo - Pause a sincronizacao do OneDrive e tente de novo
    pause
    exit /b 1
)

if not exist "%DIST_BUILD%\ConversorParaJPEG.exe" (
    echo.
    echo ERRO: o executavel nao foi gerado.
    pause
    exit /b 1
)

echo.
echo [3/3] Copiando executavel final...
if not exist "%~dp0dist" mkdir "%~dp0dist"

copy /Y "%DIST_BUILD%\ConversorParaJPEG.exe" "%EXE_SAIDA%" >nul
if exist "%~dp0LEIA-ME.txt" copy /Y "%~dp0LEIA-ME.txt" "%~dp0dist\LEIA-ME.txt" >nul

if exist "%ZIP_SAIDA%" del /F /Q "%ZIP_SAIDA%" 2>nul
powershell -NoProfile -Command "Compress-Archive -Path '%EXE_SAIDA%','%~dp0dist\LEIA-ME.txt' -DestinationPath '%ZIP_SAIDA%' -Force" 2>nul
if errorlevel 1 (
    powershell -NoProfile -Command "Compress-Archive -Path '%EXE_SAIDA%' -DestinationPath '%ZIP_SAIDA%' -Force"
)

if exist "%BUILD_ROOT%" rmdir /S /Q "%BUILD_ROOT%" 2>nul

echo.
echo ========================================
echo   PRONTO!
echo ========================================
echo.
echo Executavel unico:
echo   %EXE_SAIDA%
echo.
echo ZIP para envio (recomendado):
echo   %ZIP_SAIDA%
echo.
echo IMPORTANTE:
echo   - Agora e so UM arquivo .exe (sem pasta _internal)
echo   - Para enviar, prefira o ZIP (WhatsApp pode corromper .exe solto)
echo   - Ela extrai o ZIP e da duplo clique em ConversorParaJPEG.exe
echo.
pause

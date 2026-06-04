@echo off
setlocal enabledelayedexpansion
title Rupestre AI - Dashboard

echo.
echo ============================================================
echo   Rupestre AI - Real-time Graph Visualization
echo ============================================================
echo.

:: 1. Verificar Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js no esta instalado.
    echo         Descargalo desde: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js detectado

:: 2. Buscar npm.cmd (forma correcta en Windows)
set NPM_CMD=
for /f "usebackq tokens=*" %%p in (`where npm.cmd 2^>nul`) do (
    if "!NPM_CMD!"=="" set NPM_CMD=%%p
)
if "%NPM_CMD%"=="" (
    for /f "usebackq tokens=*" %%p in (`where npm 2^>nul`) do (
        if "!NPM_CMD!"=="" set NPM_CMD=%%p
    )
)
if "%NPM_CMD%"=="" (
    echo [ERROR] npm no encontrado. Reinstala Node.js.
    pause
    exit /b 1
)
echo [OK] npm encontrado

:: 3. Verificar Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado.
    echo         Descargalo desde: https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python detectado

:: 4. Instalar dependencias Node si faltan
if not exist "%~dp0server\node_modules" (
    echo.
    echo [INFO] Instalando dependencias Node.js...
    pushd "%~dp0server"
    call "%NPM_CMD%" install --prefer-offline --no-audit
    if errorlevel 1 (
        echo [ERROR] Fallo npm install.
        popd
        pause
        exit /b 1
    )
    popd
    echo [OK] Dependencias instaladas
) else (
    echo [OK] Dependencias ya instaladas
)

:: 5. Verificar requests Python
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando requests...
    python -m pip install requests -q
)
echo [OK] Dependencias Python listas

echo.
echo [INFO] Iniciando servidor...
echo.

:: 6. Limpiar puerto y lanzar servidor en ventana separada
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":5000 "') do taskkill /f /pid %%p >nul 2>&1
start "Rupestre-Server" /min cmd /c "cd /d "%~dp0server" && node realtime_server.js"

:: 7. Esperar que el servidor responda
echo [INFO] Esperando servidor en http://localhost:5000 ...
set TRIES=0
:wait_loop
timeout /t 2 /nobreak >nul
powershell -Command "try{(Invoke-WebRequest http://localhost:5000/api/graph -TimeoutSec 2 -UseBasicParsing).StatusCode}catch{1}" | findstr /r "^200$" >nul 2>&1
if not errorlevel 1 goto :server_ready
set /a TRIES=TRIES+1
if %TRIES% LSS 8 goto :wait_loop
echo [WARN] Servidor tardando, abriendo de todas formas...
goto :open_browser

:server_ready
echo [OK] Servidor listo

:open_browser
:: 8. Simulador desactivado a peticion del usuario
:: start "Rupestre-Simulator" /min cmd /c "cd /d "%~dp0server" && node event_simulator.js"

:: 9. Abrir navegador
timeout /t 1 /nobreak >nul
start "" http://localhost:5000
echo [OK] Navegador abierto

echo.
echo ============================================================
echo   Dashboard:  http://localhost:5000
echo   API:        http://localhost:5000/api/graph
echo.
echo   Presiona ENTER para detener el sistema.
echo ============================================================
echo.
pause >nul

:: 10. Limpiar al salir
echo.
echo [INFO] Deteniendo procesos...
taskkill /f /fi "WINDOWTITLE eq Rupestre-Server*" >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":5000 "') do taskkill /f /pid %%p >nul 2>&1
echo [OK] Sistema detenido.

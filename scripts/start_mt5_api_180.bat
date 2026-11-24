@echo off
title MT5 API - Multi Instance Manager

set "APPDIR=Z:\mt5_api"
set "VENV_PY=C:\mt5_api\venv\Scripts\python.exe"

echo ==========================================
echo       MT5 API - SERVER 192.168.1.180
echo ==========================================
echo.

if not exist "%VENV_PY%" (
    echo ERRORE: %VENV_PY% non trovato.
    pause
    exit /b 1
)

if not exist "%APPDIR%\" (
    echo ERRORE: cartella %APPDIR% non trovata.
    pause
    exit /b 1
)

cd /d "%APPDIR%"

echo [1/3] Arresto istanze precedenti...
"%VENV_PY%" stop_multi_instances.py

echo.
echo [2/3] Avvio istanze 8000-8003...
start "MT5_API 8000-8003" "%VENV_PY%" run_multi_instances.py

echo.
echo [3/3] Verifica...
timeout /t 5 /nobreak >nul

curl.exe -s -m 5 http://127.0.0.1:8000/openapi.json >nul
if errorlevel 1 (
    echo [!] Agente 8000 non risponde
) else (
    echo [OK] Agente 8000 risponde
)

curl.exe -s -m 5 http://127.0.0.1:8003/openapi.json >nul
if errorlevel 1 (
    echo [!] Agente 8003 non risponde
) else (
    echo [OK] Agente 8003 risponde
)

echo.
echo ==========================================
echo Verifica le API:
echo http://192.168.1.180:8000/docs
echo http://192.168.1.180:8001/docs
echo http://192.168.1.180:8002/docs
echo http://192.168.1.180:8003/docs
echo ==========================================
echo.
pause

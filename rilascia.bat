@echo off
rem ============================================================================
rem  RILASCIO MT5Pulse - procedura unica (vedi DEPLOY.md)
rem
rem  Doppio click (o da terminale):
rem    rilascia.bat              -> build + upload + restart + healthcheck
rem    rilascia.bat --rollback   -> ripristina l'ultimo backup
rem    rilascia.bat --setup      -> installazione una tantum sul server
rem    rilascia.bat --skip-build -> rilascio senza ricostruire il frontend
rem
rem  Il server (192.168.1.183) NON usa git ne' Docker:
rem  build locale -> backup -> upload SFTP -> systemd -> healthcheck -> rollback
rem ============================================================================
setlocal
cd /d "%~dp0"

set "PY=backend\venv\Scripts\python.exe"
if not exist "%PY%" (
    echo ERRORE: venv del backend non trovato in %PY%
    echo Crea il venv e installa le dipendenze ^(pip install -r backend\requirements.txt paramiko^).
    pause
    exit /b 1
)

"%PY%" -c "import paramiko" >nul 2>&1
if errorlevel 1 (
    echo ERRORE: paramiko mancante nel venv. Installalo con:
    echo   %PY% -m pip install paramiko
    pause
    exit /b 1
)

"%PY%" scripts\release.py %*
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo === OPERAZIONE COMPLETATA ===
) else (
    echo === OPERAZIONE FALLITA ^(exit %RC%^) ===
    echo Per tornare allo stato precedente: rilascia.bat --rollback
)
pause
exit /b %RC%

@echo off
REM Aggiorna/riavvia gli agenti MT5 sulla macchina Windows (192.168.1.180).
REM Da eseguire dopo aver fatto git pull nella cartella del progetto.
setlocal

set ROOT=%~dp0..
cd /d "%ROOT%\backend\mt5_api" || goto :error

echo [1/2] Fermo le istanze MT5_API sulle porte 8000-8003...
..\venv\Scripts\python.exe stop_multi_instances.py

echo [2/2] Avvio le istanze MT5_API sulle porte 8000-8003...
..\venv\Scripts\python.exe run_multi_instances.py
goto :eof

:error
echo [ERRORE] Cartella backend\mt5_api non trovata sotto %ROOT%
exit /b 1

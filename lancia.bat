@echo off
REM ============================================================
REM  MT5Pulse - lancio rapido (MySQL + Backend + Frontend + mt5_api)
REM  Avvia 4 finestre separate. Chiudile per fermare tutto.
REM  Dettagli e troubleshooting: AVVIO.md
REM ============================================================
setlocal

set MYSQL_BIN=C:\Users\vallo\AppData\Local\Programs\MySQL\mysql-9.4.0-winx64\bin
set MYSQL_INI=C:\Users\vallo\AppData\Local\Programs\MySQL\mysql-9.4.0-winx64\my.ini
set ROOT=C:\Users\vallo\mt5-pulse

echo [1/4] Avvio MySQL...
start "MT5Pulse - MySQL" cmd /k ""%MYSQL_BIN%\mysqld.exe" --defaults-file="%MYSQL_INI%""

REM attendo che MySQL accetti connessioni (max ~30s)
echo In attesa di MySQL...
set /a n=0
:wait_mysql
timeout /t 1 /nobreak >nul
"%MYSQL_BIN%\mysql.exe" -u trader -pvibe2025 -h localhost -e "SELECT 1;" >nul 2>&1
if %errorlevel%==0 goto mysql_up
set /a n+=1
if %n% LSS 30 goto wait_mysql
echo [ERRORE] MySQL non risponde dopo 30s. Vedi AVVIO.md.
pause
exit /b 1

:mysql_up
echo [2/4] Avvio Backend (porta 8080)...
start "MT5Pulse - Backend" cmd /k "cd /d "%ROOT%\backend" && venv\Scripts\python.exe main.py"

echo [3/4] Avvio Frontend (porta 4200)...
start "MT5Pulse - Frontend" cmd /k "cd /d "%ROOT%\frontend" && npm start"

echo [4/4] Avvio mt5_api - agente MT5 (porte 8000-8003)...
start "MT5Pulse - mt5_api" cmd /k "cd /d "%ROOT%\backend\mt5_api" && ..\venv\Scripts\python.exe run_multi_instances.py"

echo.
echo ============================================================
echo  Lancio avviato.
echo  Console web:  http://localhost:4200/
echo  Backend:      http://127.0.0.1:8080/
echo  mt5_api:      http://127.0.0.1:8000-8003
echo  (MT5 va inizializzato/loggato: vedi AVVIO.md, step 4)
echo  Chiudi le 4 finestre per fermare tutto.
echo ============================================================
endlocal

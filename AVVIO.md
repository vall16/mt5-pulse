# AVVIO MT5Pulse — guida rapida (Windows)

Tutto il necessario per lanciare la SaaS senza ricominciare le ricerche.
Ultimo lancio verificato: 2026-10-20.

## Servizi e porte

| Servizio | Porta | Note |
|---|---|---|
| MySQL 9.4 | 3306 | DB `trader_db`, utente `trader` |
| Backend (FastAPI) | 8080 | `backend/main.py` |
| Frontend (Angular) | 4200 | `frontend/` |
| mt5_api (agente MT5) | 8000-8003 | 4 istanze, `backend/mt5_api/run_multi_instances.py` |

Console web: **http://localhost:4200/**

## Prerequisiti già in posto (non rifarli)

- `backend/.env` esiste con tutte le config (MySQL, API 8080, CORS, MT5, OpenRouter). **Non ricrearlo.**
- `backend/venv` esiste con le dipendenze installate.
- `frontend/node_modules` installato (`npm install`).

## ⚠️ Gotcha principale: MySQL NON è un servizio Windows

MySQL 9.4 è installato ma **non registrato come servizio** (`net start MySQL` non funziona).
Bisogna avviare `mysqld` a mano con la config esistente.

- Install: `C:\Users\vallo\AppData\Local\Programs\MySQL\mysql-9.4.0-winx64`
- Config: `C:\Users\vallo\AppData\Local\Programs\MySQL\mysql-9.4.0-winx64\my.ini`
- Datadir: `C:\Users\vallo\AppData\Local\MySQL\data`

## Lancio manuale (4 terminali)

### 1) MySQL (in background)
```bat
"C:\Users\vallo\AppData\Local\Programs\MySQL\mysql-9.4.0-winx64\bin\mysqld.exe" --defaults-file="C:\Users\vallo\AppData\Local\Programs\MySQL\mysql-9.4.0-winx64\my.ini"
```
Verifica (~6 s dopo):
```bat
"C:\Users\vallo\AppData\Local\Programs\MySQL\mysql-9.4.0-winx64\bin\mysql.exe" -u trader -pvibe2025 -h localhost -e "SELECT COUNT(*) FROM trader_db.users;"
```
→ atteso: `2`

### 2) Backend (in background)
```bat
cd /d C:\Users\vallo\mt5-pulse\backend
venv\Scripts\python.exe main.py
```
Verifica:
```bat
curl http://127.0.0.1:8080/
```
→ atteso: `{"status":"running","message":"MT5 Manager API active"}`

### 3) Frontend (in background)
```bat
cd /d C:\Users\vallo\mt5-pulse\frontend
npm start
```
Verifica (~25 s dopo la compilazione):
```bat
curl -o nul -w "HTTP %{http_code}" http://localhost:4200/
```
→ atteso: `HTTP 200`

### 4) mt5_api — agente MT5 (in background)
⚠️ Va lanciato da **`backend/mt5_api/`**, NON da `backend/`.
Il `run_multi_instances.py` in `backend/` punta a `main:app` = il **Manager API** (sbagliato);
quello in `backend/mt5_api/` punta a `main:app` = l'agente MT5 (giusto).

```bat
cd /d C:\Users\vallo\mt5-pulse\backend\mt5_api
..\venv\Scripts\python.exe run_multi_instances.py
```
Avvia 4 istanze su **8000-8003**. Verifica:
```bat
curl http://127.0.0.1:8000/health
```
→ atteso subito dopo: `{"status":"error","message":"MT5 non inizializzato"}` (normale, vedi sotto).

#### Inizializzare e loggare MT5 (per ogni istanza)
Il terminale MT5 va inizializzato e loggato, altrimenti le istanze restano "non inizializzate".
Dati dal `backend/.env`: `MT5_PATH`, `ACCOUNT`, `PASSWORD`, `SERVER`.

```bat
curl -X POST http://127.0.0.1:8000/init-mt5 -H "Content-Type: application/json" -d "{\"path\":\"C:\\Program Files\\MetaTrader 5\\terminal64.exe\"}"
curl -X POST http://127.0.0.1:8000/login -H "Content-Type: application/json" -d "{\"login\":959911,\"password\":\"Qpnldan1@1\",\"server\":\"VTMarkets-Demo\"}"
```
Verifica finale:
```bat
curl http://127.0.0.1:8000/health
```
→ atteso: `{"status":"ok","mt5_version":"..."}`

## Lancio in un click

Usa **`lancia.bat`** (stessa cartella): avvia MySQL, backend, frontend e mt5_api in 4 finestre separate.

## Se qualcosa non parte

- **MySQL: "Can't connect ... 3306 (10061)"** → `mysqld` non è partito. Controlla che il datadir in `my.ini` esista e che la porta 3306 non sia già occupata.
- **Backend: porta 8080 occupata** → un vecchio processo è ancora lì; chiudilo e rilancia.
- **Backend: errore DB** → verifica `MYSQL_*` in `backend/.env` e che MySQL sia attivo.
- **Frontend: errore CORS / chiamate fallite** → il FE punta a `http://127.0.0.1:8080` (vedi `frontend/src/environments/environment.ts`); assicurati che il backend sia su 8080.
- **mt5_api: porta 8000 occupata** → un altro processo la usa (es. CvScreener). Trovalo con `netstat -ano | findstr :8000`, chiudilo (`taskkill /PID <pid> /F`) e rilancia.
- **mt5_api: `/health` → "MT5 non inizializzato"** → normale dopo l'avvio; esegui `/init-mt5` poi `/login` (vedi step 4).
- **mt5_api: `/health` → 404 / HTML di un altro sito** → sulla porta c'è un'altra app, non l'agente MT5.
- **mt5_api: login fallito / timeout** → verifica `ACCOUNT`/`PASSWORD`/`SERVER` in `backend/.env` e che il terminale MT5 sia aperto e raggiungibile.

## Note

- Per fermare tutto: chiudere le 4 finestre (o i processi di background). Per MySQL: `mysqladmin -u trader -pvibe2025 shutdown`.
- `trading_api/` (proxy) non è usato dal backend nel codice attuale: il backend punta direttamente agli agenti `mt5_api`.
- Il backend risolve l'URL degli agenti dalla tabella `servers` (DB): per il locale deve puntare a `127.0.0.1:8000` (o la porta giusta).

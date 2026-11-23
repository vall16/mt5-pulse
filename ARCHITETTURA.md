# Architettura MT5 Pulse

## Struttura del progetto

Repo con 3 blocchi logici: `frontend/` (Angular 20), `backend/` (FastAPI "Manager API" + MySQL) e `backend/mt5_api/` (agente MT5).

```
Browser Angular :4200
   │  environment.apiUrl → http://127.0.0.1:8080
   ▼
BACKEND (backend/main.py, porta 8080)  ── MySQL trader_db :3306 (locale) / :3307 (Docker)
   │ router: /db /mt5 /trade /adaptive /supervisor /signal-research
   │ URL dei terminali = servers.ip:porta lette dal DB (main.py:68-74, db.py)
   │ In Docker: MT5_API_URL = host.docker.internal:8000
   ▼
MT5_API (backend/mt5_api/main.py, su ogni server Windows con MT5, 8000-8003)
   → lib MetaTrader5 → terminal64.exe → broker
   (fuori Docker — Windows-only)
```

## Avvio dei servizi

### Con Docker Compose (consigliato)

```bash
docker compose up -d --build   # MySQL + backend + frontend
```
+ mt5_api a parte (Windows-only):
```bash
cd backend/mt5_api && python run_multi_instances.py
```

| Servizio | Porta host | Note |
|---|---|---|
| MySQL (container) | 3307 | auto-import dump al primo avvio |
| Backend (container) | 8080 | raggiunge mt5_api via `host.docker.internal:8000` |
| Frontend (container) | 4200 | nginx, build Angular in Dockerfile multi-stage |
| mt5_api (host) | 8000-8003 | fuori Docker, Windows-only |

### Manuale (senza Docker)

| Servizio | Comando | Porta |
|---|---|---|
| MySQL | `mysqld --no-defaults --datadir=... --port=3306` | 3306 |
| Backend | `python main.py` | 8080 |
| Frontend | `npm start` (`ng serve`) | 4200 |
| mt5_api | `run_multi_instances.py` | 8000-8003, solo Windows |

Lo startup del backend esegue `run_migrations()` (`main.py:44`); CORS ammette `:4200`.

## Relazioni tra componenti

### FE → BE

Unico punto di contatto. `trader.service.ts` e `auth.service.ts` usano `environment.apiUrl` (`src/environments/environment.ts:3`) con i prefissi dei router:

- `/db/*` — login, servers, traders, copy_orders, backtest, history, analyze
- `/mt5/check-server`, `/mt5/start_server`
- `/trade/start_polling`, `/trade/stop_polling`
- `/adaptive/*` — start/stop/status/stats
- `/supervisor/*` — start/stop/run-now/status/config/apply
- `/signal-research/*` — run, auto-discover, agent-discover, export-pdf

Eccezione: `user-dashboard.component.ts:786` costruisce `http://{slave.ip}:{porta}` e chiama **diretto** l'agente su `/symbols/active` (`trader.service.ts:231`), aggirando il backend.

### BE → mt5_api

Il backend non ha URL fissi — risolve sempre `f"http://{ip}:{port}"` dalla tabella `servers` (`db.py:1686-1694`, `mt5_routes.py:17,54-57`, `signal_research_routes.py:42-55`).

Endpoint chiamati: `/health`, `/init-mt5`, `/start_mt5`, `/login`, `/order`, `/close_order`, `/close_order_by_symbol`, `/positions`, `/history`, `/get_rates`, `/get_rates_range`, `/symbol_tick`, `/symbol_info`.

È il percorso reale in uso: `trading_signals_multi2.py` (polling segnali + replicazione master→slave) e `strategy_supervisor.py` parlano direttamente con lo slave. Non esiste un proxy intermedio: il backend raggiunge gli agenti `mt5_api` via `servers.ip:porta`.

### mt5_api

L'unico componente che tocca MetaTrader (Windows-only, lib `MetaTrader5`). Un'istanza per terminale. Espone dati (rates, tick, symbol, history, positions) e azioni di trading (order, close).

In pratica è il "braccio" distribuito, mentre il backend è il "cervello" centrale (DB, strategie, AI) e il FE la console.

## Ruoli sintetici

| Componente | Ruolo |
|---|---|
| `frontend/` | Console Angular: login, gestione traders/servers, backtest, signal research, supervisor |
| `backend/` | Cervello centrale: MySQL, strategie, replicazione master→slave, AI (OpenRouter) |
| `backend/mt5_api/` | Agente locale su ogni server Windows con MT5: unico che esegue ordini |

## Note e incoerenze note

- `environment.prod.ts` non è mai applicato (manca `fileReplacements` in `angular.json`), quindi anche in build production il FE punta a `127.0.0.1:8080`.
- `@supabase/supabase-js` è in `frontend/package.json` ma inutilizzato nel codice `src/`; le migration SQL in `frontend/supabase/` restano orfane. L'autenticazione passa da `POST /db/login` (MySQL).
- La cartella `backend/routers/` contiene file vuoti (0 byte), inutilizzata.
- Compose unificato a livello root (`docker-compose.yaml`): MySQL, backend, frontend. `backend/mt5_api` non è in Docker (Windows-only).

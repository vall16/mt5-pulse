# Architettura MT5 Pulse

## Struttura del progetto

Repo con 4 blocchi: `frontend/` (Angular 20), `backend/` (FastAPI "Manager API" + MySQL), `backend/mt5_api/` (agente MT5) e `trading_api/` (proxy HTTP).

```
Browser Angular :4200
   │  environment.apiUrl → http://127.0.0.1:8080
   ▼
BACKEND (backend/main.py, porta 8080)  ── MySQL trader_db :3306
   │ router: /db /mt5 /trade /adaptive /supervisor /signal-research
   │ URL dei terminali = servers.ip:porta lette dal DB (main.py:68-74, db.py)
   ▼
TRADING_API (opzionale, 4 istanze 8000-8003)  → proxy puro, riscrive su REMOTE_MT5_API_URL
   ▼
MT5_API (backend/mt5_api/main.py, su ogni server Windows con MT5, 8000-8003)
   → lib MetaTrader5 → terminal64.exe → broker
```

## Avvio dei servizi

| Servizio | Comando | Porta |
|---|---|---|
| Backend | `python main.py` (o Docker `uvicorn main:app`) | 8080 (`.env` API_HOST/API_PORT) |
| Frontend | `npm start` (`ng serve`, nessun proxy) | 4200 |
| mt5_api | `python main.py <MT5_PATH> <host:porta>` o `run_multi_instances.py` | 8000-8003, solo Windows |
| trading_api | `docker compose up -d` → `run_multi_instances.py` | 8000-8003 |

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

È il percorso reale in uso: `trading_signals_multi2.py` (polling segnali + replicazione master→slave) e `strategy_supervisor.py` parlano direttamente con lo slave.

### BE → trading_api

**Nessuna chiamata diretta** (grep zero riferimenti nel backend).

È un livello di proxy stateless (`trading_api/main.py:40-62`) pensato per stare su una macchina Linux/Ubuntu e instradare verso il server Windows (`REMOTE_MT5_API_URL=http://192.168.1.180:8000`), esponendo solo un sottoinsieme di route:

- `/health`, `/login`, `/positions`, `/symbols`, `/symbols/active`
- `/order`, `/close_order/{ticket}`, `/close_order_by_symbol`
- `/terminal_info`, `/get_rates_range`

Nel codice attuale il backend lo salta e punta agli agenti mt5_api.

### mt5_api

L'unico componente che tocca MetaTrader (Windows-only, lib `MetaTrader5`). Un'istanza per terminale. Espone dati (rates, tick, symbol, history, positions) e azioni di trading (order, close).

In pratica è il "braccio" distribuito, mentre il backend è il "cervello" centrale (DB, strategie, AI) e il FE la console.

## Ruoli sintetici

| Componente | Ruolo |
|---|---|
| `frontend/` | Console Angular: login, gestione traders/servers, backtest, signal research, supervisor |
| `backend/` | Cervello centrale: MySQL, strategie, replicazione master→slave, AI (OpenRouter) |
| `trading_api/` | Proxy stateless verso mt5_api (ponte Linux → Windows) |
| `backend/mt5_api/` | Agente locale su ogni server Windows con MT5: unico che esegue ordini |

## Note e incoerenze note

- `trading_api` e `backend/mt5_api` hanno la stessa porta default 8080; `EXPOSE` nei Dockerfile incoerenti (8080 vs 8000-8003).
- `environment.prod.ts` non è mai applicato (manca `fileReplacements` in `angular.json`), quindi anche in build production il FE punta a `127.0.0.1:8080`.
- `ai_analysis.py:10` usa `MT5_API_URL` default `http://127.0.0.1:8081`, incoerente con le porte 8000-8003.
- `@supabase/supabase-js` è in `frontend/package.json` ma inutilizzato nel codice `src/`; le migration SQL in `frontend/supabase/` restano orfane. L'autenticazione passa da `POST /db/login` (MySQL).
- La cartella `backend/routers/` contiene file vuoti (0 byte), inutilizzata.
- Unico compose del repo: `trading_api/docker-compose.yaml` (mancano compose per backend e mt5_api, e manca `.env` in `trading_api/`).

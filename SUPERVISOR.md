# AI Strategy Supervisor

Agente AI che gestisce **N strategie** del progetto MT5Pulse: valuta periodicamente
ogni trader/strategia configurato e produce una **raccomandazione** (`ACTIVE` / `PAUSE` / `WATCH`)
con confidenza, motivo e flag di sicurezza.

> Il supervisore **non esegue nulla in autonomia**: propone solo raccomandazioni.
> L'utente applica manualmente l'azione dal pannello (o via API `/supervisor/apply`).

---

## 1. Ruolo e modalità

- **Ruolo**: attiva / mette in pausa le strategie dei trader.
- **Metodo**: LLM (OpenRouter) + regole di sicurezza deterministiche.
- **Esecuzione**: solo raccomandazioni, nessuna azione automatica.
- **Frequenza**: valutazione periodica ogni 5-15 minuti (default 600s), più `Run Now` manuale.

## 2. Architettura

### Backend (FastAPI)
| File | Ruolo |
|------|-------|
| `backend/strategy_supervisor.py` | Logica dell'agente: `StrategySupervisor`, singoletto `supervisor`, safety check, chiamata LLM, parse risposta. |
| `backend/supervisor_routes.py` | API REST `/supervisor/*`. |
| `backend/main.py` | Registrazione del router `/supervisor`. |

### Frontend (Angular)
| File | Ruolo |
|------|-------|
| `frontend/src/app/services/trader.service.ts` | 6 metodi verso le API supervisor. |
| `frontend/src/app/components/user-dashboard/user-dashboard.component.{ts,html,css}` | Pannello "AI Strategy Supervisor" sopra la griglia traders. |

## 3. Flusso di valutazione (ogni ciclo)

1. `_collect_states()`: legge da DB i trader attivi e raccoglie per ognuno:
   - strategia e simbolo (`selected_signal`, `selected_symbol`);
   - stato polling (`RUNNING`/`STOPPED` via `_is_running`);
   - **market check** (`_check_market`): regime di mercato (`TREND`/`RANGE`/`CHAOS`...), ATR M5, mercato aperto, sessione attiva, notte, notizie ad alto impatto;
   - **performance** (win rate, net profit ultimi 30 trade) se `fetch_positions=True`.
2. `_safety_check(state, cfg)`: regole deterministiche → azione forzata (di solito `PAUSE`).
3. Prompt LLM con stato aggregato → risposta JSON `{reasoning, decisions:{<trader_id>:{action, confidence, reason}}}`.
4. `_merge_recommendations()`: fonde decisioni LLM + safety (la safety **sovrascrive** l'LLM).
5. Salva in `self.recommendations`, `self.reasoning`, `self.last_run` → leggibili da `/supervisor/status`.

## 3b. Come funziona in pratica

1. Carica i trader attivi dal DB (`_load_traders`).
2. Per ognuno raccoglie **snapshot di mercato** dal server MT5 slave: ATR M5,
   regime M15 (TREND/RANGE/CHAOS), sessione corrente, mercato aperto, fascia notturna.
3. Calcola la **performance** reale: win rate e P&L netto degli ultimi 30 trade
   chiusi (`_performance`, su `slave_orders`).
4. Conta le **posizioni aperte** sul slave.
5. Applica le **regole di sicurezza** (news, perdite consecutive, win rate basso,
   drawdown → forza `PAUSE`).
6. Invia tutto all'**LLM** (OpenRouter) che risponde con
   `{reasoning, decisions:{<trader_id>:{action, confidence, reason}}}`.
7. **Fonde** le due fonti (la safety ha priorità) → raccomandazioni mostrate nel pannello.

## 3c. Cosa gestisce (strategie e monete)

Il supervisor **non ha una lista fissa**: gestisce dinamicamente tutti i trader
**attivi nel DB** (`is_active=1`) che hanno `selected_signal` e `selected_symbol`
configurati. Ogni trader = una coppia **strategia + moneta**.

> Query usata (`_load_traders`, `strategy_supervisor.py`):
> ```sql
> SELECT ... FROM traders t
> LEFT JOIN servers ss ON ss.id = t.slave_server_id
> WHERE t.is_active = 1 AND t.selected_signal IS NOT NULL
>   AND t.selected_signal != '' AND t.selected_symbol IS NOT NULL
>   AND t.selected_symbol != ''
> ORDER BY t.id
> ```

**Snapshot attuale (dal DB):**

| Trader | Strategia | Moneta |
|--------|-----------|--------|
| Trader_Alphaa (id 1) | `SUPER_USDJPY` | USDJPY |
| Trader_Test3 (id 10) | `SUPER` | XAUUSD |
| Trader_Test4 (id 11) | `GBPUSD` | GBPUSD |

Quindi oggi il supervisor valuta **XAUUSD**, **USDJPY** e **GBPUSD**.
Aggiungendo/rimuovendo trader o cambiando `selected_signal`/`selected_symbol`
il supervisor li gestisce automaticamente al ciclo successivo.
Per limitare i trader valutati si può usare `enabled_trader_ids` nella config.

## 4. Regole di sicurezza (safety check)

Forzano `PAUSE` quando:
- **Mercato chiuso** (`is_market_open` false) per il simbolo.
- **Fascia notturna** / sessione non valida (`sessions_filter` del trader).
- **Regime NEWS** ad alto impatto nelle vicinanze.
- **≥ `max_consecutive_losses`** (default 6) perdite consecutive.
- **Win rate < `min_win_rate_for_kill`** (default 25%) con almeno `min_trades_for_kill` (default 10) trade.
- **Drawdown < `drawdown_threshold`** (default −300$).

Se scatta una regola, `recommended_action` diventa `PAUSE`, `safety_override=True`
e il motivo riporta la regola.

## 5. Configurazione di default

```python
DEFAULT_CONFIG = {
    "interval_seconds": 600,       # 5-15 min
    "model": "openrouter/free",
    "enabled_trader_ids": [],      # vuoto = tutti i trader attivi
    "lockdown_on_news": True,
    "max_consecutive_losses": 6,
    "min_trades_for_kill": 10,
    "min_win_rate_for_kill": 25.0,
    "drawdown_threshold": -300.0,
    "fetch_positions": True,       # usa la performance reale nel prompt
    "max_history": 20,
}
```

## 6. API

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | `/supervisor/start` | Avvia il ciclo periodico (body opzionale: config parziale). |
| POST | `/supervisor/stop` | Ferma il ciclo periodico. |
| POST | `/supervisor/run-now` | Esegue subito una valutazione. |
| GET  | `/supervisor/status` | Stato corrente + raccomandazioni. |
| POST | `/supervisor/config` | Aggiorna la config. |
| POST | `/supervisor/apply` | Applica manualmente `ACTIVE`/`PAUSE` a un trader (avvia/ferma il polling). |

`apply` body: `{"trader_id": int, "action": "ACTIVE"|"PAUSE"}`.
Per `ACTIVE` il trader deve avere `selected_signal` e `selected_symbol` configurati,
altrimenti risponde `ko`. Il trader viene ricostruito dal DB con `direction_filter="both"`.

## 7. Struttura raccomandazione (in `/supervisor/status`)

```json
{
  "running": true,
  "started_at": "...",
  "last_run": "...",
  "last_error": null,
  "llm_used": false,
  "reasoning": "sintesi AI (se LLM disponibile)",
  "interval_seconds": 600,
  "config": { "...": "..." },
  "recommendations": [
    {
      "trader_id": 10,
      "name": "Trader_Test3",
      "strategy": "SUPER",
      "symbol": "XAUUSD",
      "current_status": "STOPPED",
      "open_positions": 0,
      "recommended_action": "WATCH",
      "confidence": 0.5,
      "reason": "...",
      "safety_override": false,
      "safety_reason": "",
      "market": { "ok": true, "regime": "...", "atr_m5": 12.3, "..." : "..." },
      "performance": { "win_rate": 55.0, "net_profit_30": 120.0 }
    }
  ],
  "history": []
}
```

## 8. Pannello frontend

Nel componente `user-dashboard` (sopra la griglia "My Traders"):
- **Badge Running/Stopped** + pulsanti **Start / Stop / Run Now**.
- **Config**: intervallo (sec) e modello LLM, pulsante "Salva config".
- **Meta**: ultima analisi, LLM usato vs solo regole di sicurezza, eventuale errore.
- **Ragionamento AI**: sintesi testuale dell'ultimo ciclo.
- **Tabella raccomandazioni**: trader, strategia, simbolo, stato, regime/ATR, win rate / P&L,
  badge `ACTIVE`/`PAUSE`/`WATCH`, confidenza, motivo, flag di sicurezza.
- **Azioni**: "Attiva" (se fermo) / "Pausa" (se attivo) → chiama `/supervisor/apply`.
- Il pannello si **aggiorna da solo ogni 30s** quando il supervisore è in esecuzione.

## 9. Note operative

- **Senza `OPENROUTER_API_KEY`** (o su errore LLM) il sistema usa **solo le regole di sicurezza**:
  azione di default `WATCH` quando nessuna regola scatta, `llm_used=false`.
- Le regole di safety hanno **priorità sull'LLM** (`safety_override=True`).
- L'LLM richiesto deve rispondere in JSON; il parser accetta anche JSON dentro blocchi ```` ```json ... ``` ````.
- **Riavvii**: dopo modifiche ai file backend serve riavviare il processo **uvicorn**;
  per il frontend, se servito da `ng serve` si ricarica da solo, altrimenti serve una nuova build
  (il pannello usa il bundle aggiornato).

# Migliorie possibili — mt5-pulse

Elenco di miglioramenti identificati il 2026-11-26, in ordine di priorità.

> **Revisione del 2026-11-26:** il documento è stato rivisto confrontando ogni punto con il codice sorgente. L’analisi originale era buona (circa l’80% accurata); per ogni voce è stato aggiunto un blocco **Verifica** con correzioni e integrazioni. Il riordino finale delle priorità sta in fondo al file. **Non è stato modificato alcun codice, solo questo documento.**

**Giudizio complessivo:** la priorità assoluta è la **#4 (auth su `mt5_api`)**, da eseguire come blocco unico insieme alla **#3 (proxy slave-symbols)** e alla parte dei retry dei GET della **#2**. È l’unico punto il cui impatto è denaro reale / controllo delle macchine, mentre gli altri sono fastidi operativi. Il loopback (#1) e i log (#5) sono pulizie a basso rischio, da fare dopo.

---

## 1. `send_order` si chiama via HTTP su sé stesso

**File:** `backend/trading_signals_multi2.py` (~riga 175)

Il thread polling invia l'ordine con:
```python
requests.post(f"{BASE_URL}/db/traders/{trader_id}/open_order_on_slave", json=payload, timeout=75)
```
dove `BASE_URL` è `http://localhost:8080` — il backend stesso. Il round-trip loopback è inutile: thread e endpoint girano nello stesso processo.

**Problemi:**
- Overhead TCP + JSON serialize/deserialize per ogni ordine
- Punto di fallimento extra (socket exhaustion, backlog uvicorn)
- Difficile da debuggare (ConnectionError su loopback confonde la diagnosi)
- Thread pool contention sotto carico (5 trader scattano insieme)

**Fix:** importare la funzione da `db.py` e chiamarla in-process:
```python
from db import open_order_on_slave
result = open_order_on_slave(trader_id, payload)
```

**Urgenza:** bassa (loopback affidabile, volume ordini basso), ma riduce un failure mode.

**Verifica / correzioni:**
- **Confermato.** `BASE_URL` è costruito alle righe 30-33 da `API_HOST`/`API_PORT`, e usato solo alle righe 194 e 211.
- **Il problema riguarda anche `close_slave_position()`** (righe 202-216), che fa lo stesso loopback su `/db/traders/{id}/close_order_on_slave`. Il fix va applicato a entrambi.
- Lo snippet originale non è corretto: `db.py:1432` dichiara `open_order_on_slave(payload: OrderPayload)`, cioè si aspetta un modello Pydantic, non `(trader_id, payload)`. La chiamata giusta è:
  ```python
  from db import open_order_on_slave, close_order_on_slave, OrderPayload, CloseOrderPayload

  result = open_order_on_slave(OrderPayload(**payload))
  result = close_order_on_slave(CloseOrderPayload(**payload))
  ```
  e il log va adattato perché la risposta è un dict, non più `resp.text`.
- **Cosa non cambia:** `open_order_lock` (`db.py:1428`) resta globale, quindi la serializzazione degli ordini è preservata.
- Dopo il fix diventano inutili, nel modulo, `import os`, `load_dotenv()` e le righe 30-33 (`HOST`, `PORT`, `BASE_URL`): verificato che non sono usati altrove.
- **Perché il thread pool soffre:** `open_order_on_slave` è una funzione `def` sincrona, quindi FastAPI la esegue in un worker del threadpool (AnyIO, 40 worker di default). Il thread del Timer resta bloccato ad attendere la risposta HTTP: due thread per un solo ordine. Se 5 trader scattano insieme mentre altri endpoint sincroni fanno I/O bloccante verso gli slave, il pool si satura e la richiesta loopback mette in coda dentro il processo che l’ha generata (backpressure autoinflitta).
- Il timeout di 75 s si propaga al Timer: il ciclo successivo viene schedulato solo a fine `polling_loop_timer()` (righe 2097-2101), quindi un blocco interno ritarda anche il segnale dopo.

---

## 2. Nessuna retry su chiamate slave

**File:** `backend/trading_signals_multi2.py` — `get_data()`, `send_order()`, `close_slave_position()`

Tutte le `requests.get/post` verso mt5_api falliscono al primo errore. Un timeout di 50ms fa perdere il segnale o l'ordine.

**Fix:** retry con backoff (2-3 tentativi, 0.5s / 1s / 2s) su:
- `get_data()` — se fallisce, il segnale viene perso
- `send_order()` — se fallisce, l'ordine non parte
- `close_slave_position()` — se fallisce, la posizione resta aperta

Libreria: `urllib3.util.retry` o un semplice loop con `time.sleep`.

**Urgenza:** media — riduce falsi "niente segnale" da rete instabile.

**Verifica / correzioni:**
- **Il timeout citato è sbagliato:** non è 50 ms. Nel codice: `timeout=30` in `get_data()` (riga 42), `timeout=10` per `symbol_info`/`symbol_tick` (righe 143-144), `timeout=15` in `fetch_closed_deals_profit()` (riga 106), `timeout=5` per `/positions` (riga 400).
- **Non fare retry cieco sul POST ordine.** Se il primo tentativo va in timeout *dopo* che l’ordine è stato eseguito, il retry lo duplica. `open_order_lock` protegge la concorrenza, non i retry sequenziali. Serve una chiave di idempotenza legata al segnale (per esempio un `signal_id`), oppure un controllo della posizione esistente prima del retry.
- I retry sono invece sicuri e utili sui **GET** (`get_rates`, `symbol_info`, `symbol_tick`, `positions`, `history`).
- `get_data()` già nasconde l’eccezione e ritorna `None`: il retry va messo a monte, non dentro il `try` che restituisce `None`.
- **Implementazione consigliata:** un unico client wrapper lato backend (`mt5_client.py`) con `requests.Session` + `HTTPAdapter` con `Retry` sui soli GET, token (vedi #4) e timeout centralizzati. Le chiamate sono sparse in almeno 6 file (~18 punti): `db.py`, `trading_signals_multi2.py`, `ai_analysis.py`, `strategy_supervisor.py`, `mt5_routes.py`, `logger.py`.

---

## 3. Frontend chiama lo slave direttamente (CORS + sicurezza)

**File:** `frontend/src/app/services/trader.service.ts:231` (`getSlaveSymbols`), `user-dashboard.component.ts:786`

Il FE costruisce `http://{slave.ip}:{porta}` e chiama l'agente mt5_api **aggirando il backend**.

**Problemi:**
- CORS aperto su ogni mt5_api (hardcoded in `mt5_api/main.py`)
- IP del server esposto al browser
- Se il backend è dietro reverse proxy, il FE non raggiunge lo slave
- Incoerente: tutte le altre chiamate passano dal backend

**Fix:** endpoint proxy nel backend:
```
GET /db/traders/{id}/slave-symbols
```
che fa la chiamata server-to-server verso lo slave e restituisce i simboli.

**Urgenza:** media — sicurezza + pulizia architetturale.

**Verifica / correzioni:**
- **Confermato il bypass:** `user-dashboard.component.ts:864` costruisce `slaveApiUrl` da `slaveServer.ip`/`.port` e lo passa a `getSlaveSymbols()` (riga 867).
- **"CORS aperto" è impreciso:** `mt5_api/main.py:23-30` ha una whitelist di 3 origin (`localhost:4200`, `127.0.0.1:4200`, `192.168.1.183:4200`), non `*`. Rimane il fatto che l’IP privato è hardcoded e che il backend, se dietro proxy, non è più allineato.
- **Il problema vero non è CORS:** CORS vale solo per i browser; non ferma `curl`, script Python o altri processi in rete. La protezione effettiva è la #4.
- **Questa miglioria diventa obbligatoria dopo la #4:** con l’auth attiva il browser non potrà più chiamare lo slave con il token, quindi il proxy serve per non rompere la UI.

---

## 4. Nessuna autenticazione su mt5_api

**File:** `backend/mt5_api/main.py`

L'agente MT5 (che esegue ordini reali) non ha alcuna auth. Chiunque sulla rete può:
- `POST /order` → apre una posizione
- `POST /close_order` → chiude una posizione
- `POST /init-mt5` → reinizializza il terminale

**Fix:** token statico in header (es. `X-Agent-Token`), letto da `.env` su ogni istanza. Il backend lo passa nelle chiamate. 401 se mancante/errato.

**Urgenza:** alta se la rete non è isolata; bassa se solo loopback/VPN.

**Verifica / correzioni:**
- **Confermato, ed è la priorità assoluta del documento.** È l’unico punto con impatto su denaro reale e controllo delle macchine. Non esiste alcun meccanismo di auth né lato agente né lato backend (gli unici `token` nel codice sono le chiavi OpenRouter per l’AI).
- **Endpoint mancanti nell’analisi originale:**
  - `POST /start_mt5` (`mt5_api/main.py:78-94`) fa `subprocess.Popen([path])` con un path arbitrario ricevuto nel body → esecuzione di codice remota, non solo ordine falso.
  - `POST /login` accetta login/password/server del conto MT5.
  - `POST /close_order_by_symbol` (`main.py:411`) è quello usato davvero da `db.py:1630`.
- **Il fix va implementato come middleware** in `mt5_api/main.py`, così copre tutti gli endpoint in un colpo solo, inclusi quelli nuovi. Il token viaggia in chiaro su HTTP: se la rete non è fidata, affiancare firewall / allowlist IP o VPN, non considerare il token statico come sufficiente.
- **Sforzo sottostimato:** circa 18 call site da aggiornare (`db.py`, `trading_signals_multi2.py`, `ai_analysis.py`, `strategy_supervisor.py`, `mt5_routes.py`, `logger.py`). Centralizzarli in `mt5_client.py` (si veda #2) evita di doverli ritoccare due volte.

---

## 5. Log senza rotazione

**File:** `backend/main.py` (logging config), `backend/logger.py`

`fxscript.log` cresce all'infinito. Dopo mesi = GB di log.

**Fix:**
```python
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler("./fxscript.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
```

**Urgenza:** bassa (dipende da quanto gira), ma zero costo.

**Verifica / correzioni:**
- **Il bersaglio è sbagliato.** `fxscript.log` è configurato da `logging.basicConfig` (`main.py:37-43`) e contiene soprattutto startup ed errori: volume basso.
- **Il file che cresce davvero è `server_log.txt`**, scritto da `logger.py:91` con `open(file, "a", encoding="utf-8")` a ogni riga, quindi senza alcun limite. È il file che riceve tutti i log di trading.
- La rotazione va messa lì, non su `fxscript.log`. Attenzione che più processi/thread scrivono lo stesso file: `RotatingFileHandler` standard non è multiprocess-safe; meglio `concurrent-log-handler` o una rotazione gestita dentro `logger.log()`.
- La lista in memoria `logs` è **già** limitata a `MAX_LOGS = 2000` (`logger.py:22`, troncamento alle righe 94-96): non c’è leak di memoria, solo crescita del file.

---

## 6. `is_market_open` troppo naive

**File:** `backend/trading_signals_multi2.py` (~riga 68)

Non considera:
- Festivi (Xmas, Capodanno, Good Friday, bank holidays)
- Orari diversi per azioni (MSFT, NVDA) vs forex (XAUUSD, GBPUSD)
- "Sunday 23:00" è approssimativo (varia per broker, 21:00-23:00 UTC)

**Fix:** per ora non critico. Se si aggiungono simboli azionari, serve un check per-simbolo (o almeno per-categoria: forex vs stock).

**Urgenza:** bassa (solo se si espande a nuovi asset class).

**Verifica / correzioni:**
- **Confermato.** `is_market_open(symbol: str)` (righe 62-75) **ignora completamente l’argomento `symbol`**: oggi è solo un controllo sul giorno della settimana in ora di Roma.
- Chiamato in `trading_signals_multi2.py:324` e `strategy_supervisor.py:169`. Un eventuale check per-simbolo va quindi applicato a entrambi i call site.
- Resta una miglioria condizionale: solo se si aggiungono nuove asset class o simboli con orari diversi.

---

## 7. Frontend: `availableSignals` hardcoded

**File:** `frontend/src/app/components/user-dashboard/user-dashboard.component.ts` (~riga 70)

La lista dei segnali è duplicata rispetto al backend `STRATEGIES` dict. Ogni nuova strategia richiede un edit manuale in due file (backend + frontend).

**Fix:** endpoint `GET /trade/strategies` che restituisce:
```json
[{"name": "SUPER", "label": "XAUUSD Super", "timeframe": "M5", "description": "..."}]
```
Il FE lo carica al ngOnInit e popola il dropdown dinamicamente.

**Urgenza:** media — elimina il sync manuale (già causato un bug con SUPER_DM).

**Verifica / correzioni:**
- **Confermato, e il drift è già presente:** `availableSignals` (`user-dashboard.component.ts:68-83`) ha 14 voci; `STRATEGIES` (`trading_signals_multi2.py:2053-2069`) ne ha 15. Manca **`EURUSD_NOHOLD`** lato frontend.
- `STRATEGIES` contiene solo le istanze delle strategie: non ha label, timeframe o descrizione. L’endpoint dovrà quindi leggere un piccolo dizionario di metadata (nome → label/timeframe), che diventerà l’unica fonte di verità insieme alle chiavi di `STRATEGIES`.
- Nota minore collegata: `run_signal_logic()` usa `chosen = trader.selected_signal or "BASE"` (riga 2082), ma `"BASE"` non è una chiave di `STRATEGIES`: il codice scende silenziosamente a `DEFAULT_STRATEGY`.

---

## 8. `getSlaveSymbols` — debug log in produzione

**File:** `frontend/src/app/services/trader.service.ts:231-260`

~15 `console.log/error` con dettagli interni (ProgressEvent, JSON.stringify, ecc.) lasciati nel codice di produzione.

**Fix:** rimuovere o mettere dietro `environment.debug`.

**Urgenza:** bassa — rumore in console, zero impatto funzionale.

**Verifica / correzioni:**
- **Confermato.** In `getSlaveSymbols()` ci sono ~15 `console.log/error` (righe 251-284).
- Il problema è più esteso: `user-dashboard.component.ts` ne contiene circa 40, incluso `console.log('Payload:', payload)` alla riga 358. Limitare la pulizia al solo servizio lascia gran parte del rumore.
- Resta una miglioria estetica: nessun impatto funzionale.

---

## Riordino consigliato (revisione 2026-11-26)

| Fase | Miglioria | Urgenza | Sforzo | Perché in questa posizione |
|---|---|---|---|---|
| 1 | **#4 auth su mt5_api** + **#3 proxy slave-symbols** + retry GET della **#2** | **alta** | medio | Unico rischio con impatto su denaro/RCE. Con l’auth il FE non può più chiamare lo slave: il proxy diventa obbligatorio. Il client wrapper centralizza token + retry + timeout (~18 call site). |
| 2 | **#7 endpoint `/trade/strategies`** | media | basso | Economico, elimina il drift già presente (`EURUSD_NOHOLD` mancante). |
| 3 | **#1 `send_order`/close in-process** | bassa | basso | Riduce un failure mode e il backpressure autoinflitto; va applicato anche a `close_slave_position()`. |
| 4 | Resto della **#2**: idempotenza sui POST ordine | media | medio | Solo dopo aver capito come identificare un segnale: il retry cieco duplica gli ordini. |
| 5 | **#5 rotazione di `server_log.txt`** | bassa | minimo | Zero costo, ma sul file giusto (`logger.py`), non su `fxscript.log`. |
| 6 | **#8 pulizia console log** | bassa | minimo | Solo rumore; estendere a tutto `user-dashboard.component.ts`. |
| 7 | **#6 `is_market_open` per simbolo** | bassa | medio | Condizionale: solo se entrano nuove asset class. |

**Nota:** il documento originale classificava la #4 come "alta solo se la rete non è isolata". Anche in caso di rete isolata resta la miglioria con il miglior rapporto rischio coperto / sforzo, quindi andrebbe fatta comunque.

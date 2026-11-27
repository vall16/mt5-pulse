# SUPER_ADAPTIVE

Nuovo segnale derivato da `SUPER`. **`SUPER` / `SuperXauNoCloseStrategy` non è stato modificato**:
`SUPER_ADAPTIVE` è una classe nuova (`SuperXauAdaptiveStrategy`) registrata con un nome nuovo,
e la sua logica pura vive in `backend/super_adaptive_core.py`, usata sia dal polling live sia dal backtest.

## Cosa cambia rispetto a SUPER

| Funzionalità | SUPER | SUPER_ADAPTIVE |
|---|---|---|
| Parametri | fissi nel codice | JSON per-trader (`traders.strategy_params`), validato e clampato |
| Indicatori | duplicati tra live e backtest | `compute_adaptive_indicators()` condivisa (live `shift=2`, backtest `shift=2` sul bar chiuso precedente) |
| Matrice contesto | regime filter booleano | sessione × regime con soglie e size diverse |
| Score | booleano (SUPER) / stepwise (SUPER_DM) | continuo 0..1 che modula gate, size e SL/TP |
| Isteresi | no | `hysteresis_bars` / `hysteresis_hits` |
| Scadenza segnale | no | `expiry_bars` sul trigger |
| Volatility targeting | no | SL/TP allargati se ATR M5 sopra la mediana |
| Sizing | `fix_lot` | `fix_lot × multiplier` oppure lotto da `risk_pct` |
| AdaptiveAgent | non collegato | avviato automaticamente, fattori applicati come scala relativa |
| Telemetria | regime nei log | `score`, `session`, `regime`, `config_version` nei log e nei trade di backtest |

## Attivazione

1. Selezionare `XAUUSD Super Adaptive` nella dashboard (o impostare `selected_signal = 'SUPER_ADAPTIVE'`).
2. Opzionale: inserire il JSON dei parametri nel campo **Parametri SUPER_ADAPTIVE** della card e salvare.
3. Avviare il polling: l'AdaptiveAgent viene avviato automaticamente per questo segnale.
   Viene fermato automaticamente allo stop solo se era stato avviato da SUPER_ADAPTIVE.

Il JSON viene salvato come testo nella colonna `traders.strategy_params` (migration automatica all'avvio).
Chiavi sconosciute vengono ignorate; i valori fuori intervallo vengono clampati (vedi `AdaptiveParams.bounds()`).

## Parametri principali

```json
{
  "score_threshold": 0.65,
  "score_full_size": 0.85,
  "min_score_to_trigger": 0.55,
  "hysteresis_bars": 3,
  "hysteresis_hits": 2,
  "expiry_bars": 3,
  "size_multiplier": 1.0,
  "risk_pct": 0.0,
  "sl_factor_normal": 1.5,
  "tp_factor_normal": 2.2,
  "sl_factor_trend": 2.0,
  "tp_factor_trend": 3.0,
  "allow_news": false,
  "allow_range": true
}
```

- `risk_pct = 0` → usa `fix_lot` del trader; `> 0` → lotto da equity × rischio / (SL points × point value).
- `allow_news = false` → nessun ingresso in regime NEWS (default).
- `allow_range = true` → in RANGE si entra ma con soglia più alta e size ridotta.
- `config_version` è gestito dal sistema (aumenta quando il supervisore applica nuovi parametri).

### Matrice sessione × regime (override automatici)

| Sessione | RANGE | NORMAL | TREND | NEWS |
|---|---|---|---|---|
| ASIA | soglia 0.74, size 0.5 | 0.70 / 0.75 | 0.68 / 0.75 | bloccata |
| LONDON | 0.72 / 0.6 | 0.65 / 1.0 | 0.62 / 1.25 | bloccata |
| NY-LON | 0.72 / 0.6 | 0.66 / 1.0 | 0.63 / 1.15 | bloccata |
| NY | 0.74 / 0.5 | 0.68 / 0.85 | 0.65 / 1.0 | bloccata |
| OFF | bloccata | bloccata | bloccata | bloccata |

Gli override si applicano sopra ai parametri del trader; l'AdaptiveAgent può poi scalare SL/TP entro guardrail.

## Backtest

`SUPER_ADAPTIVE` è selezionabile anche nella pagina backtest. In `run_backtest()` il percorso storico
resta invariato per tutti gli altri segnali; per questo segnale viene chiamata
`strategy.compute_indicators()` su_slice allineate M1/M5/M15, poi `prepare_signal_context()`.
SL/TP e lotto usati nel backtest sono quelli calcolati dal decision core, non i default 500/600.
Ogni trade di backtest contiene `regime`, `session`, `score`, `config_version` e `lot`.
La richiesta `POST /db/backtest` accetta anche `strategy_params` (JSON opzionale) per testare
una configurazione specifica senza modificare il trader:

```json
{"strategy": "SUPER_ADAPTIVE", "symbol": "XAUUSD", "trader_id": 123,
 "strategy_params": {"score_threshold": 0.7, "risk_pct": 0.5}}
```

## Supervisore

Il supervisore riceve `params` per i trader SUPER_ADAPTIVE e può proporre
`{"action": "...", "params": {"score_threshold": 0.7, ...}}`.
Le proposte vengono validate con `AdaptiveParams.from_dict()` e appaiono come `suggested_params`
nelle raccomandazioni. Per applicarle:

```
POST /supervisor/apply
{"trader_id": 123, "action": "APPLY_PARAMS", "params": {"score_threshold": 0.7}}
```

L'azione persiste il JSON, aumenta `config_version`, aggiorna l'AdaptiveAgent in memoria e
riavvia il polling se il trader era attivo. Le azioni `ACTIVE` / `PAUSE` restano invariate.

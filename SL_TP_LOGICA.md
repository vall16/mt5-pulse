# Meccanismo SL/TP per segnali

## Regola generale
```python
# Toggle "Forza SL/TP del form" ATTIVO:
sl_points = trader.sl              # usa i valori del form, ignora il segnale
tp_points = trader.tp

# Toggle DISATTIVO (default):
sl_points = effective_sl if effective_sl is not None else trader.sl
tp_points = effective_tp if effective_tp is not None else trader.tp
```
prova git

**Priorità:** SL/TP dinamico (calcolato dalla strategia) > SL/TP fissi (impostati dall'utente nel form della dashboard)

**Toggle "Forza SL/TP del form":** quando attivo, usa **esclusivamente** i valori SL/TP inseriti nei campi del form della card, ignorando qualsiasi calcolo dinamico del segnale.

---

## Segnali che usano SL/TP FISSI (sempre quelli dell'utente)

| Segnale | Label |
|---------|-------|
| BASE | XAUUSD Base |
| BASE_NOHOLD | XAUUSD Base NoHold |
| TRENDGUARD_XAU | XAUUSD Trend Guard |
| EURUSD_NOHOLD | EURUSD Super |
| MSFT | MSFT M15 |
| NVDA | NVDA M15 |

---

## Segnali con SL/TP DINAMICI (override via ATR M5)

| Segnale | Label | Condizione ATR | SL | TP |
|---------|-------|---------------|----|----|
| SUPER | XAUUSD Super | ATR M5 ≤ 12 | 500 | 600 |
| SUPER_USDJPY | USDJPY Super | ATR M5 ≤ 0.050 | 500 | 600 |
| GBPUSD | GBPUSD Super | ATR M5 ≤ 0.0012 | 500 | 600 |
| GBPJPY | GBPJPY Super | ATR M5 ≤ 0.080 | 800 | 1000 |
| AUDJPY | AUDJPY Super | ATR M5 ≤ 0.060 | 600 | 800 |

Se la condizione ATR **non è soddisfatta**, la strategia non fa override e vengono usati i **valori fissi dell'utente**.

---

## Dove vedere nel codice

- File: `backend/trading_signals_multi2.py`
- `send_order()` — logica priorità SL/TP con toggle `use_signal_sl_tp`
- `get_dynamic_sl_tp()` — implementato in ogni strategia
- `run()` — calcolo e salvataggio `effective_sl`/`effective_tp` a ogni ciclo

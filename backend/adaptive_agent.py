# --- ADAPTIVE AGENT: regola semplici per SL/TP dinamici ---
import time
import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional


class AdaptiveAgent:
    """
    Agente adaptive per una singola sessione (trader).
    Monitora i trade chiusi e adatta sl_atr_factor / tp_atr_factor
    con regole if/else semplici.
    """

    def __init__(self, strategy_name: str, symbol: str):
        self.strategy_name = strategy_name
        self.symbol = symbol

        # --- parametri adattivi ---
        self.params = {
            "sl_atr_factor": 2.0,
            "tp_atr_factor": 3.0,
        }

        # --- trade log (ultimi 50) ---
        self.trade_log: list[dict] = []
        self._max_log = 50

        # --- conteggio per trigger analisi ---
        self._closed_count = 0
        self._analyze_every = 10

        # --- stats cache ---
        self.stats: dict = {}

        # --- lock per thread safety ---
        self._lock = threading.Lock()

        # --- positions tracking (per rilevare chiusure) ---
        self.prev_positions: dict[int, dict] = {}  # ticket -> {symbol, type, volume}

        # --- stato ---
        self.started_at = datetime.now(ZoneInfo("Europe/Rome")).isoformat()
        self.last_adjustment: Optional[str] = None
        self.adjustment_count = 0

    # ------------------------------------------------------------------ #
    #  RILEVAMENTO CHIUSURE
    # ------------------------------------------------------------------ #

    def detect_closed_trades(self, current_positions: list[dict]) -> list[dict]:
        """
        Confronta le posizioni precedenti con quelle correnti.
        Restituisce la lista delle posizioni chiuse.
        """
        current_tickets = {p["ticket"] for p in current_positions if "ticket" in p}
        closed = []
        for ticket, info in list(self.prev_positions.items()):
            if ticket not in current_tickets:
                closed.append({**info, "ticket": ticket})
        # aggiorna
        self.prev_positions = {
            p["ticket"]: {
                "symbol": p.get("symbol"),
                "type": p.get("type"),
                "volume": p.get("volume"),
                "price_open": p.get("price_open"),
            }
            for p in current_positions
            if "ticket" in p
        }
        return closed

    # ------------------------------------------------------------------ #
    #  REGISTRAZIONE TRADE
    # ------------------------------------------------------------------ #

    def on_trade_closed(self, pnl: float, atr_at_entry: float, session: str = "",
                        ticket: Optional[int] = None, score: Optional[float] = None,
                        config_version: Optional[int] = None, direction: Optional[str] = None):
        """
        Registra un trade chiuso. I campi opzionali (score/config/direzione)
        sono usati da SUPER_ADAPTIVE; gli altri segnali li lasciano a None.
        """
        with self._lock:
            record = {
                "ticket": ticket,
                "pnl": round(pnl, 2),
                "atr_at_entry": round(atr_at_entry, 4),
                "session": session,
                "result": "win" if pnl > 0 else "loss",
                "timestamp": datetime.now(ZoneInfo("Europe/Rome")).isoformat(),
            }
            # I campi aggiuntivi esistono solo per SUPER_ADAPTIVE: gli altri
            # segnali mantengono esattamente il record storico.
            if score is not None:
                record["score"] = round(float(score), 3)
            if config_version is not None:
                record["config_version"] = config_version
            if direction is not None:
                record["direction"] = direction
            self.trade_log.append(record)
            if len(self.trade_log) > self._max_log:
                self.trade_log = self.trade_log[-self._max_log:]
            self._closed_count += 1

    # ------------------------------------------------------------------ #
    #  ANALISI
    # ------------------------------------------------------------------ #

    def analyze(self) -> dict:
        """
        Calcola statistiche sulla finestra mobile dei trade log.
        """
        with self._lock:
            trades = self.trade_log
            if not trades:
                return {"win_rate": 0, "avg_win": 0, "avg_loss": 0, "rr_ratio": 0, "total": 0}

            wins = [t for t in trades if t["result"] == "win"]
            losses = [t for t in trades if t["result"] == "loss"]

            total = len(trades)
            win_rate = len(wins) / total if total > 0 else 0
            avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
            avg_loss = abs(sum(t["pnl"] for t in losses) / len(losses)) if losses else 0.01
            rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0

            # Statistiche per sessione solo per SUPER_ADAPTIVE: per gli altri
            # segnali lo stats dict resta identico a prima.
            by_session: dict = {}
            if self.strategy_name == "SUPER_ADAPTIVE":
                for t in trades:
                    key = t.get("session") or "-"
                    agg = by_session.setdefault(key, {"total": 0, "wins": 0, "pnl": 0.0})
                    agg["total"] += 1
                    agg["wins"] += 1 if t["result"] == "win" else 0
                    agg["pnl"] += float(t.get("pnl", 0))

            self.stats = {
                "win_rate": round(win_rate * 100, 1),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "rr_ratio": round(rr_ratio, 2),
                "total": total,
                "wins": len(wins),
                "losses": len(losses),
                "sl_atr_factor": self.params["sl_atr_factor"],
                "tp_atr_factor": self.params["tp_atr_factor"],
            }
            if self.strategy_name == "SUPER_ADAPTIVE":
                self.stats["by_session"] = {
                    k: {
                        "total": v["total"],
                        "win_rate": round(100.0 * v["wins"] / max(1, v["total"]), 1),
                        "pnl": round(v["pnl"], 2),
                    }
                    for k, v in by_session.items()
                }
            return self.stats

    # ------------------------------------------------------------------ #
    #  REGOLE DI ADATTAMENTO
    # ------------------------------------------------------------------ #

    def should_analyze(self) -> bool:
        """True se ci sono abbastanza nuovi trade per rianalizzare."""
        return self._closed_count >= self._analyze_every

    def adjust(self) -> dict:
        """
        Applica le regole semplici e restituisce i params aggiornati.
        Resetta il contatore dopo l'aggiustamento.
        """
        stats = self.analyze()
        if stats["total"] < self._analyze_every:
            return self.params

        wr = stats["win_rate"] / 100  # converti in decimale
        avg_win = stats["avg_win"]
        avg_loss = stats["avg_loss"]
        rr = stats["rr_ratio"]

        sl = self.params["sl_atr_factor"]
        tp = self.params["tp_atr_factor"]
        changed = False

        # Regola 1: win rate troppo basso → allarga SL, restringi TP
        if wr < 0.35:
            sl += 0.5
            tp -= 0.2
            changed = True

        # Regola 2: win rate eccellente → prova a stretire
        elif wr > 0.70 and rr > 1.5:
            sl -= 0.2
            tp += 0.2
            changed = True

        # Regola 3: perdite troppo grosse rispetto ai guadagni
        if avg_loss > avg_win * 1.5:
            sl += 0.3
            changed = True

        # Regola 4: risk/reward troppo basso
        if rr < 1.0:
            tp += 0.3
            changed = True

        # Guard rail
        sl = max(1.5, min(sl, 5.0))
        tp = max(1.0, min(tp, 4.0))

        # TP deve essere >= SL * 0.8
        if tp < sl * 0.8:
            tp = round(sl * 0.8, 1)

        self.params["sl_atr_factor"] = round(sl, 1)
        self.params["tp_atr_factor"] = round(tp, 1)

        if changed:
            self.last_adjustment = datetime.now(ZoneInfo("Europe/Rome")).isoformat()
            self.adjustment_count += 1
            self._closed_count = 0

        self.analyze()  # aggiorna stats cache
        return self.params

    # ------------------------------------------------------------------ #
    #  GET / STATUS
    # ------------------------------------------------------------------ #

    def get_params(self) -> dict:
        return dict(self.params)

    def apply_params(self, params: dict) -> dict:
        """Applica parametri proposti dal supervisore, con guardrail."""
        for key, low, high in (
            ("sl_atr_factor", 1.5, 5.0),
            ("tp_atr_factor", 1.0, 4.0),
        ):
            value = (params or {}).get(key)
            if value is None:
                continue
            try:
                self.params[key] = round(min(max(float(value), low), high), 2)
            except (TypeError, ValueError):
                continue
        self.last_adjustment = datetime.now(ZoneInfo("Europe/Rome")).isoformat()
        self.adjustment_count += 1
        return dict(self.params)

    def get_status(self) -> dict:
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "params": self.params,
            "stats": self.stats,
            "trade_count": len(self.trade_log),
            "started_at": self.started_at,
            "last_adjustment": self.last_adjustment,
            "adjustment_count": self.adjustment_count,
        }

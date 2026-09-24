"""
News Filter — blocca il trading durante eventi ad alto impatto.
Usa il calendario economico di MT5 (mt5.economic_calendar).
"""
import logging
import threading
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("news_filter")

# Mappatura simbolo → valute rilevanti
SYMBOL_CURRENCIES = {
    'XAUUSD': ['USD'],
    'EURUSD': ['EUR', 'USD'],
    'GBPUSD': ['GBP', 'USD'],
    'USDJPY': ['USD', 'JPY'],
    'GBPJPY': ['GBP', 'JPY'],
    'AUDJPY': ['AUD', 'JPY'],
    'EURJPY': ['EUR', 'JPY'],
    'AUDUSD': ['AUD', 'USD'],
    'MSFT': ['USD'],
    'MSFT.NAS': ['USD'],
    'NVDA': ['USD'],
    'NVDA.NAS': ['USD'],
}


class NewsFilter:
    """
    Singleton che cachea gli eventi ad alto impatto dal calendario MT5.
    Refresh automatico ogni 30 minuti.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, buffer_minutes: int = 30, refresh_seconds: int = 1800):
        if self._initialized:
            return
        self.buffer_minutes = buffer_minutes
        self.refresh_seconds = refresh_seconds
        self._events: list[dict] = []
        self._last_fetch: datetime | None = None
        self._initialized = True

    def _fetch_events(self):
        """Ottiene eventi ad alto impatto dai prossimi 3 giorni via MT5."""
        try:
            import MetaTrader5 as mt5

            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=3)

            events = mt5.economic_calendar(start, end)
            if events is None:
                logger.warning("economic_calendar returned None (MT5 non connesso?)")
                return

            # importance: 0=low, 1=medium, 2=HIGH
            high_impact = [e for e in events if e.importance == 2]

            self._events = [
                {
                    'time': e.date,
                    'currency': e.currency,
                    'name': e.name,
                    'forecast': e.forecast,
                    'previous': e.previous,
                }
                for e in high_impact
            ]
            self._last_fetch = datetime.now(timezone.utc)
            logger.info(f"NewsFilter: {len(self._events)} eventi high-impact caricati")

        except ImportError:
            logger.warning("MetaTrader5 non importato — news filter disattivo")
        except Exception as e:
            logger.error(f"NewsFilter fetch error: {e}")

    def _maybe_refresh(self):
        """Refresh se la cache è vecchia."""
        now = datetime.now(timezone.utc)
        if self._last_fetch is None:
            self._fetch_events()
        elif (now - self._last_fetch).total_seconds() > self.refresh_seconds:
            self._fetch_events()

    def is_blocked(self, symbol: str) -> tuple[bool, str]:
        """
        Ritorna (blocked, reason).
        blocked=True se siamo in una news window per le valute del simbolo.
        """
        self._maybe_refresh()

        currencies = SYMBOL_CURRENCIES.get(symbol, ['USD'])
        now = datetime.now(timezone.utc)
        buffer_sec = self.buffer_minutes * 60

        for ev in self._events:
            if ev['currency'] not in currencies:
                continue
            delta = abs((now - ev['time']).total_seconds())
            if delta < buffer_sec:
                mins = int(delta // 60)
                return True, f"{ev['name']} ({ev['currency']}) tra/dopo {mins}min"

        return False, ""

    def get_upcoming(self, symbol: str, hours: int = 12) -> list[dict]:
        """Eventi high-impact prossimi per il simbolo (per UI)."""
        self._maybe_refresh()
        currencies = SYMBOL_CURRENCIES.get(symbol, ['USD'])
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours)

        result = []
        for ev in self._events:
            if ev['currency'] not in currencies:
                continue
            if now <= ev['time'] <= cutoff:
                result.append(ev)
        return sorted(result, key=lambda x: x['time'])


# Instance globale
news_filter = NewsFilter(buffer_minutes=30)

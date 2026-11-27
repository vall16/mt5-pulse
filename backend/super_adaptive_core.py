"""Logica pura di SUPER_ADAPTIVE.

Modulo senza dipendenze da trading_signals_multi2: puo essere usato sia dal
polling live sia dal backtest con esattamente lo stesso codice.

Non modifica SUPER: tutte le funzioni qui dentro sono nuove.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from indicators.ta import compute_atr, compute_ema, compute_hma, compute_macd, compute_rsi


# ─────────────────────── PARAMETRI ───────────────────────


@dataclass
class AdaptiveParams:
    """Parametri configurabili per singolo trader.

    I default riproducono SUPER; tutto il resto e nuovo. Il JSON arrivante dal
    DB viene filtrato attraverso ``from_dict``: chiavi sconosciute vengono
    ignorate e i valori vengono clampati, cosi una config sbagliata non puo
    generare ordini fuori controllo.
    """

    # indicatori
    ema_fast: int = 9
    ema_slow: int = 21
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    hma_period: int = 16
    ema_macro: int = 50
    atr_period: int = 14
    regime_window: int = 192
    expansion_period: int = 10

    # filtri
    rsi_long_min: float = 45.0
    rsi_long_max: float = 70.0
    rsi_long_max_trend: float = 80.0
    rsi_short_min: float = 30.0
    rsi_short_min_trend: float = 25.0
    rsi_short_max: float = 55.0
    spike_atr_factor: float = 4.0

    # score / decisione
    score_threshold: float = 0.65
    score_full_size: float = 0.85
    min_score_to_trigger: float = 0.55
    hysteresis_bars: int = 3
    hysteresis_hits: int = 2
    expiry_bars: int = 3

    # SL / TP
    sl_factor_normal: float = 1.5
    tp_factor_normal: float = 2.2
    sl_factor_trend: float = 2.0
    tp_factor_trend: float = 3.0
    sl_min: int = 500
    sl_max: int = 2000
    tp_min: int = 600
    tp_max: int = 3000

    # sizing
    size_multiplier: float = 1.0
    half_size_at_score: bool = True
    risk_pct: float = 0.0            # 0 = disattivato (usa fix_lot del trader)
    point_value_per_lot: float = 1.0  # XAUUSD: 1 punto = 1 USD per 1.0 lotto
    min_lot: float = 0.01
    lot_step: float = 0.01
    max_lot: float = 1.0

    # regime
    allow_news: bool = False
    allow_range: bool = True

    # metadata (versione della configurazione, usata per il confronto trade)
    config_version: int = 1

    @classmethod
    def bounds(cls) -> Dict[str, Tuple[float, float]]:
        """Limiti di sicurezza: nessuna config puo uscire da questi intervalli."""
        return {
            "ema_fast": (3, 50),
            "ema_slow": (5, 200),
            "macd_fast": (3, 40),
            "macd_slow": (5, 100),
            "macd_signal": (2, 30),
            "rsi_period": (5, 50),
            "hma_period": (5, 100),
            "ema_macro": (20, 300),
            "atr_period": (5, 60),
            "regime_window": (48, 500),
            "expansion_period": (3, 50),
            "rsi_long_min": (10, 60),
            "rsi_long_max": (50, 95),
            "rsi_long_max_trend": (55, 98),
            "rsi_short_min": (5, 50),
            "rsi_short_min_trend": (2, 45),
            "rsi_short_max": (40, 90),
            "spike_atr_factor": (2.0, 8.0),
            "score_threshold": (0.45, 0.95),
            "score_full_size": (0.60, 1.0),
            "min_score_to_trigger": (0.30, 0.90),
            "hysteresis_bars": (1, 10),
            "hysteresis_hits": (1, 10),
            "expiry_bars": (1, 20),
            "sl_factor_normal": (0.8, 4.0),
            "tp_factor_normal": (1.0, 5.0),
            "sl_factor_trend": (0.8, 5.0),
            "tp_factor_trend": (1.0, 6.0),
            "sl_min": (100, 2000),
            "sl_max": (300, 4000),
            "tp_min": (150, 4000),
            "tp_max": (300, 6000),
            "size_multiplier": (0.1, 3.0),
            "risk_pct": (0.0, 3.0),
            "point_value_per_lot": (0.01, 50.0),
            "min_lot": (0.001, 10.0),
            "lot_step": (0.001, 10.0),
            "max_lot": (0.01, 100.0),
        }

    def __post_init__(self) -> None:
        bounds = self.bounds()
        for key, (low, high) in bounds.items():
            value = getattr(self, key, None)
            if value is None:
                continue
            if isinstance(value, int) and not isinstance(value, bool):
                value = int(min(max(value, low), high))
            else:
                value = float(min(max(value, low), high))
            setattr(self, key, value)
        self.hysteresis_hits = min(self.hysteresis_hits, self.hysteresis_bars)
        self.sl_max = max(self.sl_max, self.sl_min)
        self.tp_max = max(self.tp_max, self.tp_min)
        self.tp_min = max(self.tp_min, self.sl_min + 100)
        self.tp_max = max(self.tp_max, self.tp_min)
        self.score_full_size = max(self.score_full_size, self.score_threshold + 0.05)

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, Any]]) -> "AdaptiveParams":
        if not raw:
            return cls()
        if not isinstance(raw, dict):
            return cls()
        known = {f for f in cls.__dataclass_fields__ if not f.startswith("_")}
        clean = {
            k: v for k, v in raw.items()
            if k in known and k not in ("config_version",) and v is not None
        }
        # versione viene preservata solo se esplicita e numerica
        version = raw.get("config_version")
        if isinstance(version, (int, float)) and not isinstance(version, bool):
            clean["config_version"] = int(version)
        try:
            return cls(**clean)
        except (TypeError, ValueError):
            return cls()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def merged(self, overrides: Dict[str, Any]) -> "AdaptiveParams":
        """Copia con override gia validati (usata per sessione/regime/agente)."""
        if not overrides:
            return self
        raw = self.to_dict()
        raw.update(overrides)
        return AdaptiveParams.from_dict(raw)


# ─────────────────────── CONTEXT MATRIX ───────────────────────

# sessione x regime -> override. "*" = qualsiasi regressione.
CONTEXT_MATRIX: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("OFF", "*"): {"allow_entry": False},
    ("ASIA", "RANGE"): {"score_threshold": 0.74, "size_multiplier": 0.5},
    ("ASIA", "NORMAL"): {"score_threshold": 0.70, "size_multiplier": 0.75},
    ("ASIA", "TREND"): {"score_threshold": 0.68, "size_multiplier": 0.75},
    ("ASIA", "NEWS"): {"allow_entry": False},
    ("LONDON", "RANGE"): {"score_threshold": 0.72, "size_multiplier": 0.6},
    ("LONDON", "NORMAL"): {"score_threshold": 0.65, "size_multiplier": 1.0},
    ("LONDON", "TREND"): {"score_threshold": 0.62, "size_multiplier": 1.25},
    ("LONDON", "NEWS"): {"allow_entry": False},
    ("NY-LON", "RANGE"): {"score_threshold": 0.72, "size_multiplier": 0.6},
    ("NY-LON", "NORMAL"): {"score_threshold": 0.66, "size_multiplier": 1.0},
    ("NY-LON", "TREND"): {"score_threshold": 0.63, "size_multiplier": 1.15},
    ("NY-LON", "NEWS"): {"allow_entry": False},
    ("NY", "RANGE"): {"score_threshold": 0.74, "size_multiplier": 0.5},
    ("NY", "NORMAL"): {"score_threshold": 0.68, "size_multiplier": 0.85},
    ("NY", "TREND"): {"score_threshold": 0.65, "size_multiplier": 1.0},
    ("NY", "NEWS"): {"allow_entry": False},
}


def context_overrides(session: str, regime: str, allow_news: bool, allow_range: bool) -> Dict[str, Any]:
    """Risolve la matrice sessione x regime con fallback sul wildcard."""
    result: Dict[str, Any] = {}
    for key in ((session, regime), (session, "*"), ("*", regime), ("*", "*")):
        result.update(CONTEXT_MATRIX.get(key, {}))
    if regime == "NEWS" and not allow_news:
        result["allow_entry"] = False
    if regime == "RANGE" and not allow_range:
        result["allow_entry"] = False
        result["score_threshold"] = max(result.get("score_threshold", 0.65), 0.80)
    return result


# ─────────────────────── REGIME ───────────────────────


def classify_regime(atr_m15: float, percentile: float, trend_score: float,
                    is_spike: bool) -> str:
    """Stesso schema di SUPER, ma NEWS non e mai considerata 'ok' per entrare."""
    if is_spike or (percentile == percentile and percentile > 0.90):
        return "NEWS"
    if not (percentile == percentile):
        return "NORMAL"
    if percentile > 0.60 and abs(trend_score) > 0.35:
        return "TREND"
    if percentile > 0.25:
        return "NORMAL"
    return "RANGE"


def entry_regime_ok(regime: str) -> bool:
    return regime in ("TREND", "NORMAL")


# ─────────────────────── INDICATORI (CONDIVISI LIVE/BACKTEST) ───────────────────────


def _true_range(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev).abs(),
        (df["low"] - prev).abs(),
    ], axis=1).max(axis=1)


def compute_adaptive_indicators(df_m1: pd.DataFrame,
                                df_m5: pd.DataFrame,
                                df_m15: pd.DataFrame,
                                params: AdaptiveParams,
                                shift: int = 2) -> Dict[str, Any]:
    """Calcola tutti gli indicatori sulla candela chiusa ``iloc[-shift]``.

    ``shift=2`` riproduce SUPER (penultima candela chiusa). ``shift=1`` viene
    usato dal backtest, dove l'indice corrente e gia una candela chiusa.
    La Logica e identica nei due percorsi: questo e il punto chiave.
    """
    if df_m1 is None or df_m5 is None or df_m15 is None or len(df_m1) < shift + 5:
        raise ValueError("dati M1/M5/M15 insufficienti")

    i = -shift
    ema_fast = compute_ema(df_m1, params.ema_fast)
    ema_slow = compute_ema(df_m1, params.ema_slow)
    macd, macd_sig = compute_macd(df_m1, params.macd_fast, params.macd_slow, params.macd_signal)
    rsi = compute_rsi(df_m1, params.rsi_period)
    atr_m1 = _true_range(df_m1).rolling(params.atr_period).mean()

    hma_m5 = compute_hma(df_m5, params.hma_period)
    tr_m5 = _true_range(df_m5)
    atr_m5 = tr_m5.rolling(params.atr_period).mean()

    ema_macro = compute_ema(df_m15, params.ema_macro)
    atr_m15 = _true_range(df_m15).rolling(params.atr_period).mean()
    pct = compute_rolling_percentile_safe(atr_m15, params.regime_window)

    atr_val = _at(atr_m1, i)
    body = abs(_at(df_m1["close"], i) - _at(df_m1["open"], i))
    is_spike = bool(atr_val > 0 and body > atr_val * params.spike_atr_factor)
    expansion = bool(atr_val > _at(atr_m1.rolling(params.expansion_period).mean().shift(1), i))

    ema_m15_now = _at(ema_macro, i)
    ema_m15_prev = _at(ema_macro, -min(shift + 10, len(df_m15) - 1))
    atr15 = _at(atr_m15, i)
    trend_score = (ema_m15_now - ema_m15_prev) / atr15 if atr15 and atr15 > 0 else 0.0
    regime = classify_regime(atr15, _at(pct, i), trend_score, is_spike)

    atr5 = _at(atr_m5, i)
    vol_median = _at(atr_m5.rolling(params.regime_window).median(), i)
    vol_ratio = float(atr5 / vol_median) if vol_median and vol_median > 0 else 1.0

    return {
        "ema_fast": _at(ema_fast, i),
        "ema_slow": _at(ema_slow, i),
        "ema_spread": (_at(ema_fast, i) - _at(ema_slow, i)) / atr_val if atr_val > 0 else 0.0,
        "macd": _at(macd, i),
        "macd_sig": _at(macd_sig, i),
        "macd_hist_norm": (_at(macd, i) - _at(macd_sig, i)) / atr_val if atr_val > 0 else 0.0,
        "rsi": _at(rsi, i),
        "hma": _at(hma_m5, i),
        "hma_prev": _at(hma_m5, -min(shift + 1, len(df_m5) - 1)),
        "hma_slope": (_at(hma_m5, i) - _at(hma_m5, -min(shift + 1, len(df_m5) - 1))) / atr5 if atr5 and atr5 > 0 else 0.0,
        "macro_up": bool(_at(df_m15["close"], i) > ema_m15_now),
        "macro_dist": (_at(df_m15["close"], i) - ema_m15_now) / atr15 if atr15 and atr15 > 0 else 0.0,
        "atr_m1": atr_val,
        "atr_m5": atr5,
        "atr_m15": atr15,
        "atr_pct": _at(pct, i),
        "vol_ratio": vol_ratio,
        "is_spike": is_spike,
        "expansion": expansion,
        "regime": regime,
        "trend_score": trend_score,
        "bar_time": df_m1["time"].iloc[i] if "time" in df_m1.columns else None,
    }


def compute_rolling_percentile_safe(series: pd.Series, window: int) -> pd.Series:
    if len(series) < 2:
        return pd.Series([np.nan] * len(series), index=series.index)
    return series.rolling(max(5, window), min_periods=max(5, window // 2)).apply(
        lambda x: float(np.mean(x <= x[-1])), raw=True
    )


def _at(series: pd.Series, index: int) -> float:
    try:
        value = series.iloc[index]
    except (IndexError, KeyError, TypeError):
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


# ─────────────────────── SCORE CONTINUO ───────────────────────


def compute_score(ind: Dict[str, Any], direction: str, params: AdaptiveParams) -> Tuple[float, Dict[str, float]]:
    """Score 0..1. Stessi 4 fattori di SUPER_DM, ma con slope normalizzate.

    Il risultato non e solo un gate: modula soglia, size e SL/TP.
    """
    sign = 1.0 if direction == "buy" else -1.0

    momentum = 0.0
    if np.isfinite(ind["macd_hist_norm"]):
        momentum += 0.6 * _sigmoid(ind["macd_hist_norm"] * sign * 6.0)
    rsi = ind["rsi"]
    if np.isfinite(rsi):
        if direction == "buy":
            momentum += 0.4 * _rsi_score(rsi, params.rsi_long_min, params.rsi_long_max_trend)
        else:
            momentum += 0.4 * _rsi_score(100.0 - rsi, 100.0 - params.rsi_short_max,
                                         100.0 - params.rsi_short_min_trend)

    trend = 0.0
    if np.isfinite(ind["ema_spread"]):
        trend += 0.4 * _sigmoid(ind["ema_spread"] * sign * 4.0)
    if np.isfinite(ind["hma_slope"]):
        trend += 0.35 * _sigmoid(ind["hma_slope"] * sign * 6.0)
    if np.isfinite(ind["macro_dist"]):
        macro_bonus = 1.0 if (ind["macro_up"] == (direction == "buy")) else 0.0
        trend += 0.25 * (0.5 * macro_bonus + 0.5 * _sigmoid(ind["macro_dist"] * sign * 2.0))

    volatility = 0.0
    volatility += 0.5 if ind["expansion"] else 0.0
    volatility += 0.3 if not ind["is_spike"] else 0.0
    volatility += 0.2 if entry_regime_ok(ind["regime"]) else 0.0

    rsi_position = 0.0
    if np.isfinite(rsi):
        if direction == "buy":
            lo, hi = params.rsi_long_min, params.rsi_long_max
        else:
            lo, hi = params.rsi_short_min, params.rsi_short_max
        mid = (lo + hi) / 2.0
        span = max(1.0, (hi - lo) / 2.0)
        rsi_position = max(0.0, 1.0 - abs(rsi - mid) / (span * 1.5))

    breakdown = {
        "momentum": round(momentum, 3),
        "trend": round(trend, 3),
        "volatility": round(volatility, 3),
        "rsi": round(rsi_position, 3),
    }
    score = (
        0.30 * momentum
        + 0.30 * trend
        + 0.25 * volatility
        + 0.15 * rsi_position
    )
    # gate booleano storico: se una condizione hard manca, il score non basta
    if not _hard_ok(ind, direction, params):
        score = min(score, params.min_score_to_trigger - 0.01)
    return round(float(np.clip(score, 0.0, 1.0)), 4), breakdown


def _hard_ok(ind: Dict[str, Any], direction: str, params: AdaptiveParams) -> bool:
    rsi = ind["rsi"]
    if not np.isfinite(rsi):
        return False
    if direction == "buy":
        rsi_ok = params.rsi_long_min < rsi < (
            params.rsi_long_max_trend if ind["regime"] == "TREND" else params.rsi_long_max
        )
    else:
        rsi_ok = (
            params.rsi_short_min_trend if ind["regime"] == "TREND" else params.rsi_short_min
        ) < rsi < params.rsi_short_max
    return (
        bool(np.isfinite(ind["ema_fast"]) and np.isfinite(ind["ema_slow"]))
        and (ind["ema_fast"] > ind["ema_slow"]) == (direction == "buy")
        and bool(np.isfinite(ind["macd"]) and np.isfinite(ind["macd_sig"]))
        and (ind["macd"] > ind["macd_sig"]) == (direction == "buy")
        and bool(np.isfinite(ind["hma"]) and np.isfinite(ind["hma_prev"]))
        and (ind["hma"] > ind["hma_prev"]) == (direction == "buy")
        and ind["macro_up"] == (direction == "buy")
        and rsi_ok
        and ind["expansion"]
        and not ind["is_spike"]
        and entry_regime_ok(ind["regime"])
    )


def _sigmoid(x: float) -> float:
    if not np.isfinite(x):
        return 0.0
    return float(1.0 / (1.0 + np.exp(-np.clip(x, -10.0, 10.0))))


def _rsi_score(rsi: float, lo: float, hi: float) -> float:
    if rsi < lo:
        return max(0.0, 1.0 - (lo - rsi) / max(1.0, lo))
    if rsi > hi:
        return max(0.0, 1.0 - (rsi - hi) / max(1.0, 100.0 - hi))
    return 1.0


# ─────────────────────── HYSTERESIS / EXPIRY ───────────────────────


def score_history_update(state: Dict[str, Any], direction: str, score: float, bars: int) -> None:
    key = f"{direction}_scores"
    history = state.setdefault(key, [])
    history.append(float(score))
    del history[:-max(1, bars)]


def hysteresis_ok(state: Dict[str, Any], direction: str, threshold: float,
                  bars: int, hits: int) -> bool:
    history = state.get(f"{direction}_scores", [])
    if len(history) < max(1, hits):
        return False
    recent = history[-max(1, bars):]
    return sum(1 for s in recent if s >= threshold) >= min(hits, len(recent))


def trigger_register(state: Dict[str, Any], direction: str, bar_id: int) -> None:
    state[f"{direction}_trigger_bar"] = int(bar_id)


def trigger_fresh(state: Dict[str, Any], direction: str, bar_id: int, expiry: int) -> bool:
    last = state.get(f"{direction}_trigger_bar")
    if last is None:
        return False
    return 0 <= int(bar_id) - int(last) <= max(1, expiry)


# ─────────────────────── SIZING ───────────────────────


def size_multiplier(score: float, params: AdaptiveParams, context_multiplier: float) -> float:
    multiplier = float(context_multiplier) * float(params.size_multiplier)
    if params.half_size_at_score and score < params.score_full_size:
        multiplier *= 0.5
    return float(np.clip(multiplier, 0.05, 5.0))


def risk_based_lot(equity: float, sl_points: float, params: AdaptiveParams) -> Optional[float]:
    """Lot sizing da rischio. None se risk_pct disattivato o dati invalidi."""
    if params.risk_pct <= 0 or not np.isfinite(equity) or equity <= 0:
        return None
    if not np.isfinite(sl_points) or sl_points <= 0:
        return None
    risk_eur = equity * params.risk_pct / 100.0
    per_lot = sl_points * params.point_value_per_lot
    if per_lot <= 0:
        return None
    raw = risk_eur / per_lot
    step = max(0.001, params.lot_step)
    lot = float(np.floor(raw / step) * step)
    return float(np.clip(lot, params.min_lot, min(params.max_lot, lot)))


# ─────────────────────── ADAPTIVE AGENT BRIDGE ───────────────────────


def agent_overrides(agent_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Converte i fattori SL/TP dell'AdaptiveAgent in override sicuri.

    L'agente lavora con sl_atr_factor/tp_atr_factor (default 2/3, tarati sul
    regime TREND). Qui li si applica come scala relativa, non come valori
    assoluti, cosi NON si modifica SUPER e i guardrail restano quelli qui.
    """
    if not agent_params:
        return {}
    try:
        sl = float(agent_params.get("sl_atr_factor", 2.0))
        tp = float(agent_params.get("tp_atr_factor", 3.0))
    except (TypeError, ValueError):
        return {}
    sl_ratio = float(np.clip(sl / 2.0, 0.8, 1.5))
    tp_ratio = float(np.clip(tp / 3.0, 0.8, 1.5))
    return {
        "sl_factor_normal": round(1.5 * sl_ratio, 3),
        "tp_factor_normal": round(2.2 * tp_ratio, 3),
        "sl_factor_trend": round(2.0 * sl_ratio, 3),
        "tp_factor_trend": round(3.0 * tp_ratio, 3),
    }


def effective_params(base: AdaptiveParams, session: str, ind: Dict[str, Any],
                     agent_params: Optional[Dict[str, Any]] = None) -> Tuple[AdaptiveParams, Dict[str, Any]]:
    """Risolve params finali: base -> matrice contesto -> volatilita -> agente."""
    ctx = context_overrides(
        session,
        ind["regime"],
        bool(base.allow_news),
        bool(base.allow_range),
    )
    overrides: Dict[str, Any] = dict(ctx)
    overrides.update(agent_overrides(agent_params))
    # volatility targeting: ATR alto rispetto alla mediana -> SL/TP piu larghi
    ratio = float(np.clip(ind["vol_ratio"], 0.5, 2.0))
    factor = float(np.clip(1.0 + 0.25 * (ratio - 1.0), 0.88, 1.25))
    for key in ("sl_factor_normal", "tp_factor_normal", "sl_factor_trend", "tp_factor_trend"):
        overrides[key] = round(float(overrides.get(key, getattr(base, key))) * factor, 3)
    return base.merged(overrides), ctx


def dynamic_sl_tp(ind: Dict[str, Any], params: AdaptiveParams) -> Tuple[int, int]:
    if params.sl_min > 0 and not np.isfinite(ind["atr_m5"]):
        return params.sl_min, params.tp_min
    atr = float(ind["atr_m5"])
    if atr <= 0:
        return params.sl_min, params.tp_min
    if ind["regime"] == "TREND":
        sl_f, tp_f = params.sl_factor_trend, params.tp_factor_trend
    else:
        sl_f, tp_f = params.sl_factor_normal, params.tp_factor_normal
    sl = int(atr * sl_f * 100)
    tp = int(atr * tp_f * 100)
    sl = max(params.sl_min, min(sl, params.sl_max))
    tp = max(max(params.tp_min, sl + 100), min(tp, params.tp_max))
    return int(sl), int(tp)

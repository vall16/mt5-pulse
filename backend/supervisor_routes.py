# --- SUPERVISOR ROUTES: API per l'agente AI che gestisce N strategie ---
import json
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from logger import log as global_log
from strategy_supervisor import (
    supervisor,
    start_supervisor,
    stop_supervisor,
    run_now,
    get_status,
    update_config,
    _is_running,
)
from db import get_connection, parse_strategy_params
from super_adaptive_core import AdaptiveParams
from models import Trader
from trading_signals_multi2 import start_polling, stop_polling, StopPollingRequest

router = APIRouter()


class SupervisorConfigRequest(BaseModel):
    interval_seconds: Optional[int] = None
    model: Optional[str] = None
    enabled_trader_ids: Optional[List[int]] = None
    lockdown_on_news: Optional[bool] = None
    max_consecutive_losses: Optional[int] = None
    min_trades_for_kill: Optional[int] = None
    min_win_rate_for_kill: Optional[float] = None
    drawdown_threshold: Optional[float] = None


class ApplyRequest(BaseModel):
    trader_id: int
    action: str
    # SUPER_ADAPTIVE: parametri da applicare con action=APPLY_PARAMS
    params: Optional[dict] = None


# ------------------------------------------------------------------ #
#  START / STOP / RUN
# ------------------------------------------------------------------ #

@router.post("/start")
def start(req: Optional[SupervisorConfigRequest] = None):
    cfg = req.model_dump(exclude_none=True) if req else None
    return start_supervisor(cfg)


@router.post("/stop")
def stop():
    return stop_supervisor()


@router.post("/run-now")
def run_now_endpoint():
    return run_now()


# ------------------------------------------------------------------ #
#  STATUS
# ------------------------------------------------------------------ #

@router.get("/status")
def status():
    return get_status()


# ------------------------------------------------------------------ #
#  CONFIG
# ------------------------------------------------------------------ #

@router.post("/config")
def config(req: SupervisorConfigRequest):
    cfg = req.model_dump(exclude_none=True)
    if not cfg:
        return {"status": "ok", "config": dict(supervisor.config)}
    return update_config(cfg)


# ------------------------------------------------------------------ #
#  APPLY (l'utente applica manualmente una raccomandazione)
# ------------------------------------------------------------------ #

def _build_trader_from_db(row: dict) -> Trader:
    return Trader(
        id=row["id"],
        name=row.get("name"),
        status="active" if row.get("is_active") else "inactive",
        master_server_id=row.get("master_server_id"),
        slave_server_id=row.get("slave_server_id"),
        sl=row.get("sl"),
        tp=row.get("tp"),
        tsl=row.get("tsl"),
        moltiplicatore=row.get("moltiplicatore") or 1.0,
        fix_lot=row.get("fix_lot"),
        custom_signal_interval=row.get("custom_signal_interval") or 5,
        selected_symbol=row.get("selected_symbol"),
        selected_signal=row.get("selected_signal"),
        sessions_filter=row.get("sessions_filter") or "ASIA,LONDON,NY-LON,NY,OFF",
        direction_filter="both",
        broker=row.get("broker"),
        strategy_params=parse_strategy_params(row.get("strategy_params")),
    )


@router.post("/apply")
def apply(req: ApplyRequest):
    action = req.action.strip().upper()
    if action not in ("ACTIVE", "PAUSE", "APPLY_PARAMS"):
        return {"status": "ko", "message": "Azione non supportata (attese ACTIVE, PAUSE o APPLY_PARAMS)"}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.*, ss.server AS broker
            FROM traders t
            LEFT JOIN servers ss ON ss.id = t.slave_server_id
            WHERE t.id = %s
        """, (req.trader_id,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not row:
        return {"status": "ko", "message": "Trader non trovato"}

    if action == "APPLY_PARAMS":
        if row.get("selected_signal") != "SUPER_ADAPTIVE":
            return {"status": "ko", "message": "APPLY_PARAMS e' solo per SUPER_ADAPTIVE"}
        if not req.params:
            return {"status": "ko", "message": "Nessun parametro fornito"}

        current = parse_strategy_params(row.get("strategy_params")) or {}
        merged = dict(current)
        merged.update(req.params)
        validated = AdaptiveParams.from_dict(merged).to_dict()
        validated["config_version"] = int(validated.get("config_version", 1)) + 1
        payload = json.dumps(validated, ensure_ascii=False)

        write_conn = get_connection()
        write_cursor = write_conn.cursor()
        try:
            write_cursor.execute(
                "UPDATE traders SET strategy_params = %s WHERE id = %s",
                (payload, req.trader_id),
            )
            write_conn.commit()
        finally:
            write_cursor.close()
            write_conn.close()

        # Aggiorna anche l'AdaptiveAgent in memoria, se attivo.
        from adaptive_routes import get_agent
        agent = get_agent(req.trader_id)
        agent_params = None
        if agent:
            agent_params = agent.apply_params(req.params)

        was_running = _is_running(req.trader_id)
        if was_running:
            stop_polling(StopPollingRequest(trader_id=req.trader_id))
            row["strategy_params"] = payload
            start_polling(_build_trader_from_db(row))

        global_log(
            f"🧠 Supervisor: parametri SUPER_ADAPTIVE applicati al trader {req.trader_id} "
            f"(versione {validated['config_version']})"
        )
        return {
            "status": "ok",
            "action": "APPLY_PARAMS",
            "trader_id": req.trader_id,
            "config_version": validated["config_version"],
            "params": validated,
            "agent_params": agent_params,
            "polling_restarted": was_running,
        }

    if action == "PAUSE":
        stop_polling(StopPollingRequest(trader_id=req.trader_id))
        global_log(f"🧠 Supervisor: PAUSA applicata al trader {req.trader_id}")
        return {"status": "ok", "action": "PAUSE", "trader_id": req.trader_id,
                "message": "Polling fermato"}

    if not row.get("selected_signal") or not row.get("selected_symbol"):
        return {"status": "ko", "message": "Trader senza segnale/simbolo configurato"}

    trader = _build_trader_from_db(row)
    start_polling(trader)
    global_log(f"🧠 Supervisor: ATTIVAZIONE applicata al trader {req.trader_id} ({trader.name})")
    return {"status": "ok", "action": "ACTIVE", "trader_id": req.trader_id,
            "message": "Polling avviato"}

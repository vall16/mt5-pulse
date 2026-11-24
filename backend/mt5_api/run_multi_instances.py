# run_multi_instances.py
# Avvia OGNI agente MT5 in un PROCESSO SEPARATO.
#
# Perche': MetaTrader5 puo' avere una sola connessione attiva per processo.
# Se 4 uvicorn girano nello stesso Python, un /init-mt5 o /login fatto su
# una porta cambia il terminale di TUTTE le altre porte (e' successo al
# trader reale su 8003, finito sul demo di 8000).
#
# Configurazione: instances.json nella stessa cartella (vedi sotto).
# Override rapido: variabile d'ambiente MT5_API_INSTANCES con JSON.

import json
import os
import subprocess
import sys
from pathlib import Path

HOST = os.environ.get("MT5_API_HOST", "0.0.0.0")

# Usato solo se non esiste instances.json e non e' impostata MT5_API_INSTANCES
DEFAULT_INSTANCES = [
    {"port": 8000, "path": r"C:\MT5_1\terminal64.exe", "name": "METAQUOTES_DEMO"},
    {"port": 8001, "path": r"C:\Program Files\MetaTrader 5 - 2\terminal64.exe", "name": "ICMARKETS_DEMO"},
    {"port": 8002, "path": r"C:\Program Files\MetaTrader 5 - 3\terminal64.exe", "name": "ICMARKETS_DEMO_2"},
    {"port": 8003, "path": r"C:\MT5_2\terminal64.exe", "name": "ICMARKETS_REAL"},
]


def _normalize(data):
    """Accetta sia una lista sia un dizionario {'instances': [...]}."""
    if isinstance(data, dict):
        data = data.get("instances", [])
    if not isinstance(data, list):
        raise ValueError("Configurazione istanze non valida: attesa una lista")

    result = []
    for item in data:
        result.append({
            "port": int(item["port"]),
            "path": str(item["path"]),
            "name": str(item.get("name", f"port_{item['port']}")),
        })
    return result


def load_instances():
    raw = os.environ.get("MT5_API_INSTANCES")
    if raw:
        return _normalize(json.loads(raw))

    cfg = Path(__file__).with_name("instances.json")
    if cfg.exists():
        return _normalize(json.loads(cfg.read_text(encoding="utf-8")))

    return DEFAULT_INSTANCES


def main():
    here = Path(__file__).resolve().parent
    main_py = here / "main.py"
    python = sys.executable

    if not main_py.exists():
        print(f"ERRORE: {main_py} non trovato")
        sys.exit(1)

    instances = load_instances()
    print(f"🚀 Avvio {len(instances)} agenti MT5 in processi separati ({HOST})")

    procs = []
    for inst in instances:
        path = inst["path"]
        port = inst["port"]
        name = inst["name"]

        if not Path(path).exists():
            print(f"⚠️  [{name}:{port}] SKIP — terminale non trovato: {path}")
            continue

        cmd = [python, str(main_py), path, f"{HOST}:{port}"]
        print(f"▶️  [{name}:{port}] {path}")

        kwargs = {"cwd": str(here)}
        if os.name == "nt" and os.environ.get("MT5_API_SAME_CONSOLE") != "1":
            kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE

        try:
            procs.append((name, port, subprocess.Popen(cmd, **kwargs)))
        except Exception as e:
            print(f"❌ [{name}:{port}] Impossibile avviare: {e}")

    if not procs:
        print("❌ Nessun agente avviato. Controlla instances.json.")
        sys.exit(1)

    print(f"\n✅ Avviati {len(procs)} processi. Chiudi le finestre o premi CTRL+C per fermarli.")

    try:
        for name, port, proc in procs:
            code = proc.wait()
            print(f"🛑 [{name}:{port}] processo terminato (exit={code})")
    except KeyboardInterrupt:
        print("\n🛑 Arresto richiesto, chiusura agenti...")
        for _, _, proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for _, _, proc in procs:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("✅ Tutti gli agenti fermati.")


if __name__ == "__main__":
    main()

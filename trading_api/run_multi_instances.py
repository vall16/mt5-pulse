# run_multi_instances.py
import asyncio
import uvicorn
import os
from importlib import import_module

# L’app da lanciare: punta al main aggiornato che legge REMOTE_MT5_API_URL da env
PROJECT_APP = "main:app"  # main.py aggiornato

# Lista di porte su cui lanciare le istanze
PORTS = [8000, 8001, 8002, 8003]

# URL remoto MT5 (puoi cambiare qui o tramite env)
REMOTE_MT5_API_URL = os.getenv("REMOTE_MT5_API_URL", "http://192.168.1.180:8000")

async def main():
    servers = []
    for port in PORTS:
        # Imposta variabile d'ambiente per ogni istanza
        os.environ["REMOTE_MT5_API_URL"] = REMOTE_MT5_API_URL
        os.environ["API_PORT"] = str(port)

        config = uvicorn.Config(
            PROJECT_APP,
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=False
        )
        server = uvicorn.Server(config)
        servers.append(server.serve())

    # Lancia tutte le istanze in parallelo
    await asyncio.gather(*servers)

if __name__ == "__main__":
    print(f"🔹 Avvio istanze TRADING_API proxy verso {REMOTE_MT5_API_URL} sulle porte {PORTS}")
    asyncio.run(main())

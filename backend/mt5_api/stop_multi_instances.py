import re
import subprocess

PORTS = [8000, 8001, 8002, 8003]


def find_pids(port):
    """Trova i PID che stanno ASCOLTANDO sulla porta (solo righe LISTENING)."""
    pids = []
    try:
        result = subprocess.check_output(
            f"netstat -ano | findstr :{port}",
            shell=True,
            text=True,
        ).strip().splitlines()
    except Exception:
        return pids

    for line in result:
        if "LISTENING" not in line.upper():
            continue
        parts = re.split(r"\s+", line.strip())
        if len(parts) >= 5 and parts[-1].isdigit():
            pid = parts[-1]
            if pid not in pids:
                pids.append(pid)

    return pids


def kill_pid(pid):
    try:
        print(f"🛑 Kill PID {pid}")
        subprocess.call(f"taskkill /F /PID {pid}", shell=True)
    except Exception as e:
        print(f"Errore uccidendo PID {pid} → {e}")


def main():
    print("🔍 Sto cercando server Uvicorn su:", PORTS)

    killed = set()
    for port in PORTS:
        pids = find_pids(port)
        if not pids:
            print(f"✔️ Porta {port} libera (nessun listener)")
            continue
        for pid in pids:
            if pid in killed:
                print(f"↪️ Porta {port}: PID {pid} gia' terminato")
                continue
            print(f"➡️ Porta {port} occupata da PID {pid} → TERMINO...")
            kill_pid(pid)
            killed.add(pid)

    print(f"\n✅ Terminati {len(killed)} processi.")


if __name__ == "__main__":
    main()

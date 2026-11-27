"""Healthcheck rapido remoto: HTTP 8080/4200 + stato servizi systemd."""
import re
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent.parent


def get_password() -> str:
    import os
    if os.environ.get("MT5_DEPLOY_PASSWORD"):
        return os.environ["MT5_DEPLOY_PASSWORD"]
    doc = ROOT / "LANCIO_REMOTO.md"
    if doc.exists():
        m = re.search(r"SSH su 183 \| `vibe` / `([^`]+)`", doc.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    sys.exit("Password SSH non trovata")


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.183"
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, username="vibe", password=get_password(), timeout=20)
    cmd = (
        'curl -fsS -o /dev/null -w "backend:%{http_code}\\n" http://127.0.0.1:8080/ ; '
        'curl -fsS -o /dev/null -w "frontend:%{http_code}\\n" http://127.0.0.1:4200/ ; '
        'systemctl is-active mt5pulse-backend mt5pulse-frontend'
    )
    _, o, e = c.exec_command(cmd)
    print(o.read().decode())
    err = e.read().decode()
    if err:
        print(err, file=sys.stderr)
    c.close()


if __name__ == "__main__":
    main()

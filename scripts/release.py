#!/usr/bin/env python3
"""Rilascio MT5Pulse senza git sul server.

Flusso:
  1. build frontend in locale (configuration production-remote)
  2. backup dello stato corrente sul server
  3. upload backend + frontend dist + deploy/ via SFTP
  4. restart dei servizi systemd
  5. healthcheck; se fallisce, restore automatico del backup

Uso (dal PC Windows, con il venv del backend):
  backend\\venv\\Scripts\\python.exe scripts\\release.py --setup   # una tantum
  backend\\venv\\Scripts\\python.exe scripts\\release.py           # rilascio
  backend\\venv\\Scripts\\python.exe scripts\\release.py --rollback

La password SSH viene letta da MT5_DEPLOY_PASSWORD oppure da LANCIO_REMOTO.md.
"""
from __future__ import annotations

import argparse
import getpass
import os
import posixpath
import re
import shlex
import stat
import subprocess
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HOST = "192.168.1.183"
DEFAULT_USER = "vibe"
DEFAULT_APP = "/home/vibe/code/mt5-pulse"
BACKUP_DIR = "/home/vibe/backups"
VENV = "/home/vibe/venvs/mt5pulse"

BACKEND_EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "mt5_api", "node_modules", ".angular"}
BACKEND_EXCLUDE_FILES = {"fxscript.log", "server_log.txt", "auto_discover_log.txt", ".env"}
BACKEND_EXCLUDE_SUFFIX = {".pyc", ".log"}


def get_password() -> str:
    if os.environ.get("MT5_DEPLOY_PASSWORD"):
        return os.environ["MT5_DEPLOY_PASSWORD"]
    doc = ROOT / "LANCIO_REMOTO.md"
    if doc.exists():
        m = re.search(r"SSH su 183 \| `vibe` / `([^`]+)`", doc.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return getpass.getpass("Password SSH: ")


class Remote:
    def __init__(self, host: str, user: str, password: str, app: str):
        self.app = app
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(host, username=user, password=password, timeout=20)
        self.sftp = self.client.open_sftp()

    def close(self):
        self.sftp.close()
        self.client.close()

    def run(self, cmd: str, sudo: bool = False, check: bool = True, timeout: int = 900) -> str:
        full = f"sudo -S -p '' bash -c {shlex.quote(cmd)}" if sudo else cmd
        print(f"\n$ {cmd}", flush=True)
        stdin, stdout, stderr = self.client.exec_command(full, timeout=timeout)
        if sudo:
            stdin.write(self.password + "\n")
            stdin.flush()
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        code = stdout.channel.recv_exit_status()
        if out.strip():
            print(out.strip(), flush=True)
        if err.strip():
            print(err.strip(), flush=True)
        if check and code != 0:
            raise RuntimeError(f"Comando fallito (exit {code}): {cmd}")
        return out

    def mkdirs(self, remote: str):
        cur = ""
        for part in remote.strip("/").split("/"):
            cur += "/" + part
            try:
                self.sftp.stat(cur)
            except FileNotFoundError:
                self.sftp.mkdir(cur)

    def upload_dir(self, local: Path, remote: str, exclude_dirs=None, exclude_files=None, exclude_suffix=None):
        exclude_dirs = exclude_dirs or set()
        exclude_files = exclude_files or set()
        exclude_suffix = exclude_suffix or set()
        self.mkdirs(remote)
        for item in sorted(local.iterdir()):
            if item.is_dir():
                if item.name in exclude_dirs:
                    continue
                self.upload_dir(item, posixpath.join(remote, item.name), exclude_dirs, exclude_files, exclude_suffix)
            else:
                if item.name in exclude_files or item.suffix in exclude_suffix:
                    continue
                self.sftp.put(str(item), posixpath.join(remote, item.name))

    def rm_tree(self, remote: str):
        try:
            entries = self.sftp.listdir_attr(remote)
        except FileNotFoundError:
            return
        for e in entries:
            r = posixpath.join(remote, e.filename)
            if stat.S_ISDIR(e.st_mode):
                self.rm_tree(r)
            else:
                self.sftp.remove(r)
        self.sftp.rmdir(remote)


def build_frontend():
    print("==> Build frontend locale (production-remote)", flush=True)
    subprocess.run(
        "npm run build -- --configuration production-remote",
        cwd=ROOT / "frontend",
        shell=True,
        check=True,
    )


def healthcheck(r: Remote) -> bool:
    out = r.run(
        "curl -fsS http://127.0.0.1:8080/ >/dev/null && curl -fsS -o /dev/null http://127.0.0.1:4200/ && echo HEALTHY || echo UNHEALTHY",
        check=False,
        timeout=60,
    )
    return "HEALTHY" in out


def wait_healthy(r: Remote, seconds: int = 60) -> bool:
    for _ in range(seconds):
        if healthcheck(r):
            return True
        time.sleep(1)
    return False


def backup(r: Remote) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = f"{BACKUP_DIR}/mt5-pulse-{ts}.tgz"
    r.run(f"mkdir -p {BACKUP_DIR}")
    r.run(
        f"tar czf {path} -C {r.app} "
        "--exclude=backend/venv --exclude=__pycache__ --exclude='*.pyc' --exclude='*.log' "
        "backend frontend/dist deploy"
    )
    print(f"==> Backup: {path}", flush=True)
    return path


def latest_backup(r: Remote) -> str | None:
    out = r.run(f"ls -1t {BACKUP_DIR}/mt5-pulse-*.tgz 2>/dev/null | head -1", check=False)
    return out.strip() or None


def restore(r: Remote, path: str):
    print(f"==> Restore da {path}", flush=True)
    r.run(f"tar xzf {path} -C {r.app}")


def restart(r: Remote):
    r.run("systemctl restart mt5pulse-backend mt5pulse-frontend", sudo=True)


def upload_app(r: Remote):
    print("==> Upload backend", flush=True)
    r.upload_dir(
        ROOT / "backend",
        f"{r.app}/backend",
        exclude_dirs=BACKEND_EXCLUDE_DIRS,
        exclude_files=BACKEND_EXCLUDE_FILES,
        exclude_suffix=BACKEND_EXCLUDE_SUFFIX,
    )
    print("==> Upload deploy/", flush=True)
    r.upload_dir(ROOT / "deploy", f"{r.app}/deploy")
    print("==> Upload frontend dist", flush=True)
    browser = ROOT / "frontend" / "dist" / "demo" / "browser"
    if not browser.exists():
        raise RuntimeError("Build frontend mancante: eseguire prima la build")
    remote_browser = f"{r.app}/frontend/dist/demo/browser"
    r.rm_tree(remote_browser)
    r.upload_dir(browser, remote_browser)


def install_deps(r: Remote):
    r.run(f"{VENV}/bin/pip install -q --disable-pip-version-check --upgrade --requirement {r.app}/backend/requirements.txt")


def setup(r: Remote):
    upload_app(r)

    print("==> Creo venv backend (se manca)", flush=True)
    r.run(f"mkdir -p {posixpath.dirname(VENV)}")
    out = r.run(f"test -x {VENV}/bin/python && echo yes || echo no", check=False)
    if "no" in out:
        r.run(f"python3 -m venv {VENV}", check=False)
        out = r.run(f"test -x {VENV}/bin/python && echo yes || echo no", check=False)
        if "no" in out:
            r.run("apt-get update && apt-get install -y python3-venv", sudo=True)
            r.run(f"python3 -m venv {VENV}")

    install_deps(r)

    print("==> Installo unit systemd", flush=True)
    for unit in ("mt5pulse-backend.service", "mt5pulse-frontend.service"):
        r.run(f"install -m 0644 {r.app}/deploy/systemd/{unit} /etc/systemd/system/{unit}", sudo=True)
    r.run("systemctl daemon-reload", sudo=True)
    r.run("systemctl enable mt5pulse-backend mt5pulse-frontend", sudo=True)

    print("==> Configuro sudoers per il restart", flush=True)
    r.run(
        "printf '%s\\n' 'vibe ALL=(root) NOPASSWD: /usr/bin/systemctl restart mt5pulse-backend, /usr/bin/systemctl restart mt5pulse-frontend' "
        "> /etc/sudoers.d/mt5pulse && chmod 440 /etc/sudoers.d/mt5pulse && visudo -cf /etc/sudoers.d/mt5pulse",
        sudo=True,
    )

    print("==> Fermo eventuali processi manuali", flush=True)
    r.run("pkill -f '^python3 main.py' || true", check=False)
    r.run("pkill -f '^python3 spa_server.py' || true", check=False)

    r.run("systemctl start mt5pulse-backend mt5pulse-frontend", sudo=True)
    if not wait_healthy(r):
        raise RuntimeError("Setup completato ma healthcheck fallito")
    print("==> Setup OK", flush=True)


def release(r: Remote, skip_build: bool):
    if not skip_build:
        build_frontend()
    path = backup(r)
    upload_app(r)
    install_deps(r)
    restart(r)
    if wait_healthy(r):
        print("==> Rilascio OK", flush=True)
        return
    print("!! Healthcheck fallito: rollback automatico", flush=True)
    restore(r, path)
    restart(r)
    wait_healthy(r)
    raise RuntimeError("Rilascio fallito, rollback eseguito")


def rollback(r: Remote):
    path = latest_backup(r)
    if not path:
        raise RuntimeError("Nessun backup disponibile")
    restore(r, path)
    install_deps(r)
    restart(r)
    if not wait_healthy(r):
        raise RuntimeError("Rollback eseguito ma healthcheck fallito")
    print(f"==> Rollback OK da {path}", flush=True)


def main():
    p = argparse.ArgumentParser(description="Rilascio MT5Pulse senza git")
    p.add_argument("--setup", action="store_true", help="installazione una tantum sul server")
    p.add_argument("--rollback", action="store_true", help="ripristina l'ultimo backup")
    p.add_argument("--skip-build", action="store_true", help="non ricostruire il frontend")
    p.add_argument("--host", default=os.environ.get("MT5_DEPLOY_HOST", DEFAULT_HOST))
    p.add_argument("--user", default=os.environ.get("MT5_DEPLOY_USER", DEFAULT_USER))
    p.add_argument("--app", default=os.environ.get("MT5_DEPLOY_APP", DEFAULT_APP))
    args = p.parse_args()

    r = Remote(args.host, args.user, get_password(), args.app)
    try:
        if args.setup:
            setup(r)
        elif args.rollback:
            rollback(r)
        else:
            release(r, args.skip_build)
    finally:
        r.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        sys.exit(1)

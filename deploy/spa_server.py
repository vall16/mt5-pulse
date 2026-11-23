"""Server statico per la SPA Angular buildata, con fallback su index.html.

Usato dal servizio systemd mt5pulse-frontend. La root viene da
MT5PULSE_WEB_ROOT (default: frontend/dist/demo/browser).
"""
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(
    os.environ.get(
        "MT5PULSE_WEB_ROOT",
        "/home/vibe/code/mt5-pulse/frontend/dist/demo/browser",
    )
).resolve()
HOST = os.environ.get("MT5PULSE_FRONTEND_HOST", "0.0.0.0")
PORT = int(os.environ.get("MT5PULSE_FRONTEND_PORT", "4200"))


class SPAHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _fallback_to_index(self) -> None:
        requested = unquote(urlsplit(self.path).path)
        target = (ROOT / requested.lstrip("/")).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self.send_error(403)
            return
        if not target.exists() and "." not in Path(requested).name:
            self.path = "/index.html"

    def do_GET(self):
        self._fallback_to_index()
        super().do_GET()

    def do_HEAD(self):
        self._fallback_to_index()
        super().do_HEAD()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    if not (ROOT / "index.html").is_file():
        raise SystemExit(
            f"index.html non trovato in {ROOT}: eseguire prima la build del frontend"
        )
    print(f"MT5Pulse frontend: {ROOT} -> http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), SPAHandler).serve_forever()


if __name__ == "__main__":
    main()

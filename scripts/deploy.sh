#!/usr/bin/env bash
# Deploy MT5Pulse sul server Ubuntu (192.168.1.183).
#
# Uso:
#   ./scripts/deploy.sh                # deploy di origin/main
#   ./scripts/deploy.sh rollback       # torna al commit precedente
#   ./scripts/deploy.sh rollback <SHA> # torna a uno specifico
#
# Variabili opzionali:
#   APP_DIR, BRANCH, BACKEND_SERVICE, FRONTEND_SERVICE, STATE_DIR
set -euo pipefail

APP_DIR="${APP_DIR:-/home/vibe/code/mt5-pulse}"
BRANCH="${BRANCH:-main}"
BACKEND_SERVICE="${BACKEND_SERVICE:-mt5pulse-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-mt5pulse-frontend}"
STATE_DIR="${STATE_DIR:-$HOME/.local/state/mt5pulse}"
SUDO=(sudo -n)

log()  { echo "==> $*"; }
die()  { echo "ERRORE: $*" >&2; exit 1; }

cd "$APP_DIR"

command -v git  >/dev/null || die "git non trovato"
command -v curl >/dev/null || die "curl non trovato"

snapshot_previous() {
  mkdir -p "$STATE_DIR"
  printf '%s\n' "$1" > "$STATE_DIR/previous_sha"
}

previous_sha() {
  [ -f "$STATE_DIR/previous_sha" ] && cat "$STATE_DIR/previous_sha" || true
}

install_backend() {
  log "Installo dipendenze backend (requirements.txt)"
  "$APP_DIR/backend/venv/bin/pip" install --upgrade --requirement "$APP_DIR/backend/requirements.txt"
}

build_frontend() {
  local changed="${1:-}"
  log "Build frontend (configuration production-remote)"
  cd "$APP_DIR/frontend"
  command -v npm >/dev/null || die "npm non trovato"

  if [ ! -d node_modules ] || printf '%s\n' "$changed" | grep -Eq '^frontend/package(-lock)?\.json$'; then
    log "npm ci (dipendenze frontend cambiate o node_modules assente)"
    npm ci --no-audit --no-fund
  fi

  npm run build -- --configuration production-remote
  cd "$APP_DIR"
}

restart_services() {
  log "Riavvio $BACKEND_SERVICE e $FRONTEND_SERVICE"
  "${SUDO[@]}" systemctl restart "$BACKEND_SERVICE" "$FRONTEND_SERVICE"
}

healthcheck() {
  local i
  for i in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8080/ >/dev/null 2>&1 \
       && curl -fsS -o /dev/null http://127.0.0.1:4200/; then
      return 0
    fi
    sleep 1
  done
  return 1
}

rollback() {
  local target="${1:-}"
  if [ -z "$target" ]; then
    target="$(previous_sha)"
  fi
  [ -n "$target" ] || die "nessuno SHA di rollback disponibile"

  log "Rollback a $target"
  git fetch origin "$BRANCH" --prune || true
  git reset --hard "$target"
  install_backend
  build_frontend ""
  restart_services
  healthcheck || die "healthcheck fallito dopo il rollback"
  log "Rollback completato: $target"
}

deploy() {
  local before after changed prev

  [ -z "$(git status --porcelain --untracked-files=no)" ] \
    || die "ci sono modifiche locali tracciate: pulire il clone prima del deploy"

  log "Deploy di origin/$BRANCH in $APP_DIR"
  before="$(git rev-parse HEAD)"
  git fetch origin "$BRANCH" --prune
  git pull --ff-only origin "$BRANCH"
  after="$(git rev-parse HEAD)"

  if [ "$before" = "$after" ]; then
    log "Repo già allineato a $after"
  else
    snapshot_previous "$before"
  fi
  changed="$(git diff --name-only "$before" "$after" || true)"

  if [ ! -x "$APP_DIR/backend/venv/bin/python" ] \
     || printf '%s\n' "$changed" | grep -qx 'backend/requirements.txt'; then
    install_backend
  fi

  if [ ! -d "$APP_DIR/frontend/node_modules" ] \
     || printf '%s\n' "$changed" | grep -Eq '^frontend/'; then
    build_frontend "$changed"
  fi

  restart_services

  if healthcheck; then
    log "Deploy completato: $after"
  else
    echo "Healthcheck fallito." >&2
    prev="$(previous_sha)"
    if [ -n "$prev" ] && [ "$prev" != "$after" ]; then
      rollback "$prev"
    fi
    die "deploy fallito"
  fi
}

case "${1:-deploy}" in
  deploy)   deploy ;;
  rollback) rollback "${2:-}" ;;
  *) echo "Uso: $0 [deploy|rollback [SHA]]" >&2; exit 2 ;;
esac

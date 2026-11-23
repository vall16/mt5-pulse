# Rilascio MT5Pulse sul server

Obiettivo: **un solo file da lanciare (`rilascia.bat`), procedura stabilita una volta per tutte, rollback sicuro**. Sul server remoto (`192.168.1.183`) **non si usa git né Docker**: i file vengono caricati via SFTP e backend/frontend sono servizi systemd.

## Rilascio (procedura unica)

Dal PC Windows, **doppio click su `rilascia.bat`** nella root del progetto (oppure da terminale):

```bat
rilascia.bat              :: build + upload + restart + healthcheck (+ rollback automatico se fallisce)
rilascia.bat --rollback   :: ripristina l'ultimo backup
rilascia.bat --setup      :: installazione una tantum sul server (già eseguito il 2026-11-23)
rilascia.bat --skip-build :: rilascio senza ricostruire il frontend
```

`rilascia.bat` è solo l'ingresso: tutta la logica sta in `scripts/release.py`.

## File coinvolti

| File | Ruolo |
|---|---|
| `rilascia.bat` | **punto di ingresso unico** del rilascio |
| `scripts/release.py` | build locale + upload SFTP + restart systemd + healthcheck + rollback |
| `deploy/systemd/*.service` | unit per backend e frontend |
| `deploy/spa_server.py` | server statico della SPA, con fallback `index.html` |
| `frontend/src/environments/environment.remote.ts` | URL del backend remoto, usato dalla build `production-remote` |
| `scripts/start_mt5_api.bat` | riavvio agenti MT5 sulla macchina Windows |

Il `.env` del server è **specifico del server** e non viene mai sovrascritto dal rilascio (escluso dall'upload). Sul server deve contenere:

```text
API_HOST=0.0.0.0
API_PORT=8080
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200,http://192.168.1.183:4200
```

## Requisiti sul PC Windows

- Node/npm per la build Angular.
- Il venv del backend con `paramiko` (già presente in `backend\venv`).
- Password SSH: letta da `MT5_DEPLOY_PASSWORD`, oppure da `LANCIO_REMOTO.md`, oppure chiesta interattivamente.

---

## 1. Setup una tantum (già eseguito il 2026-11-23)

```bat
rilascia.bat --setup
```

`--setup` fa tutto:

1. carica `backend/`, `deploy/` e la build del frontend sul server;
2. crea il venv Python in `/home/vibe/venvs/mt5pulse` (fuori dalla cartella app, che è su filesystem senza permessi symlink) e installa `backend/requirements.txt`;
3. installa e abilita le unit systemd `mt5pulse-backend` e `mt5pulse-frontend`;
4. crea `/etc/sudoers.d/mt5pulse` (NOPASSWD solo per il restart dei due servizi);
5. ferma eventuali processi manuali residui (`python3 main.py`, `spa_server.py`) e avvia i servizi;
6. healthcheck su `:8080` e `:4200`.

Verifica:

```bash
ssh vibe@192.168.1.183
systemctl status mt5pulse-backend mt5pulse-frontend
curl http://127.0.0.1:8080/
curl http://127.0.0.1:4200/
```

---

## 2. Rilascio normale

Dal PC Windows, nella root del progetto:

```bat
rilascia.bat
```

`release.py` esegue, in ordine:

1. `npm run build -- --configuration production-remote` in locale (il bundle punta a `http://192.168.1.183:8080`);
2. **backup** dello stato corrente sul server in `/home/vibe/backups/mt5-pulse-<timestamp>.tgz` (backend + dist + deploy, esclusi venv e log);
3. upload via SFTP di `backend/` (esclusi venv, log, `mt5_api/`, `.env`), `deploy/` e `frontend/dist/demo/browser`;
4. `pip install -r requirements.txt` nel venv del server (idempotente);
5. restart dei due servizi systemd;
6. healthcheck su `:8080` e `:4200` per 60 secondi;
7. se il healthcheck fallisce, **restore automatico del backup** e restart.

Opzioni:

- `--skip-build`: riusa la build locale esistente (utile se hai già buildato);
- `--host`, `--user`, `--app`: override di destinazione (default `192.168.1.183`, `vibe`, `/home/vibe/code/mt5-pulse`).

La build Docker locale continua a usare la configurazione `production` invariata (`127.0.0.1:8080`).

---

## 3. Rollback manuale

```bat
rilascia.bat --rollback
```

Ripristina l'ultimo backup disponibile in `/home/vibe/backups/`, reinstalla i requirements e riavvia i servizi.

> Nota: il restore sovrascrive i file presenti nel backup; eventuali file *nuovi* introdotti da un rilascio fallito non vengono rimossi automaticamente.

---

## 4. Log e diagnostica

```bash
journalctl -u mt5pulse-backend -f
journalctl -u mt5pulse-frontend -f
systemctl status mt5pulse-backend mt5pulse-frontend
```

Il backend impiega ~15 secondi ad avviarsi sul Raspberry (import pandas/numpy + migrazioni DB): è normale.

---

## 5. Agenti MT5 su `192.168.1.180` (Windows)

Le modifiche a `backend/mt5_api/` **non** si propagano da sole: sulla macchina Windows aggiorna i file e lancia:

```bat
scripts\start_mt5_api.bat
```

Lo script ferma le istanze sulle porte 8000-8003 e le riavvia. Ricorda poi `/init-mt5` e `/login` se i terminali sono stati chiusi.

---

## 6. Database

All'avvio il backend esegue `run_migrations()` (aggiunta colonne mancanti). Se la modifica crea **nuove tabelle**, applica lo SQL manualmente su MySQL prima del rilascio.

---

## 7. Perché non GitHub Actions / git sul server

`192.168.1.183` è un IP privato della LAN: i runner GitHub pubblici non lo raggiungono, e si è scelto di non tenere un clone git sul server. Il rilascio è quindi push-based dal PC Windows (`release.py`). Per automatizzarlo servirebbe un runner/self-hosted dentro la LAN che esegua lo stesso comando.

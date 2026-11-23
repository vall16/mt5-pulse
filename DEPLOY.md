# Rilascio MT5Pulse sul server

Obiettivo: **una sorgente di verità (`main` su GitHub), un comando di deploy, rollback sicuro**. Sul server remoto **non si usa Docker**: backend e frontend sono servizi systemd.

## File coinvolti

| File | Ruolo |
|---|---|
| `scripts/deploy.sh` | deploy/rollback idempotente sul server Ubuntu |
| `scripts/install_server.sh` | installazione una tantum delle unit systemd |
| `deploy/systemd/*.service` | unit per backend e frontend |
| `deploy/spa_server.py` | server statico della SPA, con fallback `index.html` |
| `frontend/src/environments/environment.remote.ts` | URL del backend remoto, usato dalla build `production-remote` |
| `scripts/start_mt5_api.bat` | riavvio agenti MT5 sulla macchina Windows |

I file `.env` restano **fuori da git** (`.gitignore`) e non vengono mai sovrascritti dal deploy.

---

## 1. Setup una tantum su `192.168.1.183`

Se il clone non esiste ancora:

```bash
ssh vibe@192.168.1.183
git clone https://github.com/vall16/mt5-pulse.git /home/vibe/code/mt5-pulse
cd /home/vibe/code/mt5-pulse/backend
python3 -m venv venv
```

Installa le unit systemd e abilitale all'avvio:

```bash
cd /home/vibe/code/mt5-pulse
./scripts/install_server.sh
sudo systemctl start mt5pulse-backend mt5pulse-frontend
```

Consenti all'utente `vibe` di riavviare **solo** i due servizi:

```bash
sudo visudo -f /etc/sudoers.d/mt5pulse
```

```text
vibe ALL=(root) NOPASSWD: /usr/bin/systemctl restart mt5pulse-backend, /usr/bin/systemctl restart mt5pulse-frontend
```

Verifica iniziale:

```bash
systemctl status mt5pulse-backend mt5pulse-frontend
curl http://127.0.0.1:8080/
curl http://127.0.0.1:4200/
```

> Il vecchio `frontend/spa_server.py` eventualmente presente sul server non viene toccato: la nuova unit usa `deploy/spa_server.py`, che è versionato.

---

## 2. Rilascio normale

Dal tuo PC Windows:

```bat
git push origin main
ssh vibe@192.168.1.183 "cd /home/vibe/code/mt5-pulse && ./scripts/deploy.sh"
```

`deploy.sh` esegue, in ordine:

1. rifiuta il deploy se il clone sul server ha modifiche tracciate;
2. `git fetch` + `git pull --ff-only origin main`;
3. salva lo SHA precedente in `~/.local/state/mt5pulse/previous_sha`;
4. reinstalla i requirements solo se `backend/requirements.txt` è cambiato;
5. esegue `npm ci` se sono cambiati i file lock, poi `npm run build -- --configuration production-remote`;
6. riavvia i due servizi systemd;
7. fa healthcheck su `:8080` e `:4200` per 30 secondi;
8. se il healthcheck fallisce, **fa automaticamente rollback** allo SHA precedente.

Il frontend remoto usa `environment.remote.ts` (`http://192.168.1.183:8080`): niente più `sed` sui file buildati. La build Docker locale continua a usare la configurazione `production` invariata.

---

## 3. Rollback manuale

```bash
ssh vibe@192.168.1.183 "cd /home/vibe/code/mt5-pulse && ./scripts/deploy.sh rollback"
```

Oppure verso un commit specifico:

```bash
ssh vibe@192.168.1.183 "cd /home/vibe/code/mt5-pulse && ./scripts/deploy.sh rollback <SHA>"
```

---

## 4. Log e diagnostica

```bash
journalctl -u mt5pulse-backend -f
journalctl -u mt5pulse-frontend -f
systemctl status mt5pulse-backend mt5pulse-frontend
```

---

## 5. Agenti MT5 su `192.168.1.180` (Windows)

Le modifiche a `backend/mt5_api/` **non** si propagano da sole: sulla macchina Windows:

```bat
cd C:\Users\vallo\mt5-pulse
git pull origin main
scripts\start_mt5_api.bat
```

Lo script ferma le istanze sulle porte 8000-8003 e le riavvia. Ricorda poi `/init-mt5` e `/login` se i terminali sono stati chiusi.

---

## 6. Database

All'avvio il backend esegue `run_migrations()` (aggiunta colonne mancanti). Se la modifica crea **nuove tabelle**, applica lo SQL manualmente su MySQL prima del deploy.

---

## 7. Perché non ho messo GitHub Actions

`192.168.1.183` è un IP privato: i runner GitHub pubblici non possono raggiungerlo via SSH. Il comando di deploy resta identico; per automatizzarlo servirebbe un **self-hosted runner** dentro la LAN che esegua lo stesso `ssh ... ./scripts/deploy.sh`.

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.183', username='vibe', password='vibe2025')

cmds = [
    ('Python', 'which python3 && python3 --version'),
    ('Venv', 'ls /home/vibe/code/mt5-pulse/backend/venv/bin/python 2>/dev/null || echo NO_VENV'),
    ('Deps', 'cd /home/vibe/code/mt5-pulse/backend && python3 -c "import fastapi, uvicorn, pymysql; print(\'deps_ok\')" 2>&1 || echo DEPS_MISSING'),
    ('MySQL', 'mysql -u trader -pvibe2025 -e "SELECT 1" 2>&1 || echo MYSQL_FAIL'),
    ('Port 8080', 'ss -tlnp | grep 8080 || echo PORT_FREE'),
]

for label, cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"=== {label} ===")
    print(out if out else "(empty)")
    if err:
        print(f"STDERR: {err}")
    print()

ssh.close()
print("DONE")

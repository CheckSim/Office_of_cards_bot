# Guida al Deployment

Diverse opzioni per mettere in produzione il bot.

## 🖥️ Opzione 1: Server Linux (VPS/Dedicated)

### Setup iniziale

```bash
# 1. Clona/copia i file sul server
scp -r * user@server:/opt/office-cards-bot/

# 2. Connettiti al server
ssh user@server

# 3. Vai nella directory
cd /opt/office-cards-bot

# 4. Installa Python 3.9+ se necessario
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 5. Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Installa dipendenze
pip install -r requirements.txt

# 7. Configura .env
cp .env.example .env
nano .env  # Inserisci i tuoi token
```

### Avvio manuale

```bash
# Avvio semplice
python bot.py

# Con log su file
python bot.py > bot.log 2>&1 &

# Usando lo script di avvio
chmod +x run.sh
./run.sh
```

### Avvio automatico con systemd

```bash
# 1. Copia il file service
sudo cp office-cards-bot.service /etc/systemd/system/

# 2. Modifica il file con i tuoi percorsi
sudo nano /etc/systemd/system/office-cards-bot.service
# Cambia:
# - User=your_username
# - WorkingDirectory=/path/to/bot
# - ExecStart=/path/to/bot/venv/bin/python3 /path/to/bot/bot.py
# - ReadWritePaths=/path/to/bot/data

# 3. Abilita e avvia il service
sudo systemctl daemon-reload
sudo systemctl enable office-cards-bot
sudo systemctl start office-cards-bot

# 4. Controlla lo stato
sudo systemctl status office-cards-bot

# 5. Vedi i log
sudo journalctl -u office-cards-bot -f
```

### Comandi utili systemd

```bash
# Start
sudo systemctl start office-cards-bot

# Stop
sudo systemctl stop office-cards-bot

# Restart
sudo systemctl restart office-cards-bot

# Status
sudo systemctl status office-cards-bot

# Logs in tempo reale
sudo journalctl -u office-cards-bot -f

# Disable avvio automatico
sudo systemctl disable office-cards-bot
```

## 🐳 Opzione 2: Docker

### Build e run

```bash
# 1. Build image
docker build -t office-cards-bot .

# 2. Run container
docker run -d \
  --name office-cards-bot \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  office-cards-bot

# 3. Vedi logs
docker logs -f office-cards-bot

# 4. Stop container
docker stop office-cards-bot

# 5. Restart
docker restart office-cards-bot
```

### Docker Compose

Crea `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: office-cards-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    environment:
      - TZ=Europe/Rome
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Poi:

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build
```

## ☁️ Opzione 3: Cloud Hosting

### Heroku

```bash
# 1. Installa Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# 2. Login
heroku login

# 3. Crea app
heroku create office-cards-bot

# 4. Configura variabili d'ambiente
heroku config:set BOT_TOKEN=your_token
heroku config:set SPOTIFY_CLIENT_ID=your_id
heroku config:set SPOTIFY_CLIENT_SECRET=your_secret
heroku config:set ADMIN_CHAT_ID=your_chat_id

# 5. Crea Procfile
echo "worker: python bot.py" > Procfile

# 6. Deploy
git init
git add .
git commit -m "Initial commit"
git push heroku main

# 7. Scale worker
heroku ps:scale worker=1

# 8. Logs
heroku logs --tail
```

### Railway

1. Vai su [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Seleziona il tuo repository
4. Aggiungi variabili d'ambiente nel dashboard
5. Railway detecta automaticamente Python e installa dipendenze
6. Il bot parte automaticamente

### Render

1. Vai su [render.com](https://render.com)
2. Click "New" → "Background Worker"
3. Connetti GitHub repository
4. Configura:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
5. Aggiungi variabili d'ambiente
6. Deploy

### DigitalOcean App Platform

```bash
# 1. Installa doctl
# https://docs.digitalocean.com/reference/doctl/how-to/install/

# 2. Autenticazione
doctl auth init

# 3. Crea app spec file
cat > .do/app.yaml <<EOF
name: office-cards-bot
services:
- name: bot
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python bot.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: BOT_TOKEN
    scope: RUN_TIME
    value: your_token
  - key: SPOTIFY_CLIENT_ID
    scope: RUN_TIME
    value: your_id
  - key: SPOTIFY_CLIENT_SECRET
    scope: RUN_TIME
    value: your_secret
EOF

# 4. Deploy
doctl apps create --spec .do/app.yaml
```

## 🔄 Opzione 4: Screen/tmux (Temporaneo)

Buono per testing, non per produzione.

### Screen

```bash
# Avvia screen
screen -S office-cards-bot

# Attiva venv e avvia bot
source venv/bin/activate
python bot.py

# Detach (Ctrl+A poi D)

# Riattacca
screen -r office-cards-bot

# Lista screen
screen -ls

# Termina
screen -X -S office-cards-bot quit
```

### Tmux

```bash
# Nuova sessione
tmux new -s office-cards-bot

# Avvia bot
source venv/bin/activate
python bot.py

# Detach (Ctrl+B poi D)

# Riattacca
tmux attach -t office-cards-bot

# Lista sessioni
tmux ls

# Termina
tmux kill-session -t office-cards-bot
```

## 📊 Monitoring

### Log rotation (Linux)

Crea `/etc/logrotate.d/office-cards-bot`:

```
/opt/office-cards-bot/bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### Health check script

Crea `health_check.sh`:

```bash
#!/bin/bash

if ! pgrep -f "python.*bot.py" > /dev/null; then
    echo "Bot non in esecuzione! Riavvio..."
    systemctl restart office-cards-bot
    
    # Notifica admin (opzionale)
    curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
         -d "chat_id=$ADMIN_CHAT_ID" \
         -d "text=⚠️ Bot riavviato automaticamente"
fi
```

Aggiungi a crontab:

```bash
crontab -e
# Aggiungi:
*/5 * * * * /opt/office-cards-bot/health_check.sh
```

## 🔒 Sicurezza

1. **Non committare .env su Git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Usa variabili d'ambiente sicure**
   - Heroku: Config Vars
   - Docker: secrets
   - Server: file .env con permessi 600

3. **Firewall** (se su VPS)
   ```bash
   sudo ufw allow ssh
   sudo ufw enable
   ```

4. **Backup automatico**
   ```bash
   # Crontab backup giornaliero
   0 3 * * * tar -czf /backup/office-cards-$(date +\%Y\%m\%d).tar.gz /opt/office-cards-bot/data/
   ```

## 🐛 Troubleshooting

### Bot non parte

```bash
# Controlla logs
tail -f bot.log

# Verifica variabili d'ambiente
cat .env

# Test manuale
python bot.py

# Controlla permessi
ls -la data/
chmod 755 data/
```

### Memoria alta

```bash
# Controlla uso memoria
ps aux | grep python

# Limita con systemd
# In .service file aggiungi:
# MemoryMax=512M
# MemoryHigh=400M
```

### CSV corrotto

```bash
# Backup
cp data/db.csv data/db.csv.backup

# Verifica encoding
file -I data/db.csv

# Riparazione base
python -c "import pandas as pd; df = pd.read_csv('data/db.csv'); df.to_csv('data/db_fixed.csv', index=False)"
```
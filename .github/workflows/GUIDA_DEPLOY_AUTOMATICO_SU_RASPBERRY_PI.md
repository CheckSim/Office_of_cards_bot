# Guida: Deploy Automatico da GitHub a Raspberry Pi

Questa guida ti aiuterà a configurare un sistema di deploy automatico che fa il push del codice da GitHub al tuo Raspberry Pi ogni volta che fai un commit.

## 📋 Prerequisiti

- Un Raspberry Pi con Raspberry Pi OS installato
- Accesso SSH al Raspberry Pi
- Un account GitHub
- Connessione internet sul Raspberry Pi

## ⚠️ Nota per Raspberry Pi 2

Se hai un **Raspberry Pi 2 v1.1** (1GB RAM, 32-bit):
- Usa **Raspberry Pi OS Lite (32-bit, Legacy)**
- Evita Docker quando possibile (molto pesante su 1GB RAM)
- **Preferisci PM2 per Node.js e systemd per Python**
- Limita a 1-2 progetti contemporaneamente
- Aggiungi swap (vedi sezione "Ottimizzazioni per Raspberry Pi 2")

Se hai un **Raspberry Pi 4/5**:
- Usa **Raspberry Pi OS Lite (64-bit)**
- Docker funzionerà senza problemi
- Puoi gestire più progetti contemporaneamente

---

## 🔧 Parte 1: Configurazione del Raspberry Pi

### 1.1 Connessione SSH

Assicurati di avere SSH abilitato sul Pi. Se non lo hai ancora fatto:

```bash
sudo raspi-config
# Vai su: Interface Options → SSH → Enable
```

Prendi nota dell'indirizzo IP del tuo Raspberry Pi:

```bash
hostname -I
```

### 1.2 Aggiornamento del sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.3 Installazione delle dipendenze base

```bash
# Git (probabilmente già installato)
sudo apt install git -y

# Node.js e PM2 (CONSIGLIATO per Raspberry Pi 2)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Python e venv (CONSIGLIATO per Raspberry Pi 2)
sudo apt install python3-pip python3-venv -y

# Docker e Docker Compose (SOLO per Raspberry Pi 4/5 con 2GB+ RAM)
# ⚠️ SCONSIGLIATO per Raspberry Pi 2 (troppo pesante)
# Se hai un Pi 2, salta questa sezione
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**IMPORTANTE:** Dopo aver installato Docker (solo Pi 4/5), fai logout e login per applicare i permessi:

```bash
exit
# Riconnettiti via SSH
```

### 1.4 Creazione della directory per i progetti

```bash
mkdir -p ~/projects
cd ~/projects
```

### 1.5 Configurazione chiavi SSH per GitHub

Genera una coppia di chiavi SSH sul Raspberry Pi:

```bash
ssh-keygen -t ed25519 -C "github-deploy"
# Premi Enter per accettare il path predefinito (~/.ssh/id_ed25519)
# Premi Enter due volte per non impostare una passphrase
```

Visualizza la chiave pubblica:

```bash
cat ~/.ssh/id_ed25519.pub
```

Copia l'output (inizia con `ssh-ed25519`).

### 1.6 Aggiungi la chiave pubblica a GitHub

1. Vai su GitHub.com
2. Clicca sulla tua foto profilo → **Settings**
3. Nel menu a sinistra: **SSH and GPG keys**
4. Clicca **New SSH key**
5. Inserisci:
   - **Title**: `Raspberry Pi Deploy`
   - **Key**: incolla la chiave pubblica copiata prima
6. Clicca **Add SSH key**

### 1.7 Testa la connessione SSH con GitHub

```bash
ssh -T git@github.com
```

Dovresti vedere: `Hi username! You've successfully authenticated...`

---

## 🔐 Parte 2: Configurazione dei Secrets su GitHub

### 2.1 Preparazione della chiave privata

Sul Raspberry Pi, visualizza la chiave privata:

```bash
cat ~/.ssh/id_ed25519
```

Copia **tutto** l'output (inizia con `-----BEGIN OPENSSH PRIVATE KEY-----` e finisce con `-----END OPENSSH PRIVATE KEY-----`).

### 2.2 Creazione dei secrets sul repository GitHub

Per ogni progetto che vuoi deployare:

1. Vai sul repository GitHub del progetto
2. Clicca su **Settings**
3. Nel menu a sinistra: **Secrets and variables** → **Actions**
4. Clicca **New repository secret**

Crea i seguenti secrets:

#### Secret: `SSH_HOST`
- **Name**: `SSH_HOST`
- **Value**: L'indirizzo IP del tuo Raspberry Pi (es. `192.168.1.100`)

**Nota**: Se non hai un IP statico, considera di usare un servizio DynDNS come DuckDNS o No-IP.

#### Secret: `SSH_USER`
- **Name**: `SSH_USER`
- **Value**: Il tuo username sul Pi (solitamente `pi`)

#### Secret: `SSH_PRIVATE_KEY`
- **Name**: `SSH_PRIVATE_KEY`
- **Value**: Incolla la chiave privata copiata prima (inclusi BEGIN e END)

#### Secret: `SSH_PORT` (opzionale)
- **Name**: `SSH_PORT`
- **Value**: `22` (o la porta SSH personalizzata se l'hai cambiata)

#### Secret: `ENV_FILE` (se il progetto ha bisogno di variabili d'ambiente)
- **Name**: `ENV_FILE`
- **Value**: Il contenuto del tuo file `.env`

**Esempio per un bot Telegram:**
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
NODE_ENV=production
PORT=3000
```

---

## 📝 Parte 3: Aggiunta del Workflow al Progetto

### 3.1 Crea la cartella del workflow

Nel tuo progetto locale (sul tuo computer), crea la cartella:

```bash
mkdir -p .github/workflows
```

### 3.2 Crea il file del workflow

Crea il file `.github/workflows/deploy.yml` e incolla il template del workflow.

### 3.3 Commit e push

```bash
git add .github/workflows/deploy.yml
git commit -m "Add automatic deployment workflow"
git push origin main
```

---

## 🚀 Parte 4: Test del Deploy

### 4.1 Verifica che il workflow sia partito

1. Vai sul tuo repository GitHub
2. Clicca sulla tab **Actions**
3. Dovresti vedere il workflow "Deploy to Raspberry Pi" in esecuzione

### 4.2 Monitora l'esecuzione

Clicca sul workflow per vedere i log in tempo reale. Il processo:

1. ✅ Si connette al Raspberry Pi via SSH
2. ✅ Clona il repository (al primo deploy)
3. ✅ Fa il pull delle ultime modifiche
4. ✅ Crea il file `.env` dai secrets
5. ✅ Identifica il tipo di progetto (Docker/Node/Python)
6. ✅ Installa le dipendenze
7. ✅ Riavvia l'applicazione

### 4.3 Verifica sul Raspberry Pi

Connettiti al Pi e controlla che il progetto sia stato deployato:

```bash
cd ~/projects/nome-del-tuo-repo
ls -la
# Dovresti vedere tutti i file del progetto e il .env
```

---

## 🔄 Uso Quotidiano

Da ora in poi, ogni volta che fai un push su GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Il deploy partirà automaticamente! Puoi monitorare il progresso nella tab **Actions** di GitHub.

---

## 🛠️ Configurazioni Specifiche per Tipo di Progetto

### Node.js con PM2 (CONSIGLIATO per Raspberry Pi 2)

Il workflow rileva `package.json` e:
1. Installa le dipendenze con `npm install`
2. Fa il build se presente lo script `build`
3. Riavvia con PM2

**Primo setup manuale** (solo la prima volta):
```bash
cd ~/projects/tuo-progetto
pm2 start npm --name "tuo-progetto" -- start
pm2 save
pm2 startup
```

### Python con systemd (CONSIGLIATO per Raspberry Pi 2)

Il workflow rileva `requirements.txt` e:
1. Crea/attiva il virtual environment
2. Installa le dipendenze
3. Riavvia il servizio systemd

**Primo setup manuale** (solo la prima volta):

Crea il file `/etc/systemd/user/tuo-progetto.service`:
```ini
[Unit]
Description=Tuo Progetto Python
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi/projects/tuo-progetto
ExecStart=/home/pi/projects/tuo-progetto/venv/bin/python main.py
Restart=always

[Install]
WantedBy=default.target
```

Abilita e avvia:
```bash
systemctl --user enable tuo-progetto
systemctl --user start tuo-progetto
```

### Docker Compose (SOLO per Raspberry Pi 4/5)

**⚠️ ATTENZIONE: Non consigliato per Raspberry Pi 2 (1GB RAM)**

Il workflow rileva automaticamente `docker-compose.yml` e fa:
```bash
docker-compose down
docker-compose up -d --build
```

Assicurati che il tuo `docker-compose.yml` sia configurato correttamente.

**Se hai un Raspberry Pi 2**, converti il progetto Docker per usare PM2 o systemd invece.

---

## ⚡ Ottimizzazioni per Raspberry Pi 2

Se usi un Raspberry Pi 2, queste ottimizzazioni sono **essenziali**:

### 1. Aumenta lo swap

Con solo 1GB di RAM, lo swap è fondamentale:

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Cambia CONF_SWAPSIZE=100 in CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 2. Disabilita servizi non necessari

```bash
# Disabilita Bluetooth se non serve
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# Disabilita WiFi se usi ethernet
sudo systemctl disable wpa_supplicant
```

### 3. Monitora le risorse

Installa strumenti per monitorare:

```bash
sudo apt install htop iotop -y

# Usa htop per vedere RAM e CPU
htop

# Controlla lo stato della memoria
free -h
```

### 4. SD Card veloce

Usa una microSD **Classe 10 o A1** di buona qualità (SanDisk, Samsung). La velocità della SD è critica con 1GB di RAM.

### 5. Limita i progetti attivi

**Raspberry Pi 2**: Max 1-2 progetti leggeri contemporaneamente
**Raspberry Pi 4/5**: Puoi gestire 5-10+ progetti senza problemi

---

## 🔒 Sicurezza e Best Practices

### IP Statico o DynDNS

Se il tuo ISP cambia spesso l'IP pubblico:

1. Configura DynDNS (es. DuckDNS):
```bash
mkdir ~/duckdns
cd ~/duckdns
echo "echo url='https://www.duckdns.org/update?domains=tuodominio&token=tuotoken&ip=' | curl -k -o ~/duckdns/duck.log -K -" > duck.sh
chmod 700 duck.sh
crontab -e
# Aggiungi: */5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

2. Usa il dominio DuckDNS come `SSH_HOST`

### Firewall

Configura il firewall per aprire solo le porte necessarie:

```bash
sudo apt install ufw -y
sudo ufw allow ssh
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Reverse Proxy (Nginx/Caddy)

Per gestire più progetti su porte diverse, usa un reverse proxy.

**Esempio con Caddy** (gestisce automaticamente HTTPS):
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

Configura `/etc/caddy/Caddyfile`:
```
progetto1.tuodominio.duckdns.org {
    reverse_proxy localhost:3000
}

progetto2.tuodominio.duckdns.org {
    reverse_proxy localhost:3001
}
```

---

## 🐛 Troubleshooting

### Il workflow fallisce alla connessione SSH

- Verifica che l'IP sia corretto
- Controlla che SSH sia abilitato sul Pi
- Verifica che la chiave privata sia completa nei secrets

### Il progetto non si riavvia

- Controlla i log del workflow su GitHub Actions
- Connettiti al Pi e verifica manualmente:
  ```bash
  cd ~/projects/tuo-progetto
  docker-compose logs    # per Docker
  pm2 logs               # per PM2
  journalctl --user -u tuo-progetto  # per systemd
  ```

### File .env non viene creato

- Verifica che il secret `ENV_FILE` sia impostato su GitHub
- Controlla nei log del workflow il messaggio "Creating .env file"

### Permessi negati

```bash
# Sul Raspberry Pi
sudo chown -R $USER:$USER ~/projects
```

---

## 📚 Risorse Utili

- [Documentazione GitHub Actions](https://docs.github.com/en/actions)
- [Docker Compose](https://docs.docker.com/compose/)
- [PM2 Documentation](https://pm2.keymetrics.io/docs/usage/quick-start/)
- [DuckDNS](https://www.duckdns.org/)
- [Caddy Server](https://caddyserver.com/docs/)

---

## 🎉 Conclusione

Ora hai un sistema completo di CI/CD casalingo! Ogni push su GitHub viene automaticamente deployato sul tuo Raspberry Pi.

Buon coding! 🚀
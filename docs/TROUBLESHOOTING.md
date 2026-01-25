# Troubleshooting - Guida Rapida

Soluzioni ai problemi più comuni.

## 🔴 Errori All'Avvio

### ❌ No `JobQueue` set up

**Errore completo:**
```
PTBUserWarning: No `JobQueue` set up. To use `JobQueue`, you must install PTB via 
`pip install "python-telegram-bot[job-queue]"`.

AttributeError: 'NoneType' object has no attribute 'run_daily'
```

**Causa:** Manca estensione job-queue di python-telegram-bot

**Soluzione:**
```bash
pip install "python-telegram-bot[job-queue]"
```

O aggiorna requirements.txt e reinstalla:
```bash
pip install -r requirements.txt
```

---

### ❌ 'Database' object has no attribute 'episodes_df'

**Errore:**
```
AttributeError: 'Database' object has no attribute 'episodes_df'
```

**Causa:** Stai usando database SQLite ma il bot cerca attributi CSV

**Soluzione:** 
Ho aggiunto metodi di compatibilità. Aggiorna i file:
1. `database.py` (CSV) - aggiornato
2. `database_sqlite.py` - aggiornato  
3. `bot.py` - aggiornato

Riavvia il bot.

---

### ❌ ModuleNotFoundError: No module named 'X'

**Errore:**
```
ModuleNotFoundError: No module named 'spotipy'
```

**Soluzione:**
```bash
pip install -r requirements.txt
```

Se persiste:
```bash
pip install spotipy pandas python-telegram-bot[job-queue] requests beautifulsoup4
```

---

### ❌ BOT_TOKEN non trovato

**Errore:**
```
ValueError: BOT_TOKEN non trovato nel file .env
```

**Soluzione:**
1. Crea file `.env` dalla copia di `.env.example`
2. Inserisci i tuoi token:
```bash
cp .env.example .env
nano .env
```

---

## 🟡 Errori Durante l'Uso

### ❌ Bot non risponde

**Verifica:**
1. Bot in esecuzione?
   ```bash
   ps aux | grep bot.py
   ```

2. Errori nei log?
   ```bash
   tail -f bot.log
   ```

3. Token corretto?
   ```bash
   cat .env | grep BOT_TOKEN
   ```

**Soluzioni:**
- Riavvia: `python bot.py`
- Verifica token con BotFather
- Controlla connessione internet

---

### ❌ Notifiche non arrivano

**Problema:** Nuovo episodio uscito ma nessuna notifica

**Verifica:**
```
/jobs      # Job attivi?
/testcheck # Forza check manuale
```

**Cause comuni:**
1. Job non configurati → Riavvia bot
2. Utente non in lista → Fai `/start`
3. Credenziali Spotify errate → Verifica `.env`
4. Bot offline durante check → Controlla uptime

---

### ❌ Ricerche non trovano episodi

**Problema:** Cerchi episodio ma bot dice "non trovato"

**Verifica:**
```
/reload    # Ricarica database
/stats     # Vedi quanti episodi ci sono
```

**Soluzioni:**
- Database vuoto? Importa dati
- Nome ospite errato? Controlla spelling
- ID episodio errato? Usa range da /stats

---

### ❌ Comandi admin non funzionano

**Problema:** `/stats` risponde "Non sei autorizzato"

**Causa:** `ADMIN_CHAT_ID` errato in `.env`

**Soluzione:**
1. Ottieni tuo chat_id:
   - Scrivi a @userinfobot
   - Copia il numero

2. Aggiorna `.env`:
   ```
   ADMIN_CHAT_ID=123456789
   ```

3. Riavvia bot

---

## 🟢 Problemi Performance

### 🐌 Bot lento

**Sintomo:** Risponde dopo 5-10 secondi

**Con CSV:**
- Normale con >500 episodi
- Soluzione: Migra a SQLite

**Con SQLite:**
- Anormale
- Verifica: `sqlite3 data/bot.db "PRAGMA integrity_check;"`
- Ottimizza: `sqlite3 data/bot.db "VACUUM;"`

---

### 💾 Database grande

**Con CSV:**
```bash
du -sh data/*.csv
```

**Con SQLite:**
```bash
du -sh data/bot.db
# Se >100MB, ottimizza
sqlite3 data/bot.db "VACUUM;"
```

---

## 🔧 Problemi Migrazione

### ❌ Dati mancanti dopo migrazione

**Verifica quanti dati migrati:**
```bash
# CSV
wc -l data/db.csv

# SQLite  
sqlite3 data/bot.db "SELECT COUNT(*) FROM episodes;"
```

**Se diversi:**
- Controlla log migrazione
- Ri-esegui migrazione
- Verifica encoding CSV (deve essere UTF-8)

---

### ❌ Errore durante migrazione

**Errore:** "table already exists"

**Soluzione:**
```bash
rm data/bot.db
python migrate_csv_to_sqlite.py
```

---

### ❌ Bot non trova database

**Errore:** "no such table: episodes"

**Causa:** Stai usando `database.py` vecchio con `bot.db`

**Soluzione:**
```bash
# Assicurati di usare database_sqlite.py
mv database.py database_csv_backup.py
mv database_sqlite.py database.py
python bot.py
```

---

## 🌐 Problemi Network

### ❌ Spotify API non risponde

**Errore nei log:**
```
Error getting latest episode: HTTP Error 401
```

**Soluzione:**
1. Verifica credenziali in `.env`
2. Rigenera credenziali su Spotify Developer Dashboard
3. Aggiorna `.env` e riavvia

---

### ❌ Telegram API timeout

**Errore:**
```
telegram.error.TimedOut: Timed out
```

**Soluzioni:**
- Problemi rete temporanei → Riprova
- Firewall? → Verifica porte aperte
- Server lento? → Riavvia/cambia hosting

---

## 📱 Problemi Deployment

### ❌ Bot parte in locale ma non su server

**Checklist:**
1. ✅ Python 3.9+ installato?
2. ✅ Dipendenze installate?
3. ✅ File .env presente?
4. ✅ Percorsi corretti?
5. ✅ Permessi file OK?

**Verifica:**
```bash
python3 --version
pip list | grep telegram
ls -la .env
ls -la data/
```

---

### ❌ Systemd service non parte

**Verifica status:**
```bash
sudo systemctl status office-cards-bot
```

**Vedi errori:**
```bash
sudo journalctl -u office-cards-bot -n 50
```

**Cause comuni:**
- Percorso errato in .service
- Permessi file
- Python venv non attivato

**Soluzione:** Verifica paths in `/etc/systemd/system/office-cards-bot.service`

---

## 🔍 Debug Avanzato

### Abilita Log Dettagliati

In `bot.py`, cambia:
```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Cambia da INFO a DEBUG
)
```

### Salva Log su File

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

### Test Manuale Componenti

**Test Spotify:**
```python
from spotify_service import SpotifyService
from config import Config

config = Config()
spotify = SpotifyService(config)
episode = spotify.get_latest_episode()
print(episode)
```

**Test Database:**
```python
from database import Database
from config import Config

config = Config()
db = Database(config)
print(db.get_last_episode())
```

---

## 🆘 Quando Tutto Fallisce

### Ripristino Completo

```bash
# 1. Backup dati
cp -r data data_emergency_backup

# 2. Reinstalla dipendenze
pip uninstall -y python-telegram-bot spotipy pandas
pip install -r requirements.txt

# 3. Verifica .env
cat .env

# 4. Riavvia da zero
python bot.py
```

### Rollback a Versione Precedente

```bash
# Torna a CSV se SQLite problematico
mv database.py database_sqlite_problem.py
mv database_csv_backup.py database.py

# Riavvia
python bot.py
```

---

## 📞 Supporto

**Prima di chiedere aiuto:**
1. ✅ Leggi questa guida
2. ✅ Controlla log: `tail -f bot.log`
3. ✅ Prova `/reload` e riavvio bot
4. ✅ Verifica `.env` e requirements

**Informazioni utili da fornire:**
- Messaggio errore completo
- Output di `pip list`
- Versione Python: `python --version`
- OS: `uname -a` (Linux/Mac) o `ver` (Windows)
- Ultimi 20 righe log

---

## ✅ Checklist Salute Bot

Esegui periodicamente:

```bash
# 1. Verifica bot attivo
ps aux | grep bot.py

# 2. Controlla log errori
tail -50 bot.log | grep ERROR

# 3. Test comandi
# In Telegram:
/stats
/jobs

# 4. Verifica spazio disco
df -h

# 5. Backup
cp data/bot.db backups/bot_$(date +%Y%m%d).db

# 6. Ottimizza (SQLite)
sqlite3 data/bot.db "VACUUM;"
```

---

**Aggiornamento ultima modifica:** 2025-01-24
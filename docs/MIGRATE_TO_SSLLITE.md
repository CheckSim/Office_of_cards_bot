# Migrazione da CSV a SQLite

Guida passo-passo per migrare il tuo bot da CSV a SQLite.

## 🎯 Perché Migrare?

| Aspetto | CSV | SQLite | Miglioramento |
|---------|-----|--------|---------------|
| **Velocità query** | Lenta | 10-100x più veloce | ⚡⚡⚡ |
| **Concorrenza** | Problematica | Sicura | ✅ |
| **Integrità dati** | Nessuna | Validazione | ✅ |
| **Ricerche** | Scan completo | Indici | 🚀 |
| **Backup** | Multipli file | Singolo file | 📦 |
| **Transazioni** | No | ACID | ✅ |

## 📋 Cosa Serve

✅ Python con SQLite (già incluso)
✅ Dati CSV esistenti
✅ 5 minuti di tempo
✅ Backup dei dati (sempre!)

## 🚀 Procedura di Migrazione

### Step 1: Backup

**IMPORTANTISSIMO!** Fai backup prima di tutto:

```bash
# Backup cartella data completa
cp -r data data_backup_$(date +%Y%m%d)

# O crea un archivio
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### Step 2: Scarica i File

Hai bisogno di questi due file:
- `database_sqlite.py` - Nuovo database con SQLite
- `migrate_csv_to_sqlite.py` - Script di migrazione

```bash
# Assicurati di essere nella directory del progetto
ls -la
# Dovresti vedere: bot.py, config.py, database.py, etc.
```

### Step 3: Esegui Migrazione

```bash
python migrate_csv_to_sqlite.py
```

**Output atteso:**
```
🔄 MIGRAZIONE DA CSV A SQLITE
============================================================

Questo script convertirà i tuoi dati CSV in un database SQLite.
I file originali NON verranno modificati.

Vuoi procedere? (s/n): s

🚀 Inizio migrazione...

2025-01-24 15:30:00 - INFO - 🔨 Creando struttura database...
2025-01-24 15:30:01 - INFO - ✅ Struttura database creata
2025-01-24 15:30:01 - INFO - 📊 Migrando episodi...
2025-01-24 15:30:05 - INFO - ✅ Episodi migrati: 250, saltati: 0
2025-01-24 15:30:05 - INFO - 💊 Migrando pillole...
2025-01-24 15:30:06 - INFO - ✅ Pillole migrate: 45, saltate: 0
2025-01-24 15:30:06 - INFO - 📈 Migrando statistiche...
2025-01-24 15:30:10 - INFO - ✅ Statistiche migrate: 15678
2025-01-24 15:30:10 - INFO - 👥 Migrando utenti notifiche...
2025-01-24 15:30:11 - INFO - ✅ Utenti notifiche migrati: 1234

==================================================
🎉 MIGRAZIONE COMPLETATA!
==================================================
📊 Episodi totali: 250
💊 Pillole totali: 45
📈 Statistiche totali: 15678
👥 Utenti notifiche: 1234
💾 Database salvato in: data/bot.db
==================================================

📝 PROSSIMI PASSI:
1. Rinomina database.py in database_csv_old.py
2. Rinomina database_sqlite.py in database.py
3. Riavvia il bot: python bot.py
4. Testa con /stats e /testcheck
5. Se tutto funziona, puoi eliminare i CSV (ma fai backup prima!)

✅ Migrazione completata con successo!
```

### Step 4: Sostituisci il Modulo Database

```bash
# Backup vecchio database.py
mv database.py database_csv_old.py

# Attiva nuovo database SQLite
mv database_sqlite.py database.py
```

### Step 5: Testa il Bot

```bash
# Avvia il bot
python bot.py
```

**Output atteso:**
```
2025-01-24 15:35:00 - INFO - ✅ Database SQLite initialized successfully
2025-01-24 15:35:01 - INFO - 🤖 Bot started successfully
2025-01-24 15:35:01 - INFO - 📅 Episode check: Weekly (Monday 17:00)
2025-01-24 15:35:01 - INFO - 💊 Pill check: Daily (12:00)
```

### Step 6: Verifica Funzionamento

Da Telegram (come admin):

```
/stats
```

**Output atteso:**
```
📊 Statistiche Bot

Database:
🎧 Episodi: 250
💊 Pillole: 45
📁 Categorie: 12
👥 Ospiti: 180

Utenti:
👤 Utenti attivi: 1,234
🔍 Query totali: 15,678
...
```

Se vedi le statistiche corrette, **la migrazione è riuscita!** 🎉

## ✅ Verifica Completa

Testa queste funzionalità:

```
✅ /start           → Menu principale
✅ Ultimo Episodio  → Visualizza ultimo episodio
✅ Pillola Casuale  → Pillola random
✅ Ricerca Categoria → Cerca per categoria
✅ Ricerca Ospite   → Cerca per ospite
✅ Numero episodio  → Scrivi un numero (es. 142)
✅ /stats           → Statistiche
✅ /users           → Lista utenti
✅ /testcheck       → Check episodi
```

Se tutto funziona → **Migrazione completata!** 🚀

## 🗑️ Pulizia (Opzionale)

**Solo DOPO aver verificato che tutto funziona:**

```bash
# I CSV non servono più (ma tieni il backup!)
# NON eliminare subito, aspetta qualche giorno

# Quando sei sicuro:
mv data/db.csv data/db_old.csv
mv data/stats.csv data/stats_old.csv
mv data/pills.csv data/pills_old.csv
mv data/notification_users.txt data/notification_users_old.txt

# Dopo una settimana senza problemi, puoi eliminarli
# rm data/*_old.csv data/*_old.txt
```

## 🔄 Rollback (Se Qualcosa Va Storto)

Se hai problemi, torna ai CSV:

```bash
# Stop bot
# Ctrl+C o kill process

# Ripristina vecchio database.py
mv database.py database_sqlite_new.py
mv database_csv_old.py database.py

# Riavvia
python bot.py
```

I tuoi dati CSV sono intatti, torni come prima.

## 📊 Confronto Performance

**Prima (CSV):**
```python
# Ricerca episodio per ID
import time
start = time.time()
episode = db.get_episode_by_id(142)
print(f"Tempo: {time.time() - start:.3f}s")
# Output: Tempo: 0.150s
```

**Dopo (SQLite):**
```python
# Stessa ricerca
start = time.time()
episode = db.get_episode_by_id(142)
print(f"Tempo: {time.time() - start:.3f}s")
# Output: Tempo: 0.002s
```

**75x più veloce!** ⚡

## 🗄️ Gestione Database SQLite

### Visualizzare i Dati

```bash
# Apri database con sqlite3
sqlite3 data/bot.db

# Comandi utili:
.tables                    # Lista tabelle
.schema episodes          # Struttura tabella
SELECT COUNT(*) FROM episodes;
SELECT * FROM episodes LIMIT 5;
.quit                     # Esci
```

### Backup Database

```bash
# SQLite = un solo file
cp data/bot.db data/bot_backup_$(date +%Y%m%d).db

# O con comando SQLite
sqlite3 data/bot.db ".backup data/bot_backup.db"
```

### Ottimizzazione

```bash
sqlite3 data/bot.db "VACUUM;"
```

Compatta il database, recupera spazio.

## 🆘 Troubleshooting

### Errore: "table episodes already exists"

**Soluzione:**
```bash
# Elimina database esistente e riprova
rm data/bot.db
python migrate_csv_to_sqlite.py
```

### Errore: "no such column: episode_id"

**Problema:** Vecchio database.py ancora attivo

**Soluzione:**
```bash
# Assicurati di aver rinominato
mv database.py database_csv_old.py
mv database_sqlite.py database.py
```

### Dati mancanti dopo migrazione

**Verifica:**
```bash
sqlite3 data/bot.db "SELECT COUNT(*) FROM episodes;"
sqlite3 data/bot.db "SELECT COUNT(*) FROM pills;"
```

Confronta con i CSV:
```bash
wc -l data/db.csv
wc -l data/pills.csv
```

Se i numeri non coincidono, controlla log migrazione.

### Bot lento dopo migrazione

**Causa:** Cache non funzionante

**Soluzione:**
```bash
# Da Telegram
/reload
```

## 🎓 Best Practices

1. **Backup regolari**
   ```bash
   # Cron giornaliero
   0 3 * * * cp /path/to/data/bot.db /path/to/backups/bot_$(date +\%Y\%m\%d).db
   ```

2. **Monitor dimensione database**
   ```bash
   ls -lh data/bot.db
   # Se >1GB, considera PostgreSQL
   ```

3. **Vacuum periodico**
   ```bash
   # Una volta al mese
   sqlite3 data/bot.db "VACUUM;"
   ```

4. **Backup prima di aggiornamenti**
   ```bash
   cp data/bot.db data/bot_before_update.db
   ```

## 📈 Prossimi Passi (Opzionale)

Dopo aver usato SQLite per un po', potresti voler:

1. **Aggiungere full-text search**
   ```sql
   CREATE VIRTUAL TABLE episodes_fts 
   USING fts5(title, description);
   ```

2. **Analytics avanzate**
   ```sql
   SELECT category, COUNT(*) 
   FROM episodes 
   GROUP BY category 
   ORDER BY COUNT(*) DESC;
   ```

3. **Migrare a PostgreSQL**
   - Per >10k utenti
   - Per team multipli
   - Per alta disponibilità

## ❓ FAQ

**Q: Perdo i dati CSV durante la migrazione?**
A: No! I CSV rimangono intatti. Lo script crea solo il nuovo database SQLite.

**Q: Posso tornare ai CSV?**
A: Sì, in qualsiasi momento. Basta ripristinare il vecchio database.py.

**Q: Quanto spazio occupa SQLite vs CSV?**
A: Simile o leggermente meno grazie alla compressione interna.

**Q: SQLite funziona su Windows/Mac/Linux?**
A: Sì, è multipiattaforma al 100%.

**Q: Devo cambiare qualcosa nel bot.py?**
A: No! Il nuovo database.py ha la stessa interfaccia.

**Q: Posso usare tool grafici per SQLite?**
A: Sì! Consigliati: DB Browser for SQLite, DBeaver, DataGrip.

## 🎉 Conclusione

Una volta migrato a SQLite:
- ✅ Bot 10-100x più veloce
- ✅ Nessun rischio corruzione dati
- ✅ Query complesse possibili
- ✅ Backup più semplici
- ✅ Pronto per scalare

**Tempo totale migrazione: ~5 minuti**
**Benefici: permanenti** 🚀

---

Per supporto: vedi `README.md` e `ADMIN_COMMANDS.md`
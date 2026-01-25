# Guida Rescraping Completo Database

Come rifare lo scraping da zero di tutti gli episodi.

## 🎯 Quando Usarlo

Usa il rescraping quando:
- ✅ Database ha caratteri corrotti (encoding errato)
- ✅ Molti episodi hanno dati mancanti
- ✅ Vuoi ripartire da zero con dati puliti
- ✅ Migrazione da vecchio sistema
- ✅ Shownotes non aggiornate

## ⚙️ Come Funziona

Lo script `rescrape_all_episodes.py`:

1. **Scarica TUTTI gli episodi da Spotify**
   - Usa API ufficiale Spotify
   - Gestisce paginazione automaticamente
   - Scarica descrizioni, URL, date

2. **Fa scraping sito per shownotes**
   - Per ogni episodio visita officeofcards.com
   - Estrae URL shownotes e nome ospite
   - Pausa 1 secondo tra richieste (rate limiting)

3. **Crea backup automatici**
   - Salva vecchi file prima di sovrascrivere
   - Nomi con timestamp: `db_backup_20250124_153045.csv`

4. **Genera nuovo database pulito**
   - CSV o SQLite (a scelta)
   - Dati UTF-8 corretti
   - Tutti i campi validati

## 🚀 Uso

### Esecuzione Base

```bash
python rescrape_all_episodes.py
```

**Output:**
```
====================================================================
🔄 RESCRAPING COMPLETO DATABASE OFFICE OF CARDS
====================================================================

Questo script:
  1. Scarica TUTTI gli episodi da Spotify
  2. Fa scraping delle shownotes dal sito
  3. Crea backup dei dati esistenti
  4. Sovrascrive il database con dati puliti

⏱️  Tempo stimato: 5-15 minuti (dipende dal numero di episodi)

Vuoi procedere? (s/n): s

Formato database:
  1. CSV (compatibile con database.py)
  2. SQLite (compatibile con database_sqlite.py)
  3. Entrambi

Scegli (1/2/3): 3

🚀 Inizio rescraping...

============================================================
📊 SCRAPING EPISODI PRINCIPALI
============================================================

📡 Scaricando episodi da Spotify...
  ✓ Scaricati 50 episodi finora...
  ✓ Scaricati 100 episodi finora...
  ✓ Scaricati 150 episodi finora...
✅ Totale episodi scaricati: 152

🔄 Parsing episodi...
✅ 152 episodi parsati

🌐 Arricchendo episodi con shownotes...
  [1/152] Episodio 152: Intervista con John Doe...
  [2/152] Episodio 151: Q&A con gli ascoltatori...
  ...
✅ Arricchimento completato!

============================================================
💊 SCRAPING PILLOLE
============================================================

📡 Scaricando episodi da Spotify...
✅ Totale episodi scaricati: 45

🔄 Parsing pillole...
✅ 45 pillole parsate

============================================================
💾 SALVATAGGIO DATI
============================================================

📦 Backup vecchio db.csv → db_backup_20250124_153045.csv
💾 Salvando 152 episodi...
✅ Salvato: data/db.csv

📦 Backup vecchio pills.csv → pills_backup_20250124_153045.csv
💾 Salvando 45 pillole...
✅ Salvato: data/pills.csv

============================================================
💾 SALVATAGGIO IN SQLITE
============================================================

📦 Backup vecchio database → bot_backup_20250124_153045.db
🗑️  Svuotando tabelle esistenti...
💾 Inserendo 152 episodi...
💾 Inserendo 45 pillole...
✅ Database salvato: data/bot.db

============================================================
📊 REPORT FINALE
============================================================

📺 EPISODI:
  Totali: 152
  Con shownotes: 148 (97.4%)
  Con guest: 145 (95.4%)
  Categorie:
    - INTERVISTA: 120
    - Q&A: 15
    - INTRO: 10
    - TECH: 5
    - BUSINESS: 2

💊 PILLOLE:
  Totali: 45

⚠️  EPISODI DA VERIFICARE:
  Senza shownotes: 4
    - ID 152: Ultimo episodio appena uscito
    - ID 151: In attesa di pubblicazione shownotes
    ...

============================================================

⏱️  Tempo totale: 8.3 minuti

====================================================================
✅ RESCRAPING COMPLETATO CON SUCCESSO!
====================================================================

📝 Prossimi passi:
  1. Verifica i dati generati
  2. Riavvia il bot: python bot.py
  3. Testa con /stats
  4. Se tutto OK, elimina i backup vecchi
```

## 📋 Opzioni Formato

### Opzione 1: Solo CSV
```
Scegli (1/2/3): 1
```

**Genera:**
- `data/db.csv` - Episodi
- `data/pills.csv` - Pillole

**Per:** Chi usa `database.py` (versione CSV)

### Opzione 2: Solo SQLite
```
Scegli (1/2/3): 2
```

**Genera:**
- `data/bot.db` - Database completo

**Per:** Chi usa `database_sqlite.py`

### Opzione 3: Entrambi (Consigliato)
```
Scegli (1/2/3): 3
```

**Genera:**
- CSV + SQLite
- Massima flessibilità
- Puoi switchare tra versioni

## ⏱️ Tempi di Esecuzione

| Episodi | Tempo Stimato |
|---------|---------------|
| 50 | ~3 minuti |
| 100 | ~6 minuti |
| 150 | ~9 minuti |
| 200 | ~12 minuti |

**Fattori:**
- Download Spotify: veloce (~1 min)
- Scraping shownotes: 1 sec/episodio
- Salvataggio: veloce (~10 sec)

## 🔍 Cosa Viene Scaricato

### Per Ogni Episodio

Da **Spotify:**
- ✅ Titolo
- ✅ Descrizione
- ✅ URL Spotify
- ✅ Data pubblicazione
- ✅ ID episodio (dal titolo)
- ✅ Parte (se multi-parte)
- ✅ Categoria (dal titolo)

Da **Sito Web:**
- ✅ URL Shownotes
- ✅ Nome ospite

### Per Ogni Pillola

Da **Spotify:**
- ✅ Titolo
- ✅ Descrizione
- ✅ URL Spotify
- ✅ ID episodio correlato
- ✅ Data pubblicazione

## 🛡️ Sicurezza

### Backup Automatici

Lo script crea **sempre** backup prima di modificare:

```
data/
├── db.csv                        ← Nuovo (pulito)
├── db_backup_20250124_153045.csv ← Backup vecchio
├── pills.csv                     ← Nuovo (pulito)
├── pills_backup_20250124_153045.csv
├── bot.db                        ← Nuovo (pulito)
└── bot_backup_20250124_153045.db ← Backup vecchio
```

**Se qualcosa va storto:** Ripristina backup!

### Rollback

```bash
# Ripristina da backup
cp data/db_backup_20250124_153045.csv data/db.csv
cp data/pills_backup_20250124_153045.csv data/pills.csv

# O per SQLite
cp data/bot_backup_20250124_153045.db data/bot.db
```

## 🐛 Gestione Errori

### Interruzione Durante Scraping

Se premi `Ctrl+C` o si interrompe:
- ✅ Backup già creati (al sicuro)
- ✅ Vecchi dati ancora intatti
- ✅ Puoi riprovare quando vuoi

**Riprova:**
```bash
python rescrape_all_episodes.py
```

### Episodi Senza Shownotes

**Normale!** Episodi recenti potrebbero non avere ancora shownotes pubblicate.

Nel report vedrai:
```
⚠️  EPISODI DA VERIFICARE:
  Senza shownotes: 4
    - ID 152: Ultimo episodio appena uscito
```

**Soluzione:** Aspetta pubblicazione shownotes, poi ri-esegui.

### Rate Limiting

Lo script ha pause automatiche:
- 0.5 sec tra chiamate Spotify
- 1 sec tra scraping shownotes

**Se troppo lento:** Puoi ridurre pause in `rescrape_all_episodes.py`:
```python
time.sleep(0.3)  # Invece di 1
```

Ma attento a non essere bloccato! ⚠️

## 📊 Verifica Post-Rescraping

### 1. Conta Episodi

**CSV:**
```bash
wc -l data/db.csv
# Output: 153 (152 episodi + 1 header)
```

**SQLite:**
```bash
sqlite3 data/bot.db "SELECT COUNT(*) FROM episodes;"
# Output: 152
```

### 2. Verifica Encoding

**CSV:**
```bash
file -I data/db.csv
# Output: data/db.csv: text/plain; charset=utf-8
```

Deve essere `utf-8`! ✅

### 3. Test Bot

```bash
python bot.py
```

**In Telegram:**
```
/start
/stats
```

Controlla che numeri corrispondano!

### 4. Verifica Episodio Specifico

```
142
```

Controlla che:
- ✅ Titolo corretto
- ✅ Descrizione leggibile (no caratteri strani)
- ✅ Bottoni Spotify e Shownotes funzionanti

## 🔄 Rescraping Parziale

Vuoi solo aggiornare episodi recenti senza rifare tutto?

**Modifica script:**

```python
# In rescrape_all_episodes.py, metodo enrich_with_shownotes

def enrich_with_shownotes(self, episodes: list) -> list:
    enriched = []
    
    for episode in episodes:
        episode_id = episode.get('Id')
        
        # ⬇️ Aggiungi questa condizione
        if episode_id < 100:  # Salta episodi vecchi
            enriched.append(episode)
            continue
        # ⬆️
        
        # ... resto del codice scraping
```

**Risparmia tempo!** Scraping solo episodi >100.

## 🎓 Personalizzazioni

### Cambia Rate Limiting

In `rescrape_all_episodes.py`:

```python
time.sleep(0.5)  # ← Cambia questo valore

# Più veloce (rischio block):
time.sleep(0.2)

# Più lento (sicuro):
time.sleep(2)
```

### Scraping Solo Spotify (No Shownotes)

Commenta questa riga:
```python
# episodes = self.enrich_with_shownotes(episodes)
```

**Utile per:** Test veloce struttura dati.

### Export Aggiuntivi

Aggiungi export JSON:
```python
import json

# Dopo scraping
with open('data/episodes.json', 'w', encoding='utf-8') as f:
    json.dump(episodes, f, ensure_ascii=False, indent=2)
```

## 💡 Best Practices

1. **Fai rescraping in orari di basso traffico**
   - Notte/mattina presto
   - Meno carico sul sito

2. **Disattiva bot durante rescraping**
   ```bash
   # Stop bot
   killall python
   
   # Rescraping
   python rescrape_all_episodes.py
   
   # Restart bot
   python bot.py
   ```

3. **Tieni backup esterni**
   ```bash
   # Prima di rescraping
   tar -czf backup_completo_$(date +%Y%m%d).tar.gz data/
   ```

4. **Verifica sempre dopo rescraping**
   - Test manuale 5-10 episodi random
   - Controlla encoding
   - Testa bot

## ❓ FAQ

**Q: Perso i dati durante rescraping?**
A: No! Backup automatici sempre creati prima.

**Q: Quanto spesso fare rescraping?**
A: Solo quando necessario (dati corrotti, problemi encoding). Non serve periodicamente.

**Q: Posso interrompere e riprendere?**
A: No, rescraping è tutto-o-niente. Ma puoi interrompere e ripartire da zero.

**Q: Scraping è legale?**
A: Sì, usi API ufficiale Spotify e scraping pubblico da tuo sito.

**Q: Consuma tante API calls?**
A: Spotify: ~3-5 chiamate per tutti episodi. Sito: 1 richiesta/episodio.

## 🆘 Problemi Comuni

### Spotify API Error 429

**Errore:** "Too Many Requests"

**Soluzione:**
- Aspetta 1 ora
- Aumenta pause: `time.sleep(2)`

### Connection Timeout

**Errore:** "Connection timed out"

**Soluzione:**
- Controlla connessione internet
- Riprova più tardi
- Usa VPN se IP bloccato

### Encoding Errors

**Errore:** "UnicodeDecodeError"

**Soluzione:**
Lo script usa UTF-8. Se persiste:
```python
# In save_to_csv
df.to_csv(..., encoding='utf-8-sig')  # BOM per Excel
```

---

## ✅ Checklist Pre-Rescraping

Prima di iniziare, verifica:

- [ ] Bot fermato
- [ ] Credenziali Spotify valide (`.env`)
- [ ] Connessione internet stabile
- [ ] Spazio disco sufficiente (~50MB)
- [ ] Tempo disponibile (10-15 min)
- [ ] Backup manuale fatto (opzionale)

**Fatto?** → `python rescrape_all_episodes.py` 🚀

---

Per supporto: vedi `README.md` e `TROUBLESHOOTING.md`
# Comandi Admin - Quick Reference

Guida rapida ai comandi amministrativi del bot.

## 📋 Lista Comandi

### Informazioni e Monitoraggio

#### `/stats`
Mostra statistiche complete del bot.

**Output:**
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

Top 5 ricerche:
  • Last: 3,450
  • Random: 2,100
  • Guest Marco Montemagno: 890
  • ...

Ultimo episodio:
152 Intervista con John Doe
```

**Quando usarlo:**
- Controllare crescita utenti
- Vedere episodi più cercati
- Verificare stato database

---

#### `/jobs`
Mostra job schedulati attivi e prossima esecuzione.

**Output:**
```
📋 Job Attivi: 2

• weekly_episode_check
  ⏰ Prossima esecuzione: 27/01/2025 17:00:00

• daily_pill_check
  ⏰ Prossima esecuzione: 25/01/2025 12:00:00
  🔄 Intervallo: 24.0 ore
```

**Quando usarlo:**
- Verificare che i job siano attivi
- Sapere quando sarà il prossimo check
- Debug problemi scheduling

---

#### `/users`
Lista utenti registrati per le notifiche.

**Output:**
```
👥 Utenti Registrati: 1,234

1. 123456789
2. 987654321
3. 555444333
...
20. 111222333

... e altri 1,214 utenti
```

**Quando usarlo:**
- Contare utenti attivi
- Verificare iscrizioni
- Export lista utenti (primi 20 visibili)

---

### Testing e Debug

#### `/testcheck`
Forza un check immediato per nuovi episodi.

**Cosa fa:**
1. Chiama Spotify API
2. Controlla se c'è nuovo episodio
3. Se sì: scraping, aggiungi DB, notifica tutti
4. Se no: log "No new episode found"

**Output:**
```
🔍 Eseguo check manuale per nuovi episodi...
✅ Check completato! Controlla i log.
```

**Quando usarlo:**
- Testare sistema notifiche
- Forzare check fuori orario
- Debug problemi Spotify API

**⚠️ Attenzione:** Se trova un nuovo episodio, **notifica TUTTI gli utenti**!

---

#### `/testpill`
Forza un check immediato per nuove pillole.

**Cosa fa:**
1. Chiama Spotify API (show pillole)
2. Controlla se c'è nuova pillola
3. Se sì: aggiungi al database
4. Notifica admin (non gli utenti)

**Output:**
```
🔍 Eseguo check manuale per nuove pillole...
✅ Check completato! Controlla i log.
```

**Quando usarlo:**
- Verificare nuove pillole
- Aggiornare database pillole
- Debug problemi API pillole

---

#### `/notify`
Invia a te stesso un'anteprima della notifica episodio.

**Cosa fa:**
- Prende ultimo episodio dal database
- Formatta messaggio come per le notifiche
- Invia solo a te (admin)

**Output:**
```
🎉 Nuovo episodio del tuo podcast preferito!

152 Intervista con John Doe

[Descrizione episodio...]

[Bottoni: Spotify, Shownotes, Donazioni]

✅ Questa è come apparirà la notifica agli utenti
```

**Quando usarlo:**
- Vedere come appare la notifica
- Testare formattazione
- Verificare bottoni

---

### Gestione Database

#### `/reload`
Ricarica il database da file CSV.

**Cosa fa:**
1. Legge db.csv, pills.csv, stats.csv
2. Aggiorna variabili in memoria
3. Ricalcola categorie, ospiti, etc.

**Output:**
```
🔄 Ricaricando database...
✅ Database ricaricato!
🎧 250 episodi
💊 45 pillole
```

**Quando usarlo:**
- Dopo modifiche manuali ai CSV
- Se sospetti dati obsoleti in memoria
- Dopo import dati

---

#### `/backup`
Crea e invia backup completo di tutti i dati.

**Cosa fa:**
1. Crea file ZIP con timestamp
2. Include: db.csv, stats.csv, pills.csv, notification_users.txt
3. Invia file ZIP
4. Elimina file temporaneo

**Output:**
```
📦 Creando backup...

[File: backup_20250124_153045.zip]
📦 Backup del 24/01/2025 15:30:45

✅ Backup completato!
```

**Quando usarlo:**
- **Prima** di modifiche importanti
- Backup giornaliero/settimanale
- Prima di aggiornare il bot
- Export dati

**💡 Tip:** Automatizza con crontab:
```bash
# Backup giornaliero alle 3:00
0 3 * * * curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$ADMIN_CHAT_ID" -d "text=/backup"
```

---

### Broadcasting

#### `/message`
Avvia processo di invio messaggio a tutti gli utenti.

**Flusso:**
1. Scrivi `/message`
2. Bot chiede: "Che messaggio vuoi inviare?"
3. Scrivi il messaggio
4. Bot invia a tutti gli utenti
5. Ricevi report: "✅ Inviati: 1,200 / ❌ Falliti: 34"

**Esempio:**
```
Admin: /message
Bot: Che messaggio vuoi inviare a tutti gli utenti?
     Scrivi /cancel per annullare.

Admin: 🎉 Novità! Ora puoi cercare episodi per categoria!
       Prova subito con /start

Bot: Messaggio inviato!
     ✅ Inviati: 1,200
     ❌ Falliti: 34
```

**Quando usarlo:**
- Annunci importanti
- Nuove funzionalità
- Manutenzione programmata
- Eventi speciali

**⚠️ Best practices:**
- Usa emoji per attirare attenzione
- Messaggio breve e chiaro
- Chiama all'azione (CTA)
- Non abusare (max 1-2 al mese)

---

#### `/cancel`
Annulla processo di broadcast in corso.

**Quando usarlo:**
- Hai scritto `/message` per errore
- Vuoi ripensare al messaggio
- Hai fatto un typo

**Output:**
```
Broadcast annullato.
```

---

### Help

#### `/admin`
Mostra lista completa comandi admin.

**Output:**
```
🔧 Comandi Admin

Informazioni:
/stats - Statistiche bot
/jobs - Job schedulati attivi
/users - Lista utenti registrati

Testing:
/testcheck - Check manuale episodi
/testpill - Check manuale pillole
/notify - Anteprima notifica

Gestione:
/reload - Ricarica database
/backup - Crea backup database
/message - Broadcast messaggio
/cancel - Annulla broadcast
```

---

## 🔄 Workflow Comuni

### 📊 Check Mattutino
```
/stats     → Vedi crescita utenti e query
/jobs      → Verifica prossimi check
```

### 🆕 Nuovo Episodio Uscito
```
/testcheck → Forza check
           → Bot notifica tutti automaticamente
/stats     → Verifica engagement
```

### 🔧 Manutenzione Settimanale
```
/backup    → Backup dati
/stats     → Review performance
/users     → Conta utenti attivi
```

### 📢 Annuncio Importante
```
/notify    → Preview messaggio
/message   → Invia a tutti
           → [Scrivi messaggio]
           → Conferma invio
```

### 🐛 Debug Problema
```
/jobs      → Verifica job attivi
/reload    → Ricarica database
/testcheck → Test manuale
```

---

## 🚨 Situazioni di Emergenza

### Bot Non Notifica Nuovi Episodi

**Checklist:**
1. `/jobs` → Verifica job attivo
2. Controlla log per errori
3. `/testcheck` → Test manuale
4. Verifica credenziali Spotify in .env
5. Controlla connessione internet server

### Database Corrotto

**Soluzione:**
1. Ripristina ultimo backup
2. `/reload` → Ricarica dati
3. `/stats` → Verifica integrità
4. Se necessario, ricostruisci da Spotify

### Notifiche Non Arrivano

**Checklist:**
1. `/users` → Verifica utenti registrati
2. Controlla file `notification_users.txt`
3. `/notify` → Test su te stesso
4. Verifica token bot in .env
5. Controlla rate limiting Telegram

### Job Non Partono

**Soluzione:**
1. Riavvia bot
2. `/jobs` → Verifica creazione
3. Controlla timezone
4. Verifica zoneinfo installato

---

## 💡 Tips & Tricks

### Monitoraggio Proattivo
```bash
# Setup alert se bot offline
*/5 * * * * pgrep -f "python.*bot.py" || \
  curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$ADMIN_CHAT_ID" -d "text=⚠️ Bot offline!"
```

### Statistiche Giornaliere Automatiche
```bash
# Invia stats ogni mattina alle 9:00
0 9 * * * curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$ADMIN_CHAT_ID" -d "text=/stats"
```

### Backup Automatico
```bash
# Backup ogni domenica alle 23:00
0 23 * * 0 curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$ADMIN_CHAT_ID" -d "text=/backup"
```

---

## 📱 Comandi da Mobile

Tutti i comandi funzionano identici da mobile! 

**Tip:** Salva questa lista nei "Messaggi Salvati" di Telegram per accesso rapido.

---

## 🔐 Sicurezza

- Solo il tuo `ADMIN_CHAT_ID` (configurato in .env) può eseguire questi comandi
- Altri utenti ricevono: "❌ Non sei autorizzato."
- Non condividere ADMIN_CHAT_ID con nessuno
- Tieni al sicuro il file .env

---

## ❓ FAQ

**Q: Posso avere più admin?**
A: Attualmente no, ma puoi modificare il codice per accettare una lista di chat_id.

**Q: I comandi sono case-sensitive?**
A: No, `/Stats` e `/stats` funzionano entrambi.

**Q: Posso schedulare un broadcast?**
A: Non nativamente, ma puoi usare crontab o aggiungere la funzionalità.

**Q: Come vedo il log completo?**
A: SSH nel server e `tail -f bot.log` o usa `journalctl -u office-cards-bot -f`

---

## 📞 Supporto

Se un comando non funziona:
1. Controlla i log
2. Verifica di essere admin (ADMIN_CHAT_ID corretto)
3. Riavvia il bot
4. Controlla questo documento

Per ulteriori info: vedi `README.md` e `CENTRALIZED_CHECK.md`
# Sistema di Check Centralizzato

Documentazione dettagliata del sistema di verifica nuovi episodi e pillole.

## 🎯 Panoramica

Il bot usa un **sistema centralizzato** per verificare nuovi contenuti:
- ✅ **Un solo job** controlla Spotify (invece di uno per utente)
- ✅ **Notifiche a tutti** gli utenti registrati
- ✅ **Efficiente**: riduce API calls del 99%
- ✅ **Scalabile**: funziona con 10 o 10,000 utenti

## 📅 Configurazione Attuale

### Episodi Principali
- **Frequenza**: Settimanale
- **Giorno**: Lunedì
- **Ora**: 17:00 (Europe/Rome)
- **Funzione**: `check_new_episode_centralized()`

### Pillole
- **Frequenza**: Giornaliera
- **Ora**: 12:00 (Europe/Rome)
- **Funzione**: `check_new_pill_centralized()`

## 🔄 Flusso di Lavoro

### 1. Setup Iniziale

```
Utente → /start → Bot
                   ↓
          _setup_centralized_jobs()
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
  Episode Job            Pill Job
  (Lunedì 17:00)        (Ogni giorno 12:00)
```

Il job viene creato **solo una volta** alla prima esecuzione di `/start`. Successivi `/start` non creano job duplicati grazie a:

```python
if self.episode_check_job is None:
    # Crea job solo se non esiste
```

### 2. Check Episodi (Lunedì 17:00)

```
Scheduler Telegram
      ↓
check_new_episode_centralized()
      ↓
┌─────┴─────────────────────────┐
│ 1. Chiama Spotify API         │
│ 2. Prendi ultimo episodio     │
└─────┬─────────────────────────┘
      ↓
   È nuovo?
      ↓
   No → Fine
      ↓
   Sì → Continua
      ↓
┌─────┴─────────────────────────┐
│ 3. Scraping shownotes         │
│ 4. Aggiungi a database        │
│ 5. Reload database            │
└─────┬─────────────────────────┘
      ↓
┌─────┴─────────────────────────┐
│ 6. Prendi lista utenti        │
│    (notification_users.txt)   │
└─────┬─────────────────────────┘
      ↓
┌─────┴─────────────────────────┐
│ 7. Per ogni utente:           │
│    - Invia notifica           │
│    - Se bloccato → rimuovi    │
└─────┬─────────────────────────┘
      ↓
┌─────┴─────────────────────────┐
│ 8. Notifica admin con stats   │
└───────────────────────────────┘
```

### 3. Gestione Utenti

**Aggiunta utente** (quando fa `/start`):
```python
def add_user_to_notifications(chat_id):
    # Leggi file notification_users.txt
    # Aggiungi chat_id se non presente
    # Salva file
```

**Rimozione utente** (se ha bloccato il bot):
```python
try:
    send_message(chat_id)
except "blocked by the user":
    remove_user_from_notifications(chat_id)
```

## 📊 Confronto: Prima vs Dopo

### Vecchio Sistema (Per-User)
```
100 utenti × 24 check/giorno = 2,400 API calls/giorno
├── Utente 1: job ogni ora
├── Utente 2: job ogni ora
├── Utente 3: job ogni ora
└── ...

❌ Problemi:
- 2,400 chiamate Spotify/giorno
- CPU sempre attiva
- Latenza variabile (0-59 minuti)
- Non scala
```

### Nuovo Sistema (Centralizzato)
```
1 job × 1 check/settimana = 1 API call/settimana

✅ Vantaggi:
- 1 sola chiamata Spotify
- CPU idle 99.9% del tempo
- Notifica simultanea a tutti
- Scala infinitamente
```

**Riduzione API calls: 99.96%** 🎉

## ⚙️ Personalizzazione

### Cambiare Frequenza Check Episodi

Nel file `bot.py`, metodo `_setup_centralized_jobs()`:

#### Opzione 1: Settimanale (Attuale)
```python
self.episode_check_job = context.job_queue.run_daily(
    self.check_new_episode_centralized,
    time=time(17, 0, 0, tzinfo=ZoneInfo('Europe/Rome')),
    days=(0,),  # 0=Lunedì
    name='weekly_episode_check'
)
```

**Cambia giorni:**
- Lunedì: `days=(0,)`
- Mercoledì: `days=(2,)`
- Lunedì + Giovedì: `days=(0, 3)`
- Tutti i giorni feriali: `days=(0, 1, 2, 3, 4)`

#### Opzione 2: Giornaliero
```python
self.episode_check_job = context.job_queue.run_daily(
    self.check_new_episode_centralized,
    time=time(17, 0, 0, tzinfo=ZoneInfo('Europe/Rome')),
    # Nessun parametro days = ogni giorno
    name='daily_episode_check'
)
```

#### Opzione 3: Ogni N Ore
```python
self.episode_check_job = context.job_queue.run_repeating(
    self.check_new_episode_centralized,
    interval=21600,  # 6 ore in secondi
    first=10,        # Primo check dopo 10 secondi
    name='hourly_episode_check'
)
```

**Intervalli comuni:**
- 1 ora: `interval=3600`
- 6 ore: `interval=21600`
- 12 ore: `interval=43200`

#### Opzione 4: Orari Multipli
```python
# Check alle 9:00 e alle 18:00
context.job_queue.run_daily(
    self.check_new_episode_centralized,
    time=time(9, 0, 0, tzinfo=ZoneInfo('Europe/Rome')),
    name='morning_check'
)
context.job_queue.run_daily(
    self.check_new_episode_centralized,
    time=time(18, 0, 0, tzinfo=ZoneInfo('Europe/Rome')),
    name='evening_check'
)
```

### Cambiare Timezone

```python
from zoneinfo import ZoneInfo

# Italia
time=time(17, 0, 0, tzinfo=ZoneInfo('Europe/Rome'))

# New York
time=time(17, 0, 0, tzinfo=ZoneInfo('America/New_York'))

# UTC
time=time(17, 0, 0, tzinfo=ZoneInfo('UTC'))
```

## 🐛 Debugging

### Verificare Job Attivi

```python
# In bot.py, aggiungi comando admin
async def jobs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra job attivi (solo admin)"""
    if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
        return
    
    jobs = context.job_queue.jobs()
    text = f"📋 <b>Job Attivi: {len(jobs)}</b>\n\n"
    
    for job in jobs:
        text += f"• {job.name}\n"
        if hasattr(job, 'next_t') and job.next_t:
            next_run = job.next_t.astimezone(ZoneInfo('Europe/Rome'))
            text += f"  Prossima esecuzione: {next_run.strftime('%d/%m/%Y %H:%M:%S')}\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

# Registra handler
application.add_handler(CommandHandler('jobs', self.jobs_command))
```

### Test Manuale Check

```python
# In bot.py, aggiungi comando admin
async def test_check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Esegue check manuale (solo admin)"""
    if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
        return
    
    await update.message.reply_text("🔍 Eseguo check manuale...")
    await self.check_new_episode_centralized(context)
    await update.message.reply_text("✅ Check completato")

# Uso: /testcheck
```

### Log Check

Il bot logga automaticamente ogni check:

```
2025-01-24 17:00:00 - __main__ - INFO - 🔍 Running centralized episode check...
2025-01-24 17:00:01 - __main__ - INFO - No new episode found
```

Oppure:

```
2025-01-24 17:00:00 - __main__ - INFO - 🔍 Running centralized episode check...
2025-01-24 17:00:02 - __main__ - INFO - 🎉 New episode detected: 150 Intervista con...
2025-01-24 17:00:05 - __main__ - INFO - 📢 Notifying 247 users...
2025-01-24 17:02:15 - __main__ - INFO - ✅ Episode notification complete: 245 sent, 2 failed
```

## 📁 File Coinvolti

### notification_users.txt
```
123456789
987654321
555444333
```

Ogni riga = un chat_id da notificare.

**Gestito automaticamente da:**
- `add_user_to_notifications()` → aggiunge utente
- `remove_user_from_notifications()` → rimuove utente

### database.csv
Viene aggiornato quando c'è un nuovo episodio:
```python
self.db.add_episode(latest_episode)
self.db.reload()
```

## 🔒 Sicurezza

### Evitare Job Duplicati

Il bot previene job duplicati:
```python
if self.episode_check_job is None:
    self._setup_centralized_jobs(context)
```

### Rate Limiting Spotify

Spotify API ha limiti:
- **Anonymous**: ~100 richieste/ora
- **Autenticato**: Illimitato (praticamente)

Con check settimanale: **1 richiesta/settimana** → nessun problema!

### Gestione Errori

Ogni check è protetto:
```python
try:
    # Check episodi
except Exception as e:
    logger.error(...)
    # Notifica admin
    send_message(admin, f"Errore: {e}")
```

Se il check fallisce, il bot:
1. Logga l'errore
2. Notifica l'admin
3. Continua a funzionare normalmente
4. Riproverà al prossimo scheduled time

## 📈 Monitoraggio

### Metriche Utili

```python
# Numero utenti attivi
users = len(self.db.get_notification_users())

# Success rate notifiche
success_rate = success_count / (success_count + fail_count)

# Tempo medio invio
import time
start = time.time()
# ... send notifications ...
duration = time.time() - start
avg_time = duration / len(users)
```

### Alert Admin

Il bot notifica automaticamente l'admin:
- ✅ Quando trova un nuovo episodio
- ✅ Con statistiche di invio
- ❌ Quando ci sono errori

```python
await context.bot.send_message(
    chat_id=ADMIN_CHAT_ID,
    text=f"✅ Episodio notificato: {success}/{total} utenti"
)
```

## 🚀 Best Practices

1. **Start con check settimanale** → meno carico, sufficiente per podcast
2. **Monitora i log** → verifica che funzioni
3. **Test in staging** → prima di modificare frequenza
4. **Backup notification_users.txt** → lista preziosa!
5. **Alert admin** → sapere sempre cosa succede

## ❓ FAQ

**Q: E se l'episodio esce il martedì ma check è lunedì?**
A: Sarà notificato il lunedì successivo. Per catturare prima, usa check giornaliero o ogni 6 ore.

**Q: Posso avere check diversi per episodi e pillole?**
A: Sì! Sono due job separati, configurabili indipendentemente.

**Q: Cosa succede se il bot è offline durante il check?**
A: Il job viene skippato. Al prossimo riavvio, verrà eseguito al prossimo orario schedulato.

**Q: Come faccio un check immediato?**
A: Usa il comando `/testcheck` (admin) o riavvia il bot (esegue check dopo 10 secondi).

**Q: Troppi utenti = notifiche lente?**
A: Con 1000 utenti ci vogliono ~5-10 minuti. Telegram limita a ~30 msg/secondo. Per grandi volumi considera [questo](https://core.telegram.org/bots/faq#broadcasting-to-users).
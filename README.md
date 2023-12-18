# Office of Cards Bot

![Office of Cards Logo](Logo.png)

Benvenuto nel repository del bot Telegram per il podcast "Office of Cards". Questo bot fornisce un'interfaccia interattiva per esplorare gli episodi del podcast e ricevere notifiche sui nuovi contenuti.

Aggiungi il bot su telegram al seguente link --> [Office of Cards Bot](https://t.me/office_of_card_bot)

## Funzionalità Principali

- **Notifiche di Nuovi Episodi:** Ricevi avvisi quando viene rilasciato un nuovo episodio del podcast.
- **Esplorazione degli Episodi:** Cerca e visualizza informazioni dettagliate su specifici episodi per categoria, ospite o numero.
- **Pillole Casuali:** Ascolta un episodio casuale del podcast *Pillole di Office of Cards*.

## Come Contribuire

Se vuoi contribuire a migliorare questo bot, segui questi passaggi:

- **Fork del Repository:** Fai il fork di questo repository sul tuo account GitHub se vuoi sperimentare liberamente.
- **Apri una issue:** Apri una issue su Github nell'apposita sezione per segnalare bug o proporre nuove features

1. **Installazione Dipendenze con Anaconda:** Assicurati di avere Anaconda installato e utilizza l'environment.yml per creare l'ambiente con le dipendenze necessarie.
    ```bash
    conda env create -f environment.yml
    conda activate nome_ambiente
    ```
2. **Lavora sulle modifiche:** Apri il tuo editor preferito e inizia a contribuire! Editor consigliato: VSCode
3. **Push e Pull Request:** Quando sei soddisfatto delle tue modifiche, effettua il push sul tuo repository e invia una pull request.

## Segnalazione problemi e suggerimenti
**Per segnalare un problema (bug) o suggerire nuove funzionalità:**
1. Vai alla sezione "Issues" nel menu superiore della pagina GitHub.
2. Clicca su "New Issue".
3. Seleziona un modello appropriato (Bug Report, Feature Request, ecc.).
4. Compila il modello fornendo tutte le informazioni necessarie.
5. Clicca su "Submit new issue".
6. Sentiti libero di lavorarci tu stesso.

## Configurazione

Per testare in autonomia il bot quando effettui delle modifiche, avrai bisogno di ottenere le tue chiavi personali per i seguenti servizi:
- **Spotify:** segui le indicazioni sulla [pagina ufficiale](https://developer.spotify.com/documentation/web-api/tutorials/getting-started) di Spotify for Developers
- **Telegram:** crea un nuovo bot con [Botfather](https://telegram.me/BotFather) ed ottieni il tuo token personale

Una volta ottenute le tue chiavi personali, sostituiscile nel file `keys.py` nel seguente modo:
``` py
spotify_client_id = "YOUR_SPOTIFY_CLIENT_ID"
spotify_client_secret = "YOUR_SPOTIFY_SECRET_KEY"

bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'
```

Assicurati che il file `keys.py` sia correttamente aggiunto in `.gitignore`

## Contatti

Per domande, problemi o suggerimenti, puoi contattare il team di sviluppo:

- Simone Cecconi - [smn.ccc@gmail.com](mailto:smn.ccc@gmail.com)

Grazie per il tuo interesse e il tuo contributo!

---

© 2023 Office of Cards Bot. Licenza: [Licenza del Progetto](.LICENSE.md)
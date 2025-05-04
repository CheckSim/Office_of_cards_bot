#!/usr/bin/env python
# coding: utf-8

# Import delle librerie necessarie
import random
import requests
import spotipy
from datetime import datetime
import pandas as pd
import numpy as np
import os

from spotipy.oauth2 import SpotifyClientCredentials
from bs4 import BeautifulSoup
from telegram import Update, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, Application, MessageHandler, CallbackQueryHandler, filters, CallbackContext, ConversationHandler

# Import di costanti e chiavi API da altri moduli
from constants import *

spotify_client_id, spotify_client_secret = get_spotify_credentials()
bot_token = get_bot_token()

import nest_asyncio
nest_asyncio.apply()

# Definizione di alcune costanti
last_episode = "Ultimo Episodio"
random_episode = "Pillola Casuale"
category_search = "Ricerca per categoria"
guest_search = "Ricerca Ospite"

db_path = './data/db.csv'
stats_path = './data/stats.csv'
episode_path = './data/episode.csv'
pills_path = './data/pills.csv'

# Funzione per ricaricare dati da file CSV e aggiornare variabili globali
def reloads():
    global sheet1, last_id, last_part, categories, guests, text_start, text_error
    
    sheet1 = pd.read_csv(db_path, engine = 'python', encoding = 'latin1')
    sheet1['Guest_lower'] = sheet1['Guest'].str.lower()

    last_id = max(sheet1['Id'])
    last_part = max(sheet1[sheet1['Id'] == last_id]['Part'])

    categories = list(set(sheet1['Category']))
    try:
        categories.remove(np.nan)
    except:
        pass
    categories.append('<-- INDIETRO')

    guests = list(set(sheet1['Guest']))
    try:
        guests.remove(np.nan)
    except:
        pass
    guests.remove('*')
    guests.append('<-- INDIETRO')
    
    text_error = f"Non sono stato in grado di trovare la puntata desiderata.\n\nPer favore, seleziona una scelta dal menù principale, oppure scrivimi il nome di un ospite, oppure scrivimi un numero da 0 a {max(sheet1['Id'])}"
    text_start = f"Seleziona una scelta dal menù principale, oppure scrivimi il nome e cognome di un ospite, oppure scrivimi un numero da 0 a {max(sheet1['Id'])}"

# Funzione asincrona per notificare nuovi episodi
async def notify_episode(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        global sheet1
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret))
        results = sp._get(spotify_url, limit = 50)
        current_last_id = max(sheet1['Id'])
        last_title = []
        last_title.append(results['items'][0]['name'])
        splitted_title = last_title[0].split(' ')
        if splitted_title[0] == 'Office':
            splitted_title.remove('Office')
            splitted_title.remove('of')
            splitted_title.remove('Cards')
            splitted_title.remove('-')
        last_title[0] = ' '.join(splitted_title)
        new_id, new_part = id_part_finder(last_title[0])
        if ((new_id == current_last_id) and (new_part == max(sheet1[sheet1['Id'] == current_last_id]['Part']))):
            pass
        else:
            new_episode = pd.DataFrame(last_title, columns = ['Titolo'])
            new_episode['Id'] = new_id
            new_episode['Part'] = new_part
            new_episode['Spotify_URL'] = results['items'][0]['external_urls']['spotify']
            new_episode['Description'] = results['items'][0]['description']
            new_episode['Category'] = category_finder(last_title[0])
            new_episode['GPT'] = '*'
            new_episode['Sottotitolo'] = '*'
            new_episode['Shownotes'], new_episode['Guest'] = shownotes_names(new_id)
            new_episode['Google_url'] = 'deprecated'
            new_episode.to_csv(episode_path)
            if (new_episode['Shownotes'].values == '*') or (new_episode['Guest'].values == '*'):
                await context.bot.send_message(chat_id=311429528, text = f"* in Shownotes url o Guest. Controllare.", parse_mode='HTML')
            else:
                episode = pd.read_csv(episode_path)
                buttons = buttons_generator(episode)
                await context.bot.send_message(chat_id=context.job.chat_id, text = f"<b>Nuovo episodio del tuo podcast preferito!</b>", parse_mode='HTML')
                await context.bot.send_message(chat_id=context.job.chat_id, text = f"<b>{episode['Titolo'].values[0]}</b> \n\n {episode['Description'].values[0]}", parse_mode='HTML', reply_markup = InlineKeyboardMarkup(buttons))
                sheet1 = pd.concat([sheet1, new_episode], ignore_index = True)
                sheet1.to_csv(db_path, index = False)
    except Exception as e:
        await context.bot.send_message(chat_id=311429528, text = f"Error: {e}", parse_mode='HTML')
    else:
        reloads()

# Funzione per ottenere gli shownotes di un episodio
def shownotes_names(id_episodio):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    resp = requests.get('https://officeofcards.com/ospite/', headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')

    containers = soup.find_all('div', attrs={'class':'container-overlay'})

    if id_episodio > int(containers[0].find_all('span')[0].text.split()[-1]):
        #await context.bot.send_message(chat_id=311429528, text = f"<b>Ancora non è stata pubblicata l'ultima shownote!</b>", parse_mode='HTML')
        return '*','*'
    else:
        for container in containers:
            if id_episodio == int(container.find_all('span')[0].text.split()[-1]):
                return container.a['href'], container.find_all('span')[1].text

# Funzione per ottenere l'URL di un episodio su Google Podcast
def google_url():
    response = requests.get(google_podcast_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    google_episode = soup.find_all('a', attrs={'class':"D9uPgd"})[0]
    url = 'https://podcasts.google.com/' + google_episode['href'][2:]
    return url

# Funzione per trovare la categoria di un episodio
def category_finder(string):
    i = string.find('[')
    id_ep, part = id_part_finder(string)
    
    if id_ep == 0:
        return 'INTRO'
    elif id_ep == 3:
        return 'Q&A'
    elif id_ep == 31:
        return 'Q&A'
    elif i == -1:
        return 'INTERVISTA'
    else:
        return string[string.find('[')+1:string.find(']')]

# Funzione per trovare ID e parte di un episodio a partire dal suo titolo
def id_part_finder(stringa):
    splitted = stringa.split(' ')
        
    id_part = splitted[0].split('_')
    
    try: 
        id_ep = int(id_part[0])
    except:
        id_ep = float('NaN')
    
    if len(id_part) == 1:
        part = 1
    else:
        part = int(id_part[1])

    return id_ep, part


# Funzione per gestire il comando di start del bot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reloads()
    buttons_menu = [[KeyboardButton(last_episode), KeyboardButton(random_episode)], [KeyboardButton(category_search),KeyboardButton(guest_search)]]
    await context.bot.send_message(chat_id = update.effective_chat.id, text = text_start, reply_markup = ReplyKeyboardMarkup(buttons_menu, resize_keyboard = True))
    
    context.job_queue.run_repeating(notify_episode, chat_id = update.effective_chat.id, interval=3600, first=10)
    #context.job_queue.run_daily(notify_episode, time = time(17, 47, 00, tzinfo=ZoneInfo('Europe/Rome')), days = (1), chat_id = update.effective_chat.id, name='dailycheck', data = context)
    context.job_queue.run_repeating(check_pill, chat_id = update.effective_chat.id, interval=3600, first=15)

# Funzione asincrona per inviare un episodio in chat
async def send_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    episode = pd.read_csv(episode_path)
    buttons = buttons_generator(episode)
    await context.bot.send_message(chat_id = update.effective_chat.id, text = f"<b>{episode['Titolo'].values[0]}</b> \n\nCiao, se trovi utile questo bot, puoi sostenerlo facendo una semplice donazione tramite i link che trovi in fondo al messaggio. \n\n{episode['Description'].values[0]}", parse_mode='HTML', reply_markup = InlineKeyboardMarkup(buttons))

# Funzione asincrona per gestire la ricerca per categorie
async def categories_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories_buttons = []
    for elem in categories:
        categories_buttons.append([KeyboardButton(elem)])
    await context.bot.send_message(chat_id = update.effective_chat.id, text = 'Seleziona la categoria da ricercare:', reply_markup = ReplyKeyboardMarkup(categories_buttons, resize_keyboard = True))

# Funzione asincrona per gestire la ricerca per ospiti
async def guestf_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guest_buttons = []
    for elem in guests:
        guest_buttons.append([KeyboardButton(elem)])
    await context.bot.send_message(chat_id = update.effective_chat.id, text = "Seleziona l'ospite da ricercare:", reply_markup = ReplyKeyboardMarkup(guest_buttons, resize_keyboard = True))

# Funzione asincrona per gestire le richieste dell'utente. Si tratta della colonna portante del bot.
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global id_episodio_richiesto

    try:
        int(update.message.text)

    except:
        if last_episode in update.message.text:
            id_episode = max(sheet1['Id'])
            part_episode = max(sheet1[sheet1['Id'] == id_episode]['Part'])
            episode_info = sheet1[sheet1['Id'] == id_episode][sheet1['Part'] == part_episode]
            episode_info.to_csv(episode_path)
            stats(str(update.message.chat_id), 'Last')
            await send_episode(update, context)

        elif random_episode in update.message.text:
            await random_episode_funct(update, context)
            
        elif update.message.text == '<-- INDIETRO':
            await start_command(update, context)

        elif category_search in update.message.text:
            await categories_search(update, context)
            
        elif guest_search in update.message.text:
            await guestf_search(update, context)

        elif update.message.text in categories:
            if update.message.text == 'INTERVISTA':
                await guestf_search(update, context)
            else:
                episodes = sheet1[sheet1['Category'] == update.message.text]
                if len(episodes) == 0:
                    await context.bot.send_message(chat_id = update.effective_chat.id, text = text_error)
                elif len(episodes) == 1:
                    episodes.to_csv(episode_path)
                    stats(str(update.message.chat_id), 'Category ' + update.message.text)
                    await send_episode(update, context) 
                else:
                    episodes_buttons = []
                    for title in list(episodes['Titolo']):
                        episodes_buttons.append([KeyboardButton(title)])
                    episodes_buttons.append([KeyboardButton('<-- INDIETRO')])
                    stats(str(update.message.chat_id), 'Category ' + update.message.text)
                    await context.bot.send_message(chat_id = update.effective_chat.id, text = f'Ho trovato {len(episodes)} episodi nella mia ricerca. Scegli quale vuoi ascoltare cliccando uno dei tasti qui sotto.', reply_markup = ReplyKeyboardMarkup(episodes_buttons, resize_keyboard = True))
                    
        elif update.message.text.lower() in sheet1['Titolo'].str.lower().unique():
            episode = sheet1[sheet1['Titolo'] == update.message.text]
            episode.to_csv(episode_path)
            await send_episode(update, context)

        elif update.message.text.lower() in sheet1['Guest_lower'].unique():
            episodes = sheet1[sheet1['Guest_lower'] == update.message.text.lower()]
            if len(episodes) == 0:
                await context.bot.send_message(chat_id = update.effective_chat.id, text = text_error)
            elif len(episodes) == 1:
                episodes.to_csv(episode_path)
                await send_episode(update, context)
            else:
                episodes_buttons = []
                for title in list(episodes['Titolo']):
                    episodes_buttons.append([KeyboardButton(title)])
                episodes_buttons.append([KeyboardButton('<-- INDIETRO')])
                stats(str(update.message.chat_id), 'Guest ' + update.message.text)
                await context.bot.send_message(chat_id = update.effective_chat.id, text = f'Ho trovato {len(episodes)} episodi nella mia ricerca. Scegli quale vuoi ascoltare cliccando uno dei tasti qui sotto.', reply_markup = ReplyKeyboardMarkup(episodes_buttons, resize_keyboard = True))
                
        else:
            await context.bot.send_message(chat_id = update.effective_chat.id, text = text_error)

    else:
        id_episodio_richiesto = int(update.message.text)
        if id_episodio_richiesto in sheet1['Id']:
            if multiple_episodes(id_episodio_richiesto,'Id') == False:
                stats(str(update.message.chat_id), 'Numero')
                episode_info = sheet1[sheet1['Id'] == id_episodio_richiesto]
                episode_info.to_csv(episode_path)
                await send_episode(update, context)
            else:
                part_buttons = []
                for elem in sheet1[sheet1['Id'] == id_episodio_richiesto]['Part']:
                    part_buttons.append([InlineKeyboardButton(text = str(f"Parte {str(elem)}"), callback_data = str(elem))])
                stats(str(update.message.chat_id), 'Numero')
                await context.bot.send_message(chat_id = update.effective_chat.id, text = f'Ho trovato {len(part_buttons)} episodi nella mia ricerca. Scegli quale vuoi ascoltare cliccando uno dei tasti qui sotto.', reply_markup = InlineKeyboardMarkup(part_buttons))
        else:
            await context.bot.send_message(chat_id = update.effective_chat.id, text = text_error)

# Funzione per generare i bottoni sotto gli episodi richiesti.
def buttons_generator(episodio):
    #button_urls = episodio[['Spotify_URL', 'Google_url', 'Shownotes']]

    #buttons_text = ['🎧 Ascoltalo su Spotify 🎧', '🎧 Ascoltalo su Google Podcast 🎧', '📝 Shownotes 📝']

    # NB: ad oggi la funzione per ottenere li link a Google Podcast è stata deprecata perchè soffriva di troppi bug. Visto che nei piani di Big G c'è di rimuovere l'app podcast, per ora non ha senso riattivarla.
    
    button_urls = episodio[['Spotify_URL', 'Shownotes']]

    buttons_text = ['🎧 Ascoltalo su Spotify 🎧', '📝 Shownotes 📝']
    buttons = []

    for i, url_val in enumerate(button_urls.values[0]):
        if (pd.isna(url_val) == True) or (url_val == '*'):
            continue
        else:
            buttons.append([InlineKeyboardButton(text = str(buttons_text[i]), url = str(url_val))])

    buttons.append([InlineKeyboardButton(text = 'BuyMeACoffee☕️', url = 'https://buymeacoffee.com/SimoneCecconi'), InlineKeyboardButton(text = 'Donazione PayPal', url = 'https://www.paypal.com/paypalme/SimoneCecconi')])

    return buttons

# Funzione per ottenere le statistiche di utilizzo del podcast
def stats(chat_id, command):
    stats = pd.read_csv(stats_path)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    new_stat = pd.DataFrame({'Datetime': now, 'Chat ID': chat_id, 'Query': command}, index = [0])
    stats = pd.concat([stats, new_stat], ignore_index=True)
    stats.to_csv(stats_path, index = False)

# Funzione per determinare se l'episodlio in questione è composto di più parti o solo una.
def multiple_episodes(query, column):
    if len(sheet1[sheet1[column] == query]) > 1:
        return True
    else:
        return False

# Callback Query: serve in poche occasini, solo quando c'è un follow-up nella risposta dell'utente, come la scelda della parte dell'episodio che si vuole ascoltare.
async def cbq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    part_episode = int(update.callback_query.data)
    episodes = sheet1[sheet1['Id'] == id_episodio_richiesto]
    episode_info = episodes[episodes['Part'] == part_episode]
    buttons = buttons_generator(episode_info)
    await context.bot.send_message(chat_id = update.effective_chat.id, text = f"<b>{episode_info['Titolo'].values[0]}</b> \n\n {episode_info['Description'].values[0]}", parse_mode='HTML', reply_markup = InlineKeyboardMarkup(buttons))

# Serie di funzioni per permettere l'invio di un messaggio broadcast a tutti gli utenti
MESSAGGIO = 0

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id = update.effective_chat.id, text = f"Che messaggio vuoi mandare? Se ci ripensi scrivi in chat /cancel in chat.")
    
    return MESSAGGIO

async def mess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = pd.read_csv(stats_path)
    for listed_chat_id in stats['Chat ID'].unique():
        try:
            await context.bot.send_message(chat_id = int(listed_chat_id), text = f"{update.message.text}")
        except:
            continue
    return ConversationHandler.END
    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id = update.effective_chat.id, text = 'Ok. Quando vuoi inviare un messaggio a tutti gli user del bot scrivi /message in chat.')
    return ConversationHandler.END

# Funzione per gestire la richiesta di un episodio casuale
async def random_episode_funct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pills = pd.read_csv(pills_path)
    
    title_pill = random.choice(pills['Titolo'])
    pill = pills[pills['Titolo'] == title_pill]
        
    shownotes_urls = sheet1[sheet1['Id'] == pill['Id'].values[0]]['Shownotes']
    
    shownotes_url = shownotes_urls.to_list()
    
    #button_urls = [pill['Spotify_URL'].values[0], pill['Google_url'].values[0], shownotes_url[0]]

    #buttons_text = ['🎧 Ascoltalo su Spotify 🎧', '🎧 Ascoltalo su Google Podcast 🎧', '📝 Shownotes 📝']
    
    button_urls = [pill['Spotify_URL'].values[0], shownotes_url[0]]

    buttons_text = ['🎧 Ascoltalo su Spotify 🎧', '📝 Shownotes 📝']
    buttons = []

    for i, url_val in enumerate(button_urls):
        if pd.isna(url_val) == True or (url_val == '*'):
            continue
        else:
            buttons.append([InlineKeyboardButton(text = str(buttons_text[i]), url = str(url_val))])
    buttons.append([InlineKeyboardButton(text = 'BuyMeACoffee☕️', url = 'https://buymeacoffee.com/SimoneCecconi'), InlineKeyboardButton(text = 'Donazione PayPal', url = 'https://www.paypal.com/paypalme/SimoneCecconi')])
    stats(str(update.message.chat_id), 'Random')
    await context.bot.send_message(chat_id = update.effective_chat.id, text = f"<b>{pill['Titolo'].values[0]}</b> \n\n {pill['Description'].values[0]}", parse_mode='HTML', reply_markup = InlineKeyboardMarkup(buttons))
    
# Funzione per aggiornare il database di episodi che escono sul podcast "Pillole di Office of Cards"
def check_pill(context: ContextTypes.DEFAULT_TYPE):
    pills = pd.read_csv(pills_path)
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret))
    results = sp._get(spotify_url_pills, limit = 50)

    titles = []
    Spotify_URLS = []
    descriptions = []
    ids = []

    i = 0
    titles.append(results['items'][i]['name'])
    
    if titles[0] in pills['Titolo'].to_list():
        return
    else:
        Spotify_URLS.append(results['items'][i]['external_urls']['spotify'])
        descriptions.append(results['items'][i]['description'])

        for elem in descriptions:
            D = elem.split(' ')
            for elem2 in D:
                try:
                    id_ep = int(elem2)
                except:
                    pass
                else:
                    ids.append(id_ep)


        new_pill = pd.DataFrame(titles, columns = ['Titolo'])
        new_pill['Spotify_URL'] = Spotify_URLS
        new_pill['Description'] = descriptions
        new_pill['Id'] = ids
        
        pills = pd.concat([pills, new_pill], ignore_index = True)
        pills.to_csv(pills_path, index = False)        

# Funzione principale per far partire il bot
def main():
    try:
        reloads()
        updater = Application.builder().token(bot_token).build()

        updater.add_handler(CommandHandler('start', start_command))
        
        updater.add_handler(CallbackQueryHandler(cbq))
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("message", broadcast_message)],
            states={
                MESSAGGIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, mess)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        updater.add_handler(conv_handler)
        
        updater.add_handler(MessageHandler(filters.TEXT, message_handler))
        
        updater.run_polling()
        # updater.idle()
    except:
        pass

if __name__ == "__main__":
    main()

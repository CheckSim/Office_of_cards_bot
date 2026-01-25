#!/usr/bin/env python
# coding: utf-8

"""
Bot Telegram per Office of Cards Podcast
Versione refactorata con check centralizzato e migliore gestione
"""

import logging
from datetime import time
from zoneinfo import ZoneInfo
from typing import Optional, List
import random

import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from config import Config
from database_csv import Database
from spotify_service import SpotifyService
from web_scraper import WebScraper

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stati per ConversationHandler
MESSAGGIO = 0


class OfficeOfCardsBot:
    """Classe principale del bot Telegram"""
    
    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config)
        self.spotify = SpotifyService(config)
        self.scraper = WebScraper()
        
        # Track dei job centralizzati
        self.episode_check_job = None
        self.pill_check_job = None
        
        # Costanti UI
        self.LAST_EPISODE = "Ultimo Episodio"
        self.RANDOM_EPISODE = "Pillola Casuale"
        self.CATEGORY_SEARCH = "Ricerca per categoria"
        self.GUEST_SEARCH = "Ricerca Ospite"
        self.BACK = "<-- INDIETRO"
        
    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Genera la tastiera principale"""
        buttons = [
            [self.LAST_EPISODE, self.RANDOM_EPISODE],
            [self.CATEGORY_SEARCH, self.GUEST_SEARCH]
        ]
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    def get_category_keyboard(self) -> ReplyKeyboardMarkup:
        """Genera tastiera con categorie"""
        categories = self.db.get_categories()
        buttons = [[cat] for cat in categories]
        buttons.append([self.BACK])
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    def get_guest_keyboard(self) -> ReplyKeyboardMarkup:
        """Genera tastiera con ospiti"""
        guests = self.db.get_guests()
        buttons = [[guest] for guest in guests]
        buttons.append([self.BACK])
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    def create_episode_buttons(self, episode: pd.Series) -> List[List[InlineKeyboardButton]]:
        """Crea bottoni per un episodio"""
        buttons = []
        
        # Spotify
        if pd.notna(episode.get('Spotify_URL')) and episode['Spotify_URL'] != '*':
            buttons.append([InlineKeyboardButton(
                "🎧 Ascoltalo su Spotify 🎧",
                url=episode['Spotify_URL']
            )])
        
        # Shownotes
        if pd.notna(episode.get('Shownotes')) and episode['Shownotes'] != '*':
            buttons.append([InlineKeyboardButton(
                "📝 Shownotes 📝",
                url=episode['Shownotes']
            )])
        
        # Donazioni
        buttons.append([
            InlineKeyboardButton(
                "Ko-Fi☕️",
                url="https://ko-fi.com/simonececconi"
            ),
            InlineKeyboardButton(
                "Donazione PayPal",
                url="https://www.paypal.com/paypalme/SimoneCecconi"
            )
        ])
        
        return buttons
    
    def _setup_centralized_jobs(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Setup job centralizzati (eseguiti una volta sola)
        Più efficiente: un solo check invece di uno per utente
        """
        if self.episode_check_job is not None:
            return  # Già configurato
        
        # Check episodi settimanale (ogni lunedì alle 17:00)
        # Cambia days per altri giorni: 0=Lun, 1=Mar, 2=Mer, 3=Gio, 4=Ven, 5=Sab, 6=Dom
        self.episode_check_job = context.job_queue.run_daily(
            self.check_new_episode_centralized,
            time=time(17, 0, 0, tzinfo=ZoneInfo('Europe/Rome')),
            days=(0,),  # Solo lunedì
            name='weekly_episode_check'
        )
        
        # Alternative:
        # Per check GIORNALIERO (ogni giorno alle 17:00):
        # self.episode_check_job = context.job_queue.run_daily(
        #     self.check_new_episode_centralized,
        #     time=time(17, 0, 0, tzinfo=ZoneInfo('Europe/Rome')),
        #     name='daily_episode_check'
        # )
        
        # Per check OGNI 6 ORE:
        # self.episode_check_job = context.job_queue.run_repeating(
        #     self.check_new_episode_centralized,
        #     interval=21600,  # 6 ore
        #     first=10,
        #     name='hourly_episode_check'
        # )
        
        # Check pillole giornaliero (ogni giorno alle 12:00)
        self.pill_check_job = context.job_queue.run_daily(
            self.check_new_pill_centralized,
            time=time(12, 0, 0, tzinfo=ZoneInfo('Europe/Rome')),
            name='daily_pill_check'
        )
        
        logger.info("✅ Centralized jobs configured successfully")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce il comando /start"""
        try:
            self.db.reload()
            max_id = self.db.get_max_episode_id()
            
            text = (
                f"Benvenuto! Seleziona una scelta dal menù principale, "
                f"oppure scrivimi il nome e cognome di un ospite, "
                f"oppure un numero da 0 a {max_id}"
            )
            
            await update.message.reply_text(
                text,
                reply_markup=self.get_main_keyboard()
            )
            
            # Setup job centralizzati (solo la prima volta)
            self._setup_centralized_jobs(context)
            
            # Aggiungi utente alla lista notifiche
            self.db.add_user_to_notifications(update.effective_chat.id)
            
            logger.info(f"User {update.effective_chat.id} started the bot")
            
        except Exception as e:
            logger.error(f"Error in start_command: {e}", exc_info=True)
            await update.message.reply_text(
                "Si è verificato un errore. Riprova tra poco."
            )
    
    async def send_episode(self, update: Update, episode: pd.Series, prefix: str = ""):
        """Invia un episodio formattato"""
        try:
            title = episode['Titolo']
            description = episode.get('Description', 'Nessuna descrizione disponibile')
            
            text = f"<b>{title}</b>\n\n"
            if prefix:
                text += f"{prefix}\n\n"
            text += description
            
            buttons = self.create_episode_buttons(episode)
            
            await update.effective_chat.send_message(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            
        except Exception as e:
            logger.error(f"Error sending episode: {e}", exc_info=True)
            await update.effective_chat.send_message(
                "Errore nell'invio dell'episodio."
            )
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce i messaggi dell'utente"""
        try:
            message_text = update.message.text.strip()
            chat_id = str(update.effective_chat.id)
            
            # Ultimo episodio
            if message_text == self.LAST_EPISODE:
                await self.handle_last_episode(update, chat_id)
            
            # Episodio casuale (pillola)
            elif message_text == self.RANDOM_EPISODE:
                await self.handle_random_pill(update, chat_id)
            
            # Indietro
            elif message_text == self.BACK:
                await self.start_command(update, context)
            
            # Ricerca categoria
            elif message_text == self.CATEGORY_SEARCH:
                await update.message.reply_text(
                    "Seleziona la categoria da ricercare:",
                    reply_markup=self.get_category_keyboard()
                )
            
            # Ricerca ospite
            elif message_text == self.GUEST_SEARCH:
                await update.message.reply_text(
                    "Seleziona l'ospite da ricercare:",
                    reply_markup=self.get_guest_keyboard()
                )
            
            # Categoria selezionata
            elif message_text in self.db.get_categories():
                await self.handle_category_search(update, message_text, chat_id)
            
            # Ospite selezionato o ricerca per nome
            elif message_text.lower() in [g.lower() for g in self.db.get_guests()]:
                await self.handle_guest_search(update, message_text, chat_id)
            
            # Titolo esatto
            elif message_text in self.db.get_all_titles():
                await self.handle_title_search(update, message_text, chat_id)
            
            # Numero episodio
            elif message_text.isdigit():
                await self.handle_episode_number(update, context, int(message_text), chat_id)
            
            else:
                max_id = self.db.get_max_episode_id()
                await update.message.reply_text(
                    f"Non ho trovato quello che cerchi.\n\n"
                    f"Seleziona una scelta dal menù, scrivi il nome di un ospite, "
                    f"o un numero da 0 a {max_id}."
                )
                
        except Exception as e:
            logger.error(f"Error in message_handler: {e}", exc_info=True)
            await update.message.reply_text(
                "Si è verificato un errore. Riprova."
            )
    
    async def handle_last_episode(self, update: Update, chat_id: str):
        """Gestisce richiesta ultimo episodio"""
        episode = self.db.get_last_episode()
        if episode is not None:
            self.db.log_stat(chat_id, 'Last')
            await self.send_episode(update, episode)
        else:
            await update.message.reply_text("Nessun episodio trovato.")
    
    async def handle_random_pill(self, update: Update, chat_id: str):
        """Gestisce richiesta pillola casuale"""
        pill = self.db.get_random_pill()
        if pill is not None:
            self.db.log_stat(chat_id, 'Random')
            prefix = "Ciao! Se trovi utile questo bot, considera una donazione tramite i link in fondo."
            await self.send_episode(update, pill, prefix)
        else:
            await update.message.reply_text("Nessuna pillola disponibile.")
    
    async def handle_category_search(self, update: Update, category: str, chat_id: str):
        """Gestisce ricerca per categoria"""
        if category == 'INTERVISTA':
            await update.message.reply_text(
                "Seleziona l'ospite:",
                reply_markup=self.get_guest_keyboard()
            )
            return
        
        episodes = self.db.get_episodes_by_category(category)
        
        if len(episodes) == 0:
            await update.message.reply_text("Nessun episodio trovato per questa categoria.")
        
        elif len(episodes) == 1:
            self.db.log_stat(chat_id, f'Category {category}')
            await self.send_episode(update, episodes.iloc[0])
        
        else:
            self.db.log_stat(chat_id, f'Category {category}')
            buttons = [[title] for title in episodes['Titolo'].tolist()]
            buttons.append([self.BACK])
            
            await update.message.reply_text(
                f"Ho trovato {len(episodes)} episodi. Scegli quale ascoltare:",
                reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
            )
    
    async def handle_guest_search(self, update: Update, guest_name: str, chat_id: str):
        """Gestisce ricerca per ospite"""
        episodes = self.db.get_episodes_by_guest(guest_name)
        
        if len(episodes) == 0:
            await update.message.reply_text("Nessun episodio trovato per questo ospite.")
        
        elif len(episodes) == 1:
            self.db.log_stat(chat_id, f'Guest {guest_name}')
            await self.send_episode(update, episodes.iloc[0])
        
        else:
            self.db.log_stat(chat_id, f'Guest {guest_name}')
            buttons = [[title] for title in episodes['Titolo'].tolist()]
            buttons.append([self.BACK])
            
            await update.message.reply_text(
                f"Ho trovato {len(episodes)} episodi. Scegli quale ascoltare:",
                reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
            )
    
    async def handle_title_search(self, update: Update, title: str, chat_id: str):
        """Gestisce ricerca per titolo esatto"""
        episode = self.db.get_episode_by_title(title)
        if episode is not None:
            await self.send_episode(update, episode)
        else:
            await update.message.reply_text("Episodio non trovato.")
    
    async def handle_episode_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   episode_id: int, chat_id: str):
        """Gestisce ricerca per numero episodio"""
        episodes = self.db.get_episodes_by_id(episode_id)
        
        if len(episodes) == 0:
            max_id = self.db.get_max_episode_id()
            await update.message.reply_text(
                f"Episodio non trovato. Inserisci un numero da 0 a {max_id}."
            )
        
        elif len(episodes) == 1:
            self.db.log_stat(chat_id, 'Numero')
            await self.send_episode(update, episodes.iloc[0])
        
        else:
            # Episodio multi-parte
            self.db.log_stat(chat_id, 'Numero')
            context.user_data['episode_id'] = episode_id
            
            buttons = []
            for part in episodes['Part'].tolist():
                buttons.append([InlineKeyboardButton(
                    f"Parte {part}",
                    callback_data=f"part_{part}"
                )])
            
            await update.message.reply_text(
                f"Ho trovato {len(episodes)} parti. Scegli quale ascoltare:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce callback queries (selezione parti)"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data.startswith("part_"):
                part = int(query.data.split("_")[1])
                episode_id = context.user_data.get('episode_id')
                
                if episode_id:
                    episode = self.db.get_episode_by_id_and_part(episode_id, part)
                    if episode is not None:
                        await query.message.reply_text(
                            f"<b>{episode['Titolo']}</b>\n\n{episode.get('Description', '')}",
                            parse_mode='HTML',
                            reply_markup=InlineKeyboardMarkup(self.create_episode_buttons(episode))
                        )
                    
        except Exception as e:
            logger.error(f"Error in callback_query_handler: {e}", exc_info=True)
    
    async def check_new_episode_centralized(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Check centralizzato per nuovi episodi
        Notifica TUTTI gli utenti attivi - eseguito solo una volta
        """
        try:
            logger.info("🔍 Running centralized episode check...")
            
            # 1. Prendi ultimo episodio da Spotify
            latest_episode = self.spotify.get_latest_episode()
            
            if not latest_episode:
                logger.warning("No episode found on Spotify")
                return
            
            # 2. Controlla se è nuovo
            if not self.db.is_new_episode(latest_episode):
                logger.info("No new episode found")
                return
            
            logger.info(f"🎉 New episode detected: {latest_episode.get('Titolo')}")
            
            # 3. Scraping delle shownotes (se disponibili)
            latest_episode = self.scraper.update_episode_metadata(latest_episode)
            
            # 4. Aggiungi al database
            self.db.add_episode(latest_episode)
            self.db.reload()
            
            # 5. Recupera episodio completo
            episode = self.db.get_last_episode()
            if episode is None:
                logger.error("Could not retrieve newly added episode")
                return
            
            # 6. Prendi tutti gli utenti da notificare
            users_to_notify = self.db.get_notification_users()
            logger.info(f"📢 Notifying {len(users_to_notify)} users...")
            
            buttons = self.create_episode_buttons(episode)
            message_text = (
                f"<b>🎉 Nuovo episodio del tuo podcast preferito!</b>\n\n"
                f"<b>{episode['Titolo']}</b>\n\n"
                f"{episode.get('Description', '')}"
            )
            
            # 7. Invia a tutti gli utenti
            success_count = 0
            fail_count = 0
            
            for chat_id in users_to_notify:
                try:
                    await context.bot.send_message(
                        chat_id=int(chat_id),
                        text=message_text,
                        parse_mode='HTML',
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to notify user {chat_id}: {e}")
                    fail_count += 1
                    
                    # Se utente ha bloccato il bot, rimuovilo
                    if "blocked by the user" in str(e).lower():
                        self.db.remove_user_from_notifications(chat_id)
            
            logger.info(
                f"✅ Episode notification complete: "
                f"{success_count} sent, {fail_count} failed"
            )
            
            # 8. Notifica admin
            try:
                await context.bot.send_message(
                    chat_id=self.config.ADMIN_CHAT_ID,
                    text=(
                        f"✅ Nuovo episodio pubblicato e notificato\n"
                        f"📊 {success_count} utenti notificati, {fail_count} falliti\n"
                        f"🎧 {episode['Titolo']}"
                    )
                )
            except Exception as e:
                logger.warning(f"Could not notify admin: {e}")
                
        except Exception as e:
            logger.error(f"Error in centralized episode check: {e}", exc_info=True)
            
            # Notifica admin dell'errore
            try:
                await context.bot.send_message(
                    chat_id=self.config.ADMIN_CHAT_ID,
                    text=f"❌ Errore nel check episodi: {str(e)}"
                )
            except:
                pass
    
    async def check_new_pill_centralized(self, context: ContextTypes.DEFAULT_TYPE):
        """Check centralizzato per nuove pillole"""
        try:
            logger.info("🔍 Running centralized pill check...")
            
            latest_pill = self.spotify.get_latest_pill()
            
            if latest_pill and self.db.is_new_pill(latest_pill):
                self.db.add_pill(latest_pill)
                logger.info(f"💊 New pill added: {latest_pill.get('Titolo')}")
                
                # Notifica admin
                try:
                    await context.bot.send_message(
                        chat_id=self.config.ADMIN_CHAT_ID,
                        text=f"💊 Nuova pillola aggiunta: {latest_pill.get('Titolo')}"
                    )
                except Exception as e:
                    logger.warning(f"Could not notify admin: {e}")
            else:
                logger.info("No new pill found")
                
        except Exception as e:
            logger.error(f"Error in centralized pill check: {e}", exc_info=True)
    
    async def broadcast_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inizia processo broadcast (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("Non sei autorizzato.")
            return ConversationHandler.END
        
        await update.message.reply_text(
            "Che messaggio vuoi inviare a tutti gli utenti?\n"
            "Scrivi /cancel per annullare."
        )
        return MESSAGGIO
    
    async def broadcast_send(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Invia messaggio broadcast"""
        message = update.message.text
        chat_ids = self.db.get_notification_users()
        
        sent = 0
        failed = 0
        
        for chat_id in chat_ids:
            try:
                await context.bot.send_message(chat_id=int(chat_id), text=message)
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to send to {chat_id}: {e}")
                failed += 1
        
        await update.message.reply_text(
            f"Messaggio inviato!\n✅ Inviati: {sent}\n❌ Falliti: {failed}"
        )
        
        return ConversationHandler.END
    
    async def broadcast_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Annulla broadcast"""
        await update.message.reply_text("Broadcast annullato.")
        return ConversationHandler.END
    
    # ==========================================
    # COMANDI ADMIN
    # ==========================================
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra statistiche bot (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            # Statistiche database
            total_episodes = self.db.get_total_episodes()
            total_pills = self.db.get_total_pills()
            total_categories = len(self.db.get_categories())
            total_guests = len(self.db.get_guests())
            
            # Statistiche utenti
            total_users = len(self.db.get_notification_users())
            
            # Statistiche query
            total_queries = self.db.get_total_stats()
            
            # Top 5 query
            top_queries = self.db.get_top_queries(5)
            if top_queries:
                top_queries_text = "\n".join([f"  • {q}: {count}" for q, count in top_queries])
            else:
                top_queries_text = "  Nessuna query registrata"
            
            # Ultimo episodio
            last_ep = self.db.get_last_episode()
            last_ep_title = last_ep['Titolo'] if last_ep is not None else "N/A"
            
            text = f"""
📊 <b>Statistiche Bot</b>

<b>Database:</b>
🎧 Episodi: {total_episodes}
💊 Pillole: {total_pills}
📁 Categorie: {total_categories}
👥 Ospiti: {total_guests}

<b>Utenti:</b>
👤 Utenti attivi: {total_users}
🔍 Query totali: {total_queries}

<b>Top 5 ricerche:</b>
{top_queries_text}

<b>Ultimo episodio:</b>
{last_ep_title}
            """
            
            await update.message.reply_text(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in stats_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    
    async def jobs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra job schedulati attivi (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            jobs = context.job_queue.jobs()
            
            if not jobs:
                await update.message.reply_text("📋 Nessun job attivo")
                return
            
            text = f"📋 <b>Job Attivi: {len(jobs)}</b>\n\n"
            
            for job in jobs:
                text += f"<b>• {job.name}</b>\n"
                
                if hasattr(job, 'next_t') and job.next_t:
                    next_run = job.next_t.astimezone(ZoneInfo('Europe/Rome'))
                    text += f"  ⏰ Prossima esecuzione: {next_run.strftime('%d/%m/%Y %H:%M:%S')}\n"
                
                # Info aggiuntive
                if hasattr(job, 'interval'):
                    hours = job.interval / 3600
                    text += f"  🔄 Intervallo: {hours:.1f} ore\n"
                
                text += "\n"
            
            await update.message.reply_text(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in jobs_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    
    async def testcheck_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Esegue check manuale per nuovi episodi (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            await update.message.reply_text("🔍 Eseguo check manuale per nuovi episodi...")
            await self.check_new_episode_centralized(context)
            await update.message.reply_text("✅ Check completato! Controlla i log.")
            
        except Exception as e:
            logger.error(f"Error in testcheck_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore durante il check: {str(e)}")
    
    async def testpill_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Esegue check manuale per nuove pillole (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            await update.message.reply_text("🔍 Eseguo check manuale per nuove pillole...")
            await self.check_new_pill_centralized(context)
            await update.message.reply_text("✅ Check completato! Controlla i log.")
            
        except Exception as e:
            logger.error(f"Error in testpill_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore durante il check: {str(e)}")
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista utenti registrati per notifiche (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            users = self.db.get_notification_users()
            
            text = f"👥 <b>Utenti Registrati: {len(users)}</b>\n\n"
            
            if len(users) <= 20:
                # Mostra tutti se pochi
                for i, user in enumerate(users, 1):
                    text += f"{i}. <code>{user}</code>\n"
            else:
                # Mostra primi 20 + conteggio
                for i, user in enumerate(users[:20], 1):
                    text += f"{i}. <code>{user}</code>\n"
                text += f"\n... e altri {len(users) - 20} utenti"
            
            await update.message.reply_text(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in users_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    
    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Crea e invia backup del database (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            import zipfile
            from pathlib import Path
            
            # Nome backup con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}.zip"
            backup_path = Path(backup_name)
            
            await update.message.reply_text("📦 Creando backup...")
            
            # Crea zip con tutti i file dati
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Database episodi
                if self.config.DB_PATH.exists():
                    zipf.write(self.config.DB_PATH, 'db.csv')
                
                # Statistiche
                if self.config.STATS_PATH.exists():
                    zipf.write(self.config.STATS_PATH, 'stats.csv')
                
                # Pillole
                if self.config.PILLS_PATH.exists():
                    zipf.write(self.config.PILLS_PATH, 'pills.csv')
                
                # Utenti notifiche
                notification_file = self.config.DATA_DIR / 'notification_users.txt'
                if notification_file.exists():
                    zipf.write(notification_file, 'notification_users.txt')
            
            # Invia file
            with open(backup_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=backup_name,
                    caption=f"📦 Backup del {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                )
            
            # Rimuovi file temporaneo
            backup_path.unlink()
            
            await update.message.reply_text("✅ Backup completato!")
            
        except Exception as e:
            logger.error(f"Error in backup_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore durante il backup: {str(e)}")
    
    async def reload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ricarica il database (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            await update.message.reply_text("🔄 Ricaricando database...")
            self.db.reload()
            
            total_episodes = self.db.get_total_episodes()
            total_pills = self.db.get_total_pills()
            
            await update.message.reply_text(
                f"✅ Database ricaricato!\n"
                f"🎧 {total_episodes} episodi\n"
                f"💊 {total_pills} pillole"
            )
            
        except Exception as e:
            logger.error(f"Error in reload_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    
    async def notify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Invia notifica di test a se stesso (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Non sei autorizzato.")
            return
        
        try:
            last_ep = self.db.get_last_episode()
            
            if last_ep is None:
                await update.message.reply_text("❌ Nessun episodio nel database")
                return
            
            buttons = self.create_episode_buttons(last_ep)
            
            await update.message.reply_text(
                f"<b>🎉 Nuovo episodio del tuo podcast preferito!</b>\n\n"
                f"<b>{last_ep['Titolo']}</b>\n\n"
                f"{last_ep.get('Description', '')}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            
            await update.message.reply_text("✅ Questa è come apparirà la notifica agli utenti")
            
        except Exception as e:
            logger.error(f"Error in notify_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    
    async def help_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra comandi admin disponibili (solo admin)"""
        if update.effective_chat.id != self.config.ADMIN_CHAT_ID:
            return
        
        text = """
🔧 <b>Comandi Admin</b>

<b>Informazioni:</b>
/stats - Statistiche bot
/jobs - Job schedulati attivi
/users - Lista utenti registrati

<b>Testing:</b>
/testcheck - Check manuale episodi
/testpill - Check manuale pillole
/notify - Anteprima notifica

<b>Gestione:</b>
/reload - Ricarica database
/backup - Crea backup database
/message - Broadcast messaggio
/cancel - Annulla broadcast

<b>Broadcast:</b>
1. /message
2. Scrivi il messaggio
3. Verrà inviato a tutti gli utenti
        """
        
        await update.message.reply_text(text, parse_mode='HTML')
    
    def run(self):
        """Avvia il bot"""
        try:
            application = Application.builder().token(self.config.BOT_TOKEN).build()
            
            # Handlers comandi base
            application.add_handler(CommandHandler('start', self.start_command))
            application.add_handler(CallbackQueryHandler(self.callback_query_handler))
            
            # Admin commands
            application.add_handler(CommandHandler('stats', self.stats_command))
            application.add_handler(CommandHandler('jobs', self.jobs_command))
            application.add_handler(CommandHandler('testcheck', self.testcheck_command))
            application.add_handler(CommandHandler('testpill', self.testpill_command))
            application.add_handler(CommandHandler('users', self.users_command))
            application.add_handler(CommandHandler('backup', self.backup_command))
            application.add_handler(CommandHandler('reload', self.reload_command))
            application.add_handler(CommandHandler('notify', self.notify_command))
            application.add_handler(CommandHandler('admin', self.help_admin_command))
            
            # Conversation handler per broadcast
            broadcast_handler = ConversationHandler(
                entry_points=[CommandHandler("message", self.broadcast_start)],
                states={
                    MESSAGGIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.broadcast_send)],
                },
                fallbacks=[CommandHandler("cancel", self.broadcast_cancel)],
            )
            application.add_handler(broadcast_handler)
            
            # Message handler (deve essere ultimo)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
            
            logger.info("🤖 Bot started successfully")
            logger.info("📅 Episode check: Weekly (Monday 17:00)")
            logger.info("💊 Pill check: Daily (12:00)")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            raise


def main():
    """Entry point"""
    config = Config()
    bot = OfficeOfCardsBot(config)
    bot.run()


if __name__ == "__main__":
    main()
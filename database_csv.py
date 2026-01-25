"""
Modulo per la gestione del database (CSV)
"""

import logging
from datetime import datetime
from typing import Optional, List
import pandas as pd
import numpy as np
from threading import Lock

logger = logging.getLogger(__name__)


class Database:
    """Gestisce l'accesso ai dati del bot"""
    
    def __init__(self, config):
        self.config = config
        self._lock = Lock()  # Per thread safety
        self.episodes_df = None
        self.pills_df = None
        self.stats_df = None
        self.reload()
    
    def reload(self):
        """Ricarica i dati dai file CSV"""
        with self._lock:
            try:
                # Carica episodi
                self.episodes_df = pd.read_csv(
                    self.config.DB_PATH,
                    encoding='utf-8'
                )
                
                # Crea colonna lowercase per ricerca guest
                if 'Guest' in self.episodes_df.columns:
                    self.episodes_df['Guest_lower'] = (
                        self.episodes_df['Guest']
                        .fillna('')
                        .str.lower()
                    )
                
                # Carica pillole
                self.pills_df = pd.read_csv(
                    self.config.PILLS_PATH,
                    encoding='utf-8'
                )
                
                # Carica stats
                self.stats_df = pd.read_csv(
                    self.config.STATS_PATH,
                    encoding='utf-8'
                )
                
                logger.info("Database reloaded successfully")
                
            except Exception as e:
                logger.error(f"Error reloading database: {e}", exc_info=True)
                raise
    
    def save_episodes(self):
        """Salva il dataframe episodi"""
        with self._lock:
            try:
                self.episodes_df.to_csv(self.config.DB_PATH, index=False, encoding='utf-8')
                logger.info("Episodes saved successfully")
            except Exception as e:
                logger.error(f"Error saving episodes: {e}", exc_info=True)
    
    def save_pills(self):
        """Salva il dataframe pillole"""
        with self._lock:
            try:
                self.pills_df.to_csv(self.config.PILLS_PATH, index=False, encoding='utf-8')
                logger.info("Pills saved successfully")
            except Exception as e:
                logger.error(f"Error saving pills: {e}", exc_info=True)
    
    def log_stat(self, chat_id: str, query: str):
        """Registra una statistica"""
        with self._lock:
            try:
                now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                new_stat = pd.DataFrame({
                    'Datetime': [now],
                    'Chat ID': [chat_id],
                    'Query': [query]
                })
                
                self.stats_df = pd.concat([self.stats_df, new_stat], ignore_index=True)
                self.stats_df.to_csv(self.config.STATS_PATH, index=False, encoding='utf-8')
                
            except Exception as e:
                logger.error(f"Error logging stat: {e}", exc_info=True)
    
    def get_max_episode_id(self) -> int:
        """Restituisce l'ID massimo degli episodi"""
        if self.episodes_df.empty or 'Id' not in self.episodes_df.columns:
            return 0
        return int(self.episodes_df['Id'].max())
    
    def get_last_episode(self) -> Optional[pd.Series]:
        """Restituisce l'ultimo episodio"""
        try:
            max_id = self.get_max_episode_id()
            if max_id == 0:
                return None
            
            episodes = self.episodes_df[self.episodes_df['Id'] == max_id]
            if episodes.empty:
                return None
            
            max_part = episodes['Part'].max()
            episode = episodes[episodes['Part'] == max_part]
            
            return episode.iloc[0] if not episode.empty else None
            
        except Exception as e:
            logger.error(f"Error getting last episode: {e}", exc_info=True)
            return None
    
    def get_categories(self) -> List[str]:
        """Restituisce lista di categorie uniche"""
        if 'Category' not in self.episodes_df.columns:
            return []
        
        categories = self.episodes_df['Category'].dropna().unique().tolist()
        # Rimuovi eventuali NaN
        categories = [c for c in categories if c and str(c) != 'nan']
        return sorted(categories)
    
    def get_guests(self) -> List[str]:
        """Restituisce lista di ospiti unici"""
        if 'Guest' not in self.episodes_df.columns:
            return []
        
        guests = self.episodes_df['Guest'].dropna().unique().tolist()
        # Rimuovi NaN e '*'
        guests = [g for g in guests if g and str(g) != 'nan' and g != '*']
        return sorted(guests)
    
    def get_all_titles(self) -> List[str]:
        """Restituisce tutti i titoli"""
        if 'Titolo' not in self.episodes_df.columns:
            return []
        return self.episodes_df['Titolo'].dropna().tolist()
    
    def get_episodes_by_category(self, category: str) -> pd.DataFrame:
        """Restituisce episodi per categoria"""
        if 'Category' not in self.episodes_df.columns:
            return pd.DataFrame()
        
        return self.episodes_df[self.episodes_df['Category'] == category].copy()
    
    def get_episodes_by_guest(self, guest_name: str) -> pd.DataFrame:
        """Restituisce episodi per ospite (case insensitive)"""
        if 'Guest_lower' not in self.episodes_df.columns:
            return pd.DataFrame()
        
        return self.episodes_df[
            self.episodes_df['Guest_lower'] == guest_name.lower()
        ].copy()
    
    def get_episode_by_title(self, title: str) -> Optional[pd.Series]:
        """Restituisce episodio per titolo esatto"""
        if 'Titolo' not in self.episodes_df.columns:
            return None
        
        episodes = self.episodes_df[self.episodes_df['Titolo'] == title]
        return episodes.iloc[0] if not episodes.empty else None
    
    def get_episodes_by_id(self, episode_id: int) -> pd.DataFrame:
        """Restituisce tutti gli episodi con un dato ID"""
        if 'Id' not in self.episodes_df.columns:
            return pd.DataFrame()
        
        return self.episodes_df[self.episodes_df['Id'] == episode_id].copy()
    
    def get_episode_by_id_and_part(self, episode_id: int, part: int) -> Optional[pd.Series]:
        """Restituisce episodio specifico per ID e parte"""
        if 'Id' not in self.episodes_df.columns or 'Part' not in self.episodes_df.columns:
            return None
        
        episodes = self.episodes_df[
            (self.episodes_df['Id'] == episode_id) & 
            (self.episodes_df['Part'] == part)
        ]
        
        return episodes.iloc[0] if not episodes.empty else None
    
    def get_random_pill(self) -> Optional[pd.Series]:
        """Restituisce una pillola casuale"""
        if self.pills_df.empty:
            return None
        
        import random
        return self.pills_df.iloc[random.randint(0, len(self.pills_df) - 1)]
    
    def get_all_chat_ids(self) -> List[str]:
        """Restituisce tutti i chat ID unici dalle statistiche"""
        if 'Chat ID' not in self.stats_df.columns or self.stats_df.empty:
            return []
        
        return self.stats_df['Chat ID'].unique().tolist()
    
    def is_new_episode(self, episode_data: dict) -> bool:
        """Verifica se un episodio è nuovo"""
        try:
            episode_id = episode_data.get('Id')
            episode_part = episode_data.get('Part')
            
            if episode_id is None or episode_part is None:
                return False
            
            # Controlla se esiste già
            existing = self.episodes_df[
                (self.episodes_df['Id'] == episode_id) & 
                (self.episodes_df['Part'] == episode_part)
            ]
            
            return existing.empty
            
        except Exception as e:
            logger.error(f"Error checking if episode is new: {e}", exc_info=True)
            return False
    
    def is_new_pill(self, pill_data: dict) -> bool:
        """Verifica se una pillola è nuova"""
        try:
            title = pill_data.get('Titolo')
            if not title:
                return False
            
            existing = self.pills_df[self.pills_df['Titolo'] == title]
            return existing.empty
            
        except Exception as e:
            logger.error(f"Error checking if pill is new: {e}", exc_info=True)
            return False
    
    def add_episode(self, episode_data: dict):
        """Aggiunge un nuovo episodio al database"""
        with self._lock:
            try:
                new_episode = pd.DataFrame([episode_data])
                self.episodes_df = pd.concat(
                    [self.episodes_df, new_episode], 
                    ignore_index=True
                )
                self.save_episodes()
                logger.info(f"Added new episode: {episode_data.get('Titolo')}")
                
            except Exception as e:
                logger.error(f"Error adding episode: {e}", exc_info=True)
    
    def add_pill(self, pill_data: dict):
        """Aggiunge una nuova pillola al database"""
        with self._lock:
            try:
                new_pill = pd.DataFrame([pill_data])
                self.pills_df = pd.concat(
                    [self.pills_df, new_pill], 
                    ignore_index=True
                )
                self.save_pills()
                logger.info(f"Added new pill: {pill_data.get('Titolo')}")
                
            except Exception as e:
                logger.error(f"Error adding pill: {e}", exc_info=True)
    
    def add_user_to_notifications(self, chat_id: int):
        """Aggiungi utente alla lista notifiche"""
        notifications_file = self.config.DATA_DIR / 'notification_users.txt'
        
        try:
            # Leggi utenti esistenti
            if notifications_file.exists():
                with open(notifications_file, 'r', encoding='utf-8') as f:
                    users = set(line.strip() for line in f if line.strip())
            else:
                users = set()
            
            # Aggiungi nuovo utente
            chat_id_str = str(chat_id)
            if chat_id_str not in users:
                users.add(chat_id_str)
                
                # Salva
                with open(notifications_file, 'w', encoding='utf-8') as f:
                    for user in sorted(users):
                        f.write(f"{user}\n")
                
                logger.info(f"Added user {chat_id} to notifications")
                    
        except Exception as e:
            logger.error(f"Error adding user to notifications: {e}", exc_info=True)
    
    def get_notification_users(self) -> List[str]:
        """Recupera lista utenti da notificare"""
        notifications_file = self.config.DATA_DIR / 'notification_users.txt'
        
        try:
            if not notifications_file.exists():
                return []
            
            with open(notifications_file, 'r', encoding='utf-8') as f:
                users = [line.strip() for line in f if line.strip()]
            
            return users
                
        except Exception as e:
            logger.error(f"Error getting notification users: {e}", exc_info=True)
            return []
    
    def remove_user_from_notifications(self, chat_id: int):
        """Rimuovi utente dalla lista (es. se ha bloccato il bot)"""
        notifications_file = self.config.DATA_DIR / 'notification_users.txt'
        
        try:
            if not notifications_file.exists():
                return
            
            with open(notifications_file, 'r', encoding='utf-8') as f:
                users = set(line.strip() for line in f if line.strip())
            
            chat_id_str = str(chat_id)
            if chat_id_str in users:
                users.discard(chat_id_str)
                
                with open(notifications_file, 'w', encoding='utf-8') as f:
                    for user in sorted(users):
                        f.write(f"{user}\n")
                
                logger.info(f"Removed user {chat_id} from notifications")
                    
        except Exception as e:
            logger.error(f"Error removing user from notifications: {e}", exc_info=True)
    
    # ==========================================
    # METODI PER COMPATIBILITÀ CON COMANDI ADMIN
    # ==========================================
    
    def get_total_episodes(self) -> int:
        """Restituisce numero totale episodi"""
        return len(self.episodes_df) if not self.episodes_df.empty else 0
    
    def get_total_pills(self) -> int:
        """Restituisce numero totale pillole"""
        return len(self.pills_df) if not self.pills_df.empty else 0
    
    def get_total_stats(self) -> int:
        """Restituisce numero totale statistiche"""
        return len(self.stats_df) if not self.stats_df.empty else 0
    
    def get_top_queries(self, limit: int = 5) -> List[tuple]:
        """Restituisce top N query più frequenti"""
        try:
            if self.stats_df.empty or 'Query' not in self.stats_df.columns:
                return []
            
            top = self.stats_df['Query'].value_counts().head(limit)
            return [(query, count) for query, count in top.items()]
            
        except Exception as e:
            logger.error(f"Error getting top queries: {e}", exc_info=True)
            return []
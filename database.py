"""
Database con SQLite invece di CSV
Drop-in replacement per database.py
"""

import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path
from threading import Lock
import pandas as pd

logger = logging.getLogger(__name__)


class Database:
    """Gestisce database SQLite invece di CSV"""
    
    def __init__(self, config):
        self.config = config
        self._lock = Lock()
        
        # Path database SQLite
        self.db_path = self.config.DATA_DIR / 'bot.db'
        
        # Inizializza database
        self._init_database()
        
        # Cache in memoria per performance (opzionale)
        self._cache_categories = None
        self._cache_guests = None
    
    def _init_database(self):
        """Crea tabelle se non esistono"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Tabella episodi
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        episode_id INTEGER NOT NULL,
                        part INTEGER DEFAULT 1,
                        title TEXT NOT NULL,
                        description TEXT,
                        category TEXT,
                        guest TEXT,
                        spotify_url TEXT,
                        shownotes_url TEXT,
                        gpt TEXT,
                        subtitle TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(episode_id, part)
                    )
                ''')
                
                # Indici per performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_episode_id 
                    ON episodes(episode_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_category 
                    ON episodes(category)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_guest 
                    ON episodes(guest)
                ''')
                
                # Tabella pillole
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pills (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        episode_id INTEGER,
                        title TEXT NOT NULL,
                        description TEXT,
                        spotify_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(title)
                    )
                ''')
                
                # Tabella statistiche
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        datetime TEXT NOT NULL,
                        chat_id TEXT NOT NULL,
                        query TEXT NOT NULL
                    )
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_chat_id 
                    ON stats(chat_id)
                ''')
                
                # Tabella utenti notifiche
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_users (
                        chat_id TEXT PRIMARY KEY,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active INTEGER DEFAULT 1
                    )
                ''')
                
                conn.commit()
                conn.close()
                
                logger.info("✅ Database SQLite initialized successfully")
                
            except Exception as e:
                logger.error(f"Error initializing database: {e}", exc_info=True)
                raise
    
    def _get_connection(self):
        """Crea connessione al database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permette accesso per nome colonna
        return conn
    
    def reload(self):
        """Ricarica cache (per compatibilità con versione CSV)"""
        with self._lock:
            # Invalida cache
            self._cache_categories = None
            self._cache_guests = None
            logger.info("Database cache cleared")
    
    def get_max_episode_id(self) -> int:
        """Restituisce l'ID massimo degli episodi"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT MAX(episode_id) FROM episodes')
            result = cursor.fetchone()[0]
            
            conn.close()
            return result if result is not None else 0
            
        except Exception as e:
            logger.error(f"Error getting max episode ID: {e}", exc_info=True)
            return 0
    
    def get_last_episode(self) -> Optional[dict]:
        """Restituisce l'ultimo episodio"""
        try:
            max_id = self.get_max_episode_id()
            if max_id == 0:
                return None
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM episodes 
                WHERE episode_id = ? 
                ORDER BY part DESC 
                LIMIT 1
            ''', (max_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'Id': row['episode_id'],
                    'Part': row['part'],
                    'Titolo': row['title'],
                    'Description': row['description'],
                    'Category': row['category'],
                    'Guest': row['guest'],
                    'Spotify_URL': row['spotify_url'],
                    'Shownotes': row['shownotes_url']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting last episode: {e}", exc_info=True)
            return None
    
    def get_categories(self) -> List[str]:
        """Restituisce lista di categorie uniche"""
        if self._cache_categories is not None:
            return self._cache_categories
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT category 
                FROM episodes 
                WHERE category IS NOT NULL 
                  AND category != ''
                ORDER BY category
            ''')
            
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            self._cache_categories = categories
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}", exc_info=True)
            return []
    
    def get_guests(self) -> List[str]:
        """Restituisce lista di ospiti unici"""
        if self._cache_guests is not None:
            return self._cache_guests
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT guest 
                FROM episodes 
                WHERE guest IS NOT NULL 
                  AND guest != '' 
                  AND guest != '*'
                ORDER BY guest
            ''')
            
            guests = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            self._cache_guests = guests
            return guests
            
        except Exception as e:
            logger.error(f"Error getting guests: {e}", exc_info=True)
            return []
    
    def get_all_titles(self) -> List[str]:
        """Restituisce tutti i titoli"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT title FROM episodes')
            titles = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return titles
            
        except Exception as e:
            logger.error(f"Error getting titles: {e}", exc_info=True)
            return []
    
    def get_episodes_by_category(self, category: str) -> pd.DataFrame:
        """Restituisce episodi per categoria"""
        try:
            conn = self._get_connection()
            
            df = pd.read_sql_query(
                'SELECT * FROM episodes WHERE category = ? ORDER BY episode_id, part',
                conn,
                params=(category,)
            )
            
            # Rinomina colonne per compatibilità
            df = df.rename(columns={
                'episode_id': 'Id',
                'title': 'Titolo',
                'description': 'Description',
                'category': 'Category',
                'guest': 'Guest',
                'spotify_url': 'Spotify_URL',
                'shownotes_url': 'Shownotes'
            })
            
            conn.close()
            return df
            
        except Exception as e:
            logger.error(f"Error getting episodes by category: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_episodes_by_guest(self, guest_name: str) -> pd.DataFrame:
        """Restituisce episodi per ospite (case insensitive)"""
        try:
            conn = self._get_connection()
            
            df = pd.read_sql_query(
                'SELECT * FROM episodes WHERE LOWER(guest) = LOWER(?) ORDER BY episode_id, part',
                conn,
                params=(guest_name,)
            )
            
            df = df.rename(columns={
                'episode_id': 'Id',
                'title': 'Titolo',
                'description': 'Description',
                'category': 'Category',
                'guest': 'Guest',
                'spotify_url': 'Spotify_URL',
                'shownotes_url': 'Shownotes'
            })
            
            conn.close()
            return df
            
        except Exception as e:
            logger.error(f"Error getting episodes by guest: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_episode_by_title(self, title: str) -> Optional[dict]:
        """Restituisce episodio per titolo esatto"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM episodes WHERE title = ?', (title,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'Id': row['episode_id'],
                    'Part': row['part'],
                    'Titolo': row['title'],
                    'Description': row['description'],
                    'Category': row['category'],
                    'Guest': row['guest'],
                    'Spotify_URL': row['spotify_url'],
                    'Shownotes': row['shownotes_url']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting episode by title: {e}", exc_info=True)
            return None
    
    def get_episodes_by_id(self, episode_id: int) -> pd.DataFrame:
        """Restituisce tutti gli episodi con un dato ID"""
        try:
            conn = self._get_connection()
            
            df = pd.read_sql_query(
                'SELECT * FROM episodes WHERE episode_id = ? ORDER BY part',
                conn,
                params=(episode_id,)
            )
            
            df = df.rename(columns={
                'episode_id': 'Id',
                'part': 'Part',
                'title': 'Titolo',
                'description': 'Description',
                'category': 'Category',
                'guest': 'Guest',
                'spotify_url': 'Spotify_URL',
                'shownotes_url': 'Shownotes'
            })
            
            conn.close()
            return df
            
        except Exception as e:
            logger.error(f"Error getting episodes by ID: {e}", exc_info=True)
            return pd.DataFrame()
    
    def get_episode_by_id_and_part(self, episode_id: int, part: int) -> Optional[dict]:
        """Restituisce episodio specifico per ID e parte"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM episodes WHERE episode_id = ? AND part = ?',
                (episode_id, part)
            )
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'Id': row['episode_id'],
                    'Part': row['part'],
                    'Titolo': row['title'],
                    'Description': row['description'],
                    'Category': row['category'],
                    'Guest': row['guest'],
                    'Spotify_URL': row['spotify_url'],
                    'Shownotes': row['shownotes_url']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting episode by ID and part: {e}", exc_info=True)
            return None
    
    def get_random_pill(self) -> Optional[dict]:
        """Restituisce una pillola casuale"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM pills ORDER BY RANDOM() LIMIT 1')
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'Id': row['episode_id'],
                    'Titolo': row['title'],
                    'Description': row['description'],
                    'Spotify_URL': row['spotify_url']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting random pill: {e}", exc_info=True)
            return None
    
    def is_new_episode(self, episode_data: dict) -> bool:
        """Verifica se un episodio è nuovo"""
        try:
            episode_id = episode_data.get('Id')
            part = episode_data.get('Part', 1)
            
            if episode_id is None:
                return False
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT COUNT(*) FROM episodes WHERE episode_id = ? AND part = ?',
                (episode_id, part)
            )
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count == 0
            
        except Exception as e:
            logger.error(f"Error checking if episode is new: {e}", exc_info=True)
            return False
    
    def is_new_pill(self, pill_data: dict) -> bool:
        """Verifica se una pillola è nuova"""
        try:
            title = pill_data.get('Titolo')
            if not title:
                return False
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM pills WHERE title = ?', (title,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count == 0
            
        except Exception as e:
            logger.error(f"Error checking if pill is new: {e}", exc_info=True)
            return False
    
    def add_episode(self, episode_data: dict):
        """Aggiunge un nuovo episodio al database"""
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO episodes 
                    (episode_id, part, title, description, category, guest, 
                     spotify_url, shownotes_url, gpt, subtitle)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    episode_data.get('Id'),
                    episode_data.get('Part', 1),
                    episode_data.get('Titolo'),
                    episode_data.get('Description'),
                    episode_data.get('Category'),
                    episode_data.get('Guest'),
                    episode_data.get('Spotify_URL'),
                    episode_data.get('Shownotes'),
                    episode_data.get('GPT', '*'),
                    episode_data.get('Sottotitolo', '*')
                ))
                
                conn.commit()
                conn.close()
                
                # Invalida cache
                self._cache_categories = None
                self._cache_guests = None
                
                logger.info(f"Added new episode: {episode_data.get('Titolo')}")
                
            except Exception as e:
                logger.error(f"Error adding episode: {e}", exc_info=True)
    
    def add_pill(self, pill_data: dict):
        """Aggiunge una nuova pillola al database"""
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO pills (episode_id, title, description, spotify_url)
                    VALUES (?, ?, ?, ?)
                ''', (
                    pill_data.get('Id'),
                    pill_data.get('Titolo'),
                    pill_data.get('Description'),
                    pill_data.get('Spotify_URL')
                ))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Added new pill: {pill_data.get('Titolo')}")
                
            except Exception as e:
                logger.error(f"Error adding pill: {e}", exc_info=True)
    
    def log_stat(self, chat_id: str, query: str):
        """Registra una statistica"""
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                cursor.execute('''
                    INSERT INTO stats (datetime, chat_id, query)
                    VALUES (?, ?, ?)
                ''', (now, chat_id, query))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"Error logging stat: {e}", exc_info=True)
    
    def add_user_to_notifications(self, chat_id: int):
        """Aggiungi utente alla lista notifiche"""
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO notification_users (chat_id, active)
                    VALUES (?, 1)
                ''', (str(chat_id),))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Added user {chat_id} to notifications")
                
            except Exception as e:
                logger.error(f"Error adding user to notifications: {e}", exc_info=True)
    
    def get_notification_users(self) -> List[str]:
        """Recupera lista utenti da notificare"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT chat_id FROM notification_users 
                WHERE active = 1
                ORDER BY added_at
            ''')
            
            users = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting notification users: {e}", exc_info=True)
            return []
    
    def remove_user_from_notifications(self, chat_id: int):
        """Rimuovi utente dalla lista (segna come inattivo)"""
        with self._lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE notification_users 
                    SET active = 0 
                    WHERE chat_id = ?
                ''', (str(chat_id),))
                
                conn.commit()
                conn.close()
                
                logger.info(f"Removed user {chat_id} from notifications")
                
            except Exception as e:
                logger.error(f"Error removing user from notifications: {e}", exc_info=True)
    
    def get_all_chat_ids(self) -> List[str]:
        """Restituisce tutti i chat ID dalle statistiche (per broadcast)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT chat_id FROM stats')
            chat_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return chat_ids
            
        except Exception as e:
            logger.error(f"Error getting all chat IDs: {e}", exc_info=True)
            return []
    
    # ==========================================
    # METODI PER COMPATIBILITÀ CON COMANDI ADMIN
    # ==========================================
    
    def get_total_episodes(self) -> int:
        """Restituisce numero totale episodi"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM episodes')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting total episodes: {e}", exc_info=True)
            return 0
    
    def get_total_pills(self) -> int:
        """Restituisce numero totale pillole"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM pills')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting total pills: {e}", exc_info=True)
            return 0
    
    def get_total_stats(self) -> int:
        """Restituisce numero totale statistiche"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM stats')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting total stats: {e}", exc_info=True)
            return 0
    
    def get_top_queries(self, limit: int = 5) -> List[tuple]:
        """Restituisce top N query più frequenti"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT query, COUNT(*) as count 
                FROM stats 
                GROUP BY query 
                ORDER BY count DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            return [(row[0], row[1]) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting top queries: {e}", exc_info=True)
            return []
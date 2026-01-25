"""
Modulo di configurazione per il bot
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv


class Config:
    """Gestisce tutte le configurazioni del bot"""
    
    def __init__(self):
        # Carica variabili d'ambiente
        load_dotenv(find_dotenv())
        
        # Token e credenziali
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
        self.SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "311429528"))
        
        # Validazione
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN non trovato nel file .env")
        if not self.SPOTIFY_CLIENT_ID or not self.SPOTIFY_CLIENT_SECRET:
            raise ValueError("Credenziali Spotify non trovate nel file .env")
        
        # URL Spotify
        self.SPOTIFY_SHOW_URL = 'https://api.spotify.com/v1/shows/2cqzDBQRxqgba39VPp3FDs/episodes'
        self.SPOTIFY_PILLS_URL = 'https://api.spotify.com/v1/shows/5ILsIKO18lp9aemJqcAWdb/episodes'
        
        # URL Web Scraping
        self.SHOWNOTES_URL = 'https://officeofcards.com/ospite/'
        
        # Percorsi file
        self.DATA_DIR = Path('./data')
        self.DATA_DIR.mkdir(exist_ok=True)
        
        self.DB_PATH = self.DATA_DIR / 'db.csv'
        self.STATS_PATH = self.DATA_DIR / 'stats.csv'
        self.PILLS_PATH = self.DATA_DIR / 'pills.csv'
        
        # Inizializza file se non esistono
        self._init_files()
    
    def _init_files(self):
        """Crea file CSV vuoti se non esistono"""
        import pandas as pd
        
        # Database episodi
        if not self.DB_PATH.exists():
            pd.DataFrame(columns=[
                'Id', 'Part', 'Titolo', 'Description', 'Category', 
                'Guest', 'Spotify_URL', 'Shownotes', 'GPT', 'Sottotitolo'
            ]).to_csv(self.DB_PATH, index=False)
        
        # Statistiche
        if not self.STATS_PATH.exists():
            pd.DataFrame(columns=[
                'Datetime', 'Chat ID', 'Query'
            ]).to_csv(self.STATS_PATH, index=False)
        
        # Pillole
        if not self.PILLS_PATH.exists():
            pd.DataFrame(columns=[
                'Id', 'Titolo', 'Description', 'Spotify_URL'
            ]).to_csv(self.PILLS_PATH, index=False)
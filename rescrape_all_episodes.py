#!/usr/bin/env python
# coding: utf-8

"""
Script per rifare lo scraping completo di tutti gli episodi
Scarica da Spotify e integra con shownotes dal sito
"""

import logging
import time
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import Config
from spotify_service import SpotifyService
from web_scraper import WebScraper

# Configurazione logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class EpisodeRescraper:
    """Gestisce il rescraping completo degli episodi"""
    
    def __init__(self):
        self.config = Config()
        self.spotify = SpotifyService(self.config)
        self.scraper = WebScraper()
        
        # Dataframe per raccogliere episodi
        self.episodes = []
        self.pills = []
        
    def fetch_all_from_spotify(self, show_url: str, is_pills: bool = False) -> list:
        """
        Scarica TUTTI gli episodi da uno show Spotify
        Gestisce automaticamente la paginazione
        """
        logger.info(f"📡 Scaricando episodi da Spotify...")
        
        all_items = []
        offset = 0
        limit = 50  # Max permesso da Spotify
        
        while True:
            try:
                # Chiamata API con offset
                results = self.spotify.client._get(
                    show_url,
                    limit=limit,
                    offset=offset,
                    market='IT'
                )
                
                items = results.get('items', [])
                
                if not items:
                    break  # Finiti gli episodi
                
                all_items.extend(items)
                logger.info(f"  ✓ Scaricati {len(all_items)} episodi finora...")
                
                # Se abbiamo meno di 'limit' items, siamo all'ultima pagina
                if len(items) < limit:
                    break
                
                offset += limit
                time.sleep(0.5)  # Rate limiting gentile
                
            except Exception as e:
                logger.error(f"Errore durante download: {e}")
                break
        
        logger.info(f"✅ Totale episodi scaricati: {len(all_items)}")
        return all_items
    
    def parse_episode_from_spotify(self, item: dict) -> dict:
        """Parse singolo episodio da risposta Spotify"""
        try:
            # Estrai titolo e pulisci
            title = item.get('name', '')
            if title.startswith('Office of Cards -'):
                title = title.replace('Office of Cards -', '').strip()
            
            # Parse ID e Part
            episode_id, part = self.spotify._parse_id_part(title)
            
            # Estrai categoria
            category = self.spotify._extract_category(title, episode_id)
            
            episode_data = {
                'Id': episode_id,
                'Part': part,
                'Titolo': title,
                'Description': item.get('description', ''),
                'Category': category,
                'Guest': '*',  # Da aggiornare con scraping
                'Spotify_URL': item.get('external_urls', {}).get('spotify', ''),
                'Shownotes': '*',  # Da aggiornare con scraping
                'GPT': '*',
                'Sottotitolo': '*',
                'Release_Date': item.get('release_date', '')
            }
            
            return episode_data
            
        except Exception as e:
            logger.error(f"Errore parsing episodio: {e}")
            return None
    
    def parse_pill_from_spotify(self, item: dict) -> dict:
        """Parse singola pillola da risposta Spotify"""
        try:
            description = item.get('description', '')
            episode_id = self.spotify._extract_id_from_description(description)
            
            pill_data = {
                'Id': episode_id,
                'Titolo': item.get('name', ''),
                'Description': description,
                'Spotify_URL': item.get('external_urls', {}).get('spotify', ''),
                'Release_Date': item.get('release_date', '')
            }
            
            return pill_data
            
        except Exception as e:
            logger.error(f"Errore parsing pillola: {e}")
            return None
    
    def enrich_with_shownotes(self, episodes: list) -> list:
        """
        Arricchisce episodi con dati da shownotes
        Fa scraping del sito per ogni episodio
        """
        logger.info("🌐 Arricchendo episodi con shownotes...")
        
        enriched = []
        total = len(episodes)
        
        for idx, episode in enumerate(episodes, 1):
            episode_id = episode.get('Id')
            
            if episode_id and episode_id > 0:
                logger.info(f"  [{idx}/{total}] Episodio {episode_id}: {episode.get('Titolo', '')[:50]}...")
                
                # Scraping shownotes e guest
                shownotes_url, guest_name = self.scraper.get_shownotes_and_guest(episode_id)
                
                episode['Shownotes'] = shownotes_url
                episode['Guest'] = guest_name
                
                # Rate limiting - pausa tra richieste
                time.sleep(1)
            else:
                logger.warning(f"  [{idx}/{total}] Episodio senza ID valido: {episode.get('Titolo', '')[:50]}")
            
            enriched.append(episode)
        
        logger.info("✅ Arricchimento completato!")
        return enriched
    
    def scrape_all_episodes(self) -> pd.DataFrame:
        """Scraping completo episodi principali"""
        logger.info("\n" + "="*60)
        logger.info("📊 SCRAPING EPISODI PRINCIPALI")
        logger.info("="*60 + "\n")
        
        # 1. Download da Spotify
        items = self.fetch_all_from_spotify(self.config.SPOTIFY_SHOW_URL)
        
        if not items:
            logger.error("❌ Nessun episodio scaricato da Spotify!")
            return pd.DataFrame()
        
        # 2. Parse episodi
        logger.info("🔄 Parsing episodi...")
        episodes = []
        for item in items:
            episode = self.parse_episode_from_spotify(item)
            if episode:
                episodes.append(episode)
        
        logger.info(f"✅ {len(episodes)} episodi parsati")
        
        # 3. Arricchimento con shownotes
        episodes = self.enrich_with_shownotes(episodes)
        
        # 4. Converti in DataFrame
        df = pd.DataFrame(episodes)
        
        # 5. Ordina per ID e Part
        if not df.empty:
            df = df.sort_values(['Id', 'Part'], ascending=[True, True])
            df = df.reset_index(drop=True)
        
        return df
    
    def scrape_all_pills(self) -> pd.DataFrame:
        """Scraping completo pillole"""
        logger.info("\n" + "="*60)
        logger.info("💊 SCRAPING PILLOLE")
        logger.info("="*60 + "\n")
        
        # 1. Download da Spotify
        items = self.fetch_all_from_spotify(self.config.SPOTIFY_PILLS_URL, is_pills=True)
        
        if not items:
            logger.error("❌ Nessuna pillola scaricata da Spotify!")
            return pd.DataFrame()
        
        # 2. Parse pillole
        logger.info("🔄 Parsing pillole...")
        pills = []
        for item in items:
            pill = self.parse_pill_from_spotify(item)
            if pill:
                pills.append(pill)
        
        logger.info(f"✅ {len(pills)} pillole parsate")
        
        # 3. Converti in DataFrame
        df = pd.DataFrame(pills)
        
        # 4. Ordina per data
        if not df.empty and 'Release_Date' in df.columns:
            df = df.sort_values('Release_Date', ascending=False)
            df = df.reset_index(drop=True)
        
        return df
    
    def save_to_csv(self, df_episodes: pd.DataFrame, df_pills: pd.DataFrame):
        """Salva DataFrame in CSV"""
        logger.info("\n" + "="*60)
        logger.info("💾 SALVATAGGIO DATI")
        logger.info("="*60 + "\n")
        
        # Backup vecchi file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.config.DB_PATH.exists():
            backup_db = self.config.DATA_DIR / f'db_backup_{timestamp}.csv'
            logger.info(f"📦 Backup vecchio db.csv → {backup_db.name}")
            import shutil
            shutil.copy(self.config.DB_PATH, backup_db)
        
        if self.config.PILLS_PATH.exists():
            backup_pills = self.config.DATA_DIR / f'pills_backup_{timestamp}.csv'
            logger.info(f"📦 Backup vecchio pills.csv → {backup_pills.name}")
            import shutil
            shutil.copy(self.config.PILLS_PATH, backup_pills)
        
        # Salva nuovi file
        logger.info(f"💾 Salvando {len(df_episodes)} episodi...")
        df_episodes.to_csv(self.config.DB_PATH, index=False, encoding='utf-8')
        logger.info(f"✅ Salvato: {self.config.DB_PATH}")
        
        logger.info(f"💾 Salvando {len(df_pills)} pillole...")
        df_pills.to_csv(self.config.PILLS_PATH, index=False, encoding='utf-8')
        logger.info(f"✅ Salvato: {self.config.PILLS_PATH}")
    
    def save_to_sqlite(self, df_episodes: pd.DataFrame, df_pills: pd.DataFrame):
        """Salva DataFrame in SQLite"""
        import sqlite3
        
        logger.info("\n" + "="*60)
        logger.info("💾 SALVATAGGIO IN SQLITE")
        logger.info("="*60 + "\n")
        
        db_path = self.config.DATA_DIR / 'bot.db'
        
        # Backup database esistente
        if db_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_db = self.config.DATA_DIR / f'bot_backup_{timestamp}.db'
            logger.info(f"📦 Backup vecchio database → {backup_db.name}")
            import shutil
            shutil.copy(db_path, backup_db)
        
        # Connessione
        conn = sqlite3.connect(db_path)
        
        # Svuota tabelle esistenti
        logger.info("🗑️  Svuotando tabelle esistenti...")
        conn.execute('DELETE FROM episodes')
        conn.execute('DELETE FROM pills')
        conn.commit()
        
        # Inserisci episodi
        logger.info(f"💾 Inserendo {len(df_episodes)} episodi...")
        for _, row in df_episodes.iterrows():
            conn.execute('''
                INSERT INTO episodes 
                (episode_id, part, title, description, category, guest, 
                 spotify_url, shownotes_url, gpt, subtitle)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(row['Id']),
                int(row['Part']),
                str(row['Titolo']),
                str(row['Description']),
                str(row['Category']),
                str(row['Guest']),
                str(row['Spotify_URL']),
                str(row['Shownotes']),
                str(row.get('GPT', '*')),
                str(row.get('Sottotitolo', '*'))
            ))
        
        # Inserisci pillole
        logger.info(f"💾 Inserendo {len(df_pills)} pillole...")
        for _, row in df_pills.iterrows():
            conn.execute('''
                INSERT INTO pills (episode_id, title, description, spotify_url)
                VALUES (?, ?, ?, ?)
            ''', (
                int(row['Id']) if pd.notna(row['Id']) else None,
                str(row['Titolo']),
                str(row['Description']),
                str(row['Spotify_URL'])
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Database salvato: {db_path}")
    
    def generate_report(self, df_episodes: pd.DataFrame, df_pills: pd.DataFrame):
        """Genera report finale"""
        logger.info("\n" + "="*60)
        logger.info("📊 REPORT FINALE")
        logger.info("="*60)
        
        # Statistiche episodi
        total_eps = len(df_episodes)
        with_shownotes = len(df_episodes[df_episodes['Shownotes'] != '*'])
        with_guest = len(df_episodes[df_episodes['Guest'] != '*'])
        
        categories = df_episodes['Category'].value_counts()
        
        logger.info(f"\n📺 EPISODI:")
        logger.info(f"  Totali: {total_eps}")
        logger.info(f"  Con shownotes: {with_shownotes} ({with_shownotes/total_eps*100:.1f}%)")
        logger.info(f"  Con guest: {with_guest} ({with_guest/total_eps*100:.1f}%)")
        logger.info(f"  Categorie:")
        for cat, count in categories.head(10).items():
            logger.info(f"    - {cat}: {count}")
        
        # Statistiche pillole
        logger.info(f"\n💊 PILLOLE:")
        logger.info(f"  Totali: {len(df_pills)}")
        
        # Problemi potenziali
        logger.info(f"\n⚠️  EPISODI DA VERIFICARE:")
        no_shownotes = df_episodes[df_episodes['Shownotes'] == '*']
        if len(no_shownotes) > 0:
            logger.info(f"  Senza shownotes: {len(no_shownotes)}")
            for _, ep in no_shownotes.head(5).iterrows():
                logger.info(f"    - ID {ep['Id']}: {ep['Titolo'][:60]}")
        else:
            logger.info(f"  ✅ Tutti gli episodi hanno shownotes!")
        
        logger.info("\n" + "="*60 + "\n")


def main():
    """Funzione principale"""
    print("\n" + "="*70)
    print("🔄 RESCRAPING COMPLETO DATABASE OFFICE OF CARDS")
    print("="*70)
    print()
    print("Questo script:")
    print("  1. Scarica TUTTI gli episodi da Spotify")
    print("  2. Fa scraping delle shownotes dal sito")
    print("  3. Crea backup dei dati esistenti")
    print("  4. Sovrascrive il database con dati puliti")
    print()
    print("⏱️  Tempo stimato: 5-15 minuti (dipende dal numero di episodi)")
    print()
    
    # Chiedi conferma
    response = input("Vuoi procedere? (s/n): ").strip().lower()
    
    if response not in ['s', 'si', 'sì', 'y', 'yes']:
        print("\n❌ Operazione annullata.")
        return
    
    # Chiedi formato output
    print("\nFormato database:")
    print("  1. CSV (compatibile con database.py)")
    print("  2. SQLite (compatibile con database_sqlite.py)")
    print("  3. Entrambi")
    
    format_choice = input("\nScegli (1/2/3): ").strip()
    
    # Inizio rescraping
    print("\n🚀 Inizio rescraping...\n")
    start_time = time.time()
    
    try:
        scraper = EpisodeRescraper()
        
        # Scraping episodi
        df_episodes = scraper.scrape_all_episodes()
        
        if df_episodes.empty:
            logger.error("❌ Nessun episodio scaricato! Operazione interrotta.")
            return
        
        # Scraping pillole
        df_pills = scraper.scrape_all_pills()
        
        # Salvataggio
        if format_choice in ['1', '3']:
            scraper.save_to_csv(df_episodes, df_pills)
        
        if format_choice in ['2', '3']:
            scraper.save_to_sqlite(df_episodes, df_pills)
        
        # Report finale
        scraper.generate_report(df_episodes, df_pills)
        
        # Tempo totale
        elapsed = time.time() - start_time
        logger.info(f"⏱️  Tempo totale: {elapsed/60:.1f} minuti")
        
        print("\n" + "="*70)
        print("✅ RESCRAPING COMPLETATO CON SUCCESSO!")
        print("="*70)
        print()
        print("📝 Prossimi passi:")
        print("  1. Verifica i dati generati")
        print("  2. Riavvia il bot: python bot.py")
        print("  3. Testa con /stats")
        print("  4. Se tutto OK, elimina i backup vecchi")
        print()
        
    except KeyboardInterrupt:
        print("\n\n❌ Operazione interrotta dall'utente.")
    except Exception as e:
        logger.error(f"\n❌ Errore durante il rescraping: {e}", exc_info=True)
        print("\n💡 Suggerimento: I backup sono stati creati, puoi ripristinarli se necessario.")


if __name__ == "__main__":
    main()
#!/usr/bin/env python
# coding: utf-8

"""
Script per migrare i dati da CSV a SQLite
Esegui UNA SOLA VOLTA per convertire i dati esistenti
"""

import pandas as pd
import sqlite3
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def migrate_csv_to_sqlite():
    """Migra tutti i dati da CSV a SQLite"""
    
    # Percorsi
    data_dir = Path('./data')
    db_path = data_dir / 'bot.db'
    
    csv_db = data_dir / 'db.csv'
    csv_stats = data_dir / 'stats.csv'
    csv_pills = data_dir / 'pills.csv'
    txt_users = data_dir / 'notification_users.txt'
    
    # Verifica che i CSV esistano
    if not csv_db.exists():
        logger.error(f"❌ File {csv_db} non trovato!")
        return False
    
    # Backup del database esistente se presente
    if db_path.exists():
        backup_path = data_dir / f'bot_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        logger.warning(f"⚠️  Database SQLite già esistente, creo backup: {backup_path}")
        import shutil
        shutil.copy(db_path, backup_path)
    
    try:
        # Connessione al database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔨 Creando struttura database...")
        
        # Crea tabelle
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
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_episode_id ON episodes(episode_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON episodes(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_guest ON episodes(guest)')
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                query TEXT NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_id ON stats(chat_id)')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_users (
                chat_id TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        logger.info("✅ Struttura database creata")
        
        # Migra episodi
        logger.info("📊 Migrando episodi...")
        df_episodes = pd.read_csv(csv_db, encoding='utf-8')
        
        migrated_episodes = 0
        skipped_episodes = 0
        
        for _, row in df_episodes.iterrows():
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO episodes 
                    (episode_id, part, title, description, category, guest, 
                     spotify_url, shownotes_url, gpt, subtitle)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    int(row['Id']) if pd.notna(row['Id']) else 0,
                    int(row['Part']) if pd.notna(row['Part']) else 1,
                    str(row['Titolo']) if pd.notna(row['Titolo']) else '',
                    str(row['Description']) if pd.notna(row['Description']) else '',
                    str(row['Category']) if pd.notna(row['Category']) else '',
                    str(row['Guest']) if pd.notna(row['Guest']) else '',
                    str(row['Spotify_URL']) if pd.notna(row['Spotify_URL']) else '',
                    str(row['Shownotes']) if pd.notna(row['Shownotes']) else '',
                    str(row.get('GPT', '*')),
                    str(row.get('Sottotitolo', '*'))
                ))
                
                if cursor.rowcount > 0:
                    migrated_episodes += 1
                else:
                    skipped_episodes += 1
                    
            except Exception as e:
                logger.warning(f"Errore migrando episodio {row.get('Titolo', '?')}: {e}")
                skipped_episodes += 1
        
        conn.commit()
        logger.info(f"✅ Episodi migrati: {migrated_episodes}, saltati: {skipped_episodes}")
        
        # Migra pillole
        if csv_pills.exists():
            logger.info("💊 Migrando pillole...")
            df_pills = pd.read_csv(csv_pills, encoding='utf-8')
            
            migrated_pills = 0
            skipped_pills = 0
            
            for _, row in df_pills.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO pills (episode_id, title, description, spotify_url)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        int(row['Id']) if pd.notna(row['Id']) else None,
                        str(row['Titolo']) if pd.notna(row['Titolo']) else '',
                        str(row['Description']) if pd.notna(row['Description']) else '',
                        str(row['Spotify_URL']) if pd.notna(row['Spotify_URL']) else ''
                    ))
                    
                    if cursor.rowcount > 0:
                        migrated_pills += 1
                    else:
                        skipped_pills += 1
                        
                except Exception as e:
                    logger.warning(f"Errore migrando pillola {row.get('Titolo', '?')}: {e}")
                    skipped_pills += 1
            
            conn.commit()
            logger.info(f"✅ Pillole migrate: {migrated_pills}, saltate: {skipped_pills}")
        else:
            logger.warning("⚠️  File pillole.csv non trovato, salto migrazione pillole")
        
        # Migra statistiche
        if csv_stats.exists():
            logger.info("📈 Migrando statistiche...")
            df_stats = pd.read_csv(csv_stats, encoding='utf-8')
            
            migrated_stats = 0
            
            for _, row in df_stats.iterrows():
                try:
                    cursor.execute('''
                        INSERT INTO stats (datetime, chat_id, query)
                        VALUES (?, ?, ?)
                    ''', (
                        str(row['Datetime']) if pd.notna(row['Datetime']) else '',
                        str(row['Chat ID']) if pd.notna(row['Chat ID']) else '',
                        str(row['Query']) if pd.notna(row['Query']) else ''
                    ))
                    migrated_stats += 1
                    
                except Exception as e:
                    logger.warning(f"Errore migrando statistica: {e}")
            
            conn.commit()
            logger.info(f"✅ Statistiche migrate: {migrated_stats}")
        else:
            logger.warning("⚠️  File stats.csv non trovato, salto migrazione statistiche")
        
        # Migra utenti notifiche
        if txt_users.exists():
            logger.info("👥 Migrando utenti notifiche...")
            
            with open(txt_users, 'r', encoding='utf-8') as f:
                users = [line.strip() for line in f if line.strip()]
            
            migrated_users = 0
            
            for chat_id in users:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO notification_users (chat_id, active)
                        VALUES (?, 1)
                    ''', (chat_id,))
                    
                    if cursor.rowcount > 0:
                        migrated_users += 1
                        
                except Exception as e:
                    logger.warning(f"Errore migrando utente {chat_id}: {e}")
            
            conn.commit()
            logger.info(f"✅ Utenti notifiche migrati: {migrated_users}")
        else:
            logger.warning("⚠️  File notification_users.txt non trovato, salto migrazione utenti")
        
        # Chiudi connessione
        conn.close()
        
        # Statistiche finali
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM episodes')
        total_episodes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM pills')
        total_pills = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM stats')
        total_stats = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM notification_users WHERE active = 1')
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info("\n" + "="*50)
        logger.info("🎉 MIGRAZIONE COMPLETATA!")
        logger.info("="*50)
        logger.info(f"📊 Episodi totali: {total_episodes}")
        logger.info(f"💊 Pillole totali: {total_pills}")
        logger.info(f"📈 Statistiche totali: {total_stats}")
        logger.info(f"👥 Utenti notifiche: {total_users}")
        logger.info(f"💾 Database salvato in: {db_path}")
        logger.info("="*50)
        
        # Istruzioni post-migrazione
        logger.info("\n📝 PROSSIMI PASSI:")
        logger.info("1. Rinomina database.py in database_csv_old.py")
        logger.info("2. Rinomina database_sqlite.py in database.py")
        logger.info("3. Riavvia il bot: python bot.py")
        logger.info("4. Testa con /stats e /testcheck")
        logger.info("5. Se tutto funziona, puoi eliminare i CSV (ma fai backup prima!)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore durante la migrazione: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔄 MIGRAZIONE DA CSV A SQLITE")
    print("="*60)
    print()
    print("Questo script convertirà i tuoi dati CSV in un database SQLite.")
    print("I file originali NON verranno modificati.")
    print()
    
    response = input("Vuoi procedere? (s/n): ")
    
    if response.lower() in ['s', 'si', 'sì', 'y', 'yes']:
        print("\n🚀 Inizio migrazione...\n")
        success = migrate_csv_to_sqlite()
        
        if success:
            print("\n✅ Migrazione completata con successo!")
        else:
            print("\n❌ Migrazione fallita. Controlla i log sopra.")
    else:
        print("\n❌ Migrazione annullata.")
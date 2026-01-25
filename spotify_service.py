"""
Servizio per interagire con Spotify API
"""

import logging
from typing import Optional, Dict, Tuple
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

logger = logging.getLogger(__name__)


class SpotifyService:
    """Gestisce le interazioni con Spotify"""
    
    def __init__(self, config):
        self.config = config
        self.client = self._create_client()
    
    def _create_client(self) -> spotipy.Spotify:
        """Crea il client Spotify"""
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=self.config.SPOTIFY_CLIENT_ID,
                client_secret=self.config.SPOTIFY_CLIENT_SECRET
            )
            return spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            logger.error(f"Error creating Spotify client: {e}", exc_info=True)
            raise
    
    def get_latest_episode(self) -> Optional[Dict]:
        """Recupera l'ultimo episodio del podcast principale"""
        try:
            results = self.client._get(
                self.config.SPOTIFY_SHOW_URL,
                limit=1,
                market='IT'
            )
            
            if not results or 'items' not in results or not results['items']:
                return None
            
            episode = results['items'][0]
            return self._parse_episode(episode)
            
        except Exception as e:
            logger.error(f"Error getting latest episode: {e}", exc_info=True)
            return None
    
    def get_latest_pill(self) -> Optional[Dict]:
        """Recupera l'ultima pillola"""
        try:
            results = self.client._get(
                self.config.SPOTIFY_PILLS_URL,
                limit=1,
                market='IT'
            )
            
            if not results or 'items' not in results or not results['items']:
                return None
            
            pill = results['items'][0]
            return self._parse_pill(pill)
            
        except Exception as e:
            logger.error(f"Error getting latest pill: {e}", exc_info=True)
            return None
    
    def _parse_episode(self, episode: Dict) -> Dict:
        """Parsea un episodio Spotify in formato database"""
        try:
            # Estrai titolo
            title = episode.get('name', '')
            
            # Pulisci titolo da prefissi "Office of Cards -"
            if title.startswith('Office of Cards -'):
                title = title.replace('Office of Cards -', '').strip()
            
            # Estrai ID e Part dal titolo
            episode_id, part = self._parse_id_part(title)
            
            # Estrai categoria
            category = self._extract_category(title, episode_id)
            
            return {
                'Id': episode_id,
                'Part': part,
                'Titolo': title,
                'Description': episode.get('description', ''),
                'Category': category,
                'Spotify_URL': episode.get('external_urls', {}).get('spotify', ''),
                'Guest': '*',  # Da aggiornare con scraping
                'Shownotes': '*',  # Da aggiornare con scraping
                'GPT': '*',
                'Sottotitolo': '*'
            }
            
        except Exception as e:
            logger.error(f"Error parsing episode: {e}", exc_info=True)
            return {}
    
    def _parse_pill(self, pill: Dict) -> Dict:
        """Parsea una pillola Spotify"""
        try:
            description = pill.get('description', '')
            
            # Estrai ID dalla description
            episode_id = self._extract_id_from_description(description)
            
            return {
                'Id': episode_id,
                'Titolo': pill.get('name', ''),
                'Description': description,
                'Spotify_URL': pill.get('external_urls', {}).get('spotify', '')
            }
            
        except Exception as e:
            logger.error(f"Error parsing pill: {e}", exc_info=True)
            return {}
    
    def _parse_id_part(self, title: str) -> Tuple[int, int]:
        """
        Estrae ID e Part da un titolo
        Formato: "123_2 Titolo" oppure "123 Titolo"
        """
        try:
            parts = title.split(' ')
            if not parts:
                return 0, 1
            
            id_part = parts[0].split('_')
            
            # Estrai ID
            try:
                episode_id = int(id_part[0])
            except (ValueError, IndexError):
                return 0, 1
            
            # Estrai Part (default 1 se non presente)
            if len(id_part) > 1:
                try:
                    part = int(id_part[1])
                except ValueError:
                    part = 1
            else:
                part = 1
            
            return episode_id, part
            
        except Exception as e:
            logger.error(f"Error parsing ID/Part from '{title}': {e}")
            return 0, 1
    
    def _extract_category(self, title: str, episode_id: int) -> str:
        """Estrae la categoria da un titolo"""
        try:
            # Casi speciali
            if episode_id == 0:
                return 'INTRO'
            elif episode_id in [3, 31]:
                return 'Q&A'
            
            # Cerca categoria tra parentesi quadre [CATEGORIA]
            start = title.find('[')
            end = title.find(']')
            
            if start != -1 and end != -1:
                return title[start+1:end].strip()
            
            # Default: INTERVISTA
            return 'INTERVISTA'
            
        except Exception as e:
            logger.error(f"Error extracting category: {e}")
            return 'INTERVISTA'
    
    def _extract_id_from_description(self, description: str) -> int:
        """Estrae l'ID episodio dalla descrizione di una pillola"""
        try:
            words = description.split()
            for word in words:
                try:
                    return int(word)
                except ValueError:
                    continue
            return 0
        except Exception as e:
            logger.error(f"Error extracting ID from description: {e}")
            return 0
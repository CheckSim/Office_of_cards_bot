"""
Modulo per lo scraping delle shownotes dal sito
"""

import logging
from typing import Optional, Tuple
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebScraper:
    """Gestisce lo scraping del sito Office of Cards"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = 'https://officeofcards.com/ospite/'
    
    def get_shownotes_and_guest(self, episode_id: int) -> Tuple[str, str]:
        """
        Recupera URL shownotes e nome ospite per un episodio
        
        Returns:
            Tupla (shownotes_url, guest_name) oppure ('*', '*') se non trovati
        """
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            containers = soup.find_all('div', attrs={'class': 'container-overlay'})
            
            if not containers:
                logger.warning("No containers found on shownotes page")
                return '*', '*'
            
            # Verifica se l'episodio è già pubblicato
            latest_id = self._extract_episode_id(containers[0])
            if latest_id is None or episode_id > latest_id:
                logger.info(f"Episode {episode_id} not yet published on website")
                return '*', '*'
            
            # Cerca l'episodio specifico
            for container in containers:
                container_id = self._extract_episode_id(container)
                
                if container_id == episode_id:
                    # Estrai URL
                    link = container.find('a')
                    url = link.get('href', '*') if link else '*'
                    
                    # Estrai nome ospite
                    spans = container.find_all('span')
                    guest = spans[1].text.strip() if len(spans) > 1 else '*'
                    
                    logger.info(f"Found shownotes for episode {episode_id}: {guest}")
                    return url, guest
            
            logger.warning(f"Episode {episode_id} not found in containers")
            return '*', '*'
            
        except requests.RequestException as e:
            logger.error(f"Network error scraping shownotes: {e}")
            return '*', '*'
        except Exception as e:
            logger.error(f"Error scraping shownotes for episode {episode_id}: {e}", exc_info=True)
            return '*', '*'
    
    def _extract_episode_id(self, container) -> Optional[int]:
        """Estrae l'ID episodio da un container"""
        try:
            spans = container.find_all('span')
            if not spans:
                return None
            
            # Il primo span contiene qualcosa come "Episodio 123"
            text = spans[0].text.strip()
            words = text.split()
            
            # L'ultimo elemento dovrebbe essere il numero
            if words:
                return int(words[-1])
            
            return None
            
        except (ValueError, IndexError, AttributeError) as e:
            logger.debug(f"Could not extract episode ID from container: {e}")
            return None
    
    def update_episode_metadata(self, episode_data: dict) -> dict:
        """
        Aggiorna i metadati di un episodio con shownotes e guest
        
        Args:
            episode_data: Dizionario con dati episodio (deve contenere 'Id')
        
        Returns:
            episode_data aggiornato
        """
        try:
            episode_id = episode_data.get('Id')
            if episode_id is None:
                return episode_data
            
            shownotes_url, guest_name = self.get_shownotes_and_guest(episode_id)
            
            episode_data['Shownotes'] = shownotes_url
            episode_data['Guest'] = guest_name
            
            return episode_data
            
        except Exception as e:
            logger.error(f"Error updating episode metadata: {e}", exc_info=True)
            return episode_data
import cloudscraper
import time
from bs4 import BeautifulSoup
from ..config.scraping_config import ScrapingConfig

class HttpClient:
    def __init__(self, config: ScrapingConfig):
        self.config = config
        # Usar cloudscraper em vez de requests.Session()
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'linux',
                'desktop': True
            }
        )
        self._establish_session()
    
    def _establish_session(self):
        """Estabelece uma sessão visitando a página principal primeiro"""
        try:
            response = self.scraper.get('https://www.mg.senac.br/', timeout=30)
            if response.status_code == 200:
                time.sleep(2)
        except Exception:
            pass
    
    def get_page(self, url: str) -> BeautifulSoup:
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(2.0 * attempt)
                
                headers = {
                    'Referer': 'https://www.mg.senac.br/',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Dest': 'document'
                }
                
                response = self.scraper.get(url, timeout=self.config.timeout, 
                                          allow_redirects=True, headers=headers)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
                
            except Exception as e:
                if attempt == self.config.max_retries:
                    raise e
                time.sleep(3.0 * (attempt + 1))
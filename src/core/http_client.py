import requests
import time
from bs4 import BeautifulSoup
from ..config.scraping_config import ScrapingConfig

class HttpClient:
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_page(self, url: str) -> BeautifulSoup:
        for attempt in range(self.config.max_retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=self.config.timeout)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                if attempt == self.config.max_retries:
                    raise e
                time.sleep(self.config.retry_delay * (attempt + 1))
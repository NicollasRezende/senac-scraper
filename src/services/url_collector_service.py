import requests
import time
from bs4 import BeautifulSoup
from typing import List
from ..config.scraping_config import UrlCollectorConfig
from ..utils.file_handler import FileHandler

class UrlCollectorService:
    def __init__(self, config: UrlCollectorConfig = None):
        self.config = config or UrlCollectorConfig()
        self.base_url = "https://www.df.senac.br/noticias/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.collected_urls = set()
    
    def _get_page(self, url: str) -> BeautifulSoup:
        response = requests.get(url, headers=self.headers, timeout=self.config.timeout)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    
    def _extract_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        urls = []
        title_links = soup.select('.elementor-post__title a')
        
        for link in title_links:
            href = link.get('href')
            if href:
                urls.append(href.strip())
        
        return urls
    
    def collect_urls(self, start_page: int = None, end_page: int = None) -> List[str]:
        start_page = start_page or self.config.start_page
        end_page = end_page or self.config.end_page
        
        print(f"Iniciando coleta de URLs das páginas {start_page} a {end_page}")
        
        for page_num in range(start_page, end_page + 1):
            try:
                if page_num == 1:
                    page_url = self.base_url
                else:
                    page_url = f"{self.base_url}{page_num}/"
                
                print(f"[{page_num}/{end_page}] Processando: {page_url}")
                
                soup = self._get_page(page_url)
                page_urls = self._extract_urls_from_page(soup)
                
                new_urls = 0
                for url in page_urls:
                    if url not in self.collected_urls:
                        self.collected_urls.add(url)
                        new_urls += 1
                
                print(f"  Encontradas: {len(page_urls)} URLs ({new_urls} novas)")
                
                if page_num < end_page:
                    time.sleep(self.config.delay)
                
            except requests.RequestException as e:
                print(f"Erro na página {page_num}: {e}")
                continue
            except Exception as e:
                print(f"Erro inesperado na página {page_num}: {e}")
                continue
        
        final_urls = sorted(list(self.collected_urls))
        
        print(f"\nColeta finalizada!")
        print(f"Total de URLs únicas coletadas: {len(final_urls)}")
        
        return final_urls
    
    def collect_and_save(self, filename: str = 'senac_urls.txt', start_page: int = None, end_page: int = None) -> List[str]:
        urls = self.collect_urls(start_page, end_page)
        FileHandler.save_urls_to_file(urls, filename)
        print(f"URLs salvas em: {filename}")
        return urls
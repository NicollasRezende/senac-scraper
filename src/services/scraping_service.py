import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Optional
from ..config.scraping_config import ScrapingConfig
from ..core.http_client import HttpClient
from ..core.content_extractor import ContentExtractor
from ..models.news_article import NewsArticle
from ..utils.rate_limiter import RateLimiter
from ..utils.file_handler import FileHandler
from ..utils.statistics import Statistics

class ScrapingAgent:
    def __init__(self, config: ScrapingConfig, rate_limiter: RateLimiter):
        self.config = config
        self.rate_limiter = rate_limiter
        self.http_client = HttpClient(config)
        self.content_extractor = ContentExtractor()
    
    def scrape_url(self, url: str) -> NewsArticle:
        try:
            self.rate_limiter.wait()
            soup = self.http_client.get_page(url)
            content, content_images = self.content_extractor.extract_content(soup, url)
            
            return NewsArticle(
                url=url,
                title=self.content_extractor.extract_title(soup),
                author=self.content_extractor.extract_author(soup),
                date=self.content_extractor.extract_date(soup),
                featured_image=self.content_extractor.extract_featured_image(soup, url),
                content=content,
                content_images=content_images,
                success=True
            )
            
        except Exception as e:
            return NewsArticle(
                url=url,
                success=False,
                error=str(e)
            )

class ScrapingService:
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.rate_limiter = RateLimiter(self.config.delay_between_requests)
        self.results = []
        self.lock = threading.Lock()
    
    def _progress_callback_wrapper(self, callback: Optional[Callable], current: int, total: int, result: NewsArticle):
        if callback:
            with self.lock:
                callback(current, total, result.to_dict())
    
    def _worker_task(self, url: str, callback: Optional[Callable], total: int) -> NewsArticle:
        agent = ScrapingAgent(self.config, self.rate_limiter)
        result = agent.scrape_url(url)
        
        with self.lock:
            self.results.append(result.to_dict())
            current = len(self.results)
            
        if callback:
            self._progress_callback_wrapper(callback, current, total, result)
        
        return result
    
    def scrape_multiple(self, urls: List[str], callback: Optional[Callable] = None) -> List[Dict]:
        self.results.clear()
        total_urls = len(urls)
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_url = {
                executor.submit(self._worker_task, url, callback, total_urls): url 
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                try:
                    future.result()
                except Exception as e:
                    url = future_to_url[future]
                    print(f"Erro processando {url}: {e}")
        
        return self.results.copy()
    
    def scrape_from_file(self, file_path: str, callback: Optional[Callable] = None) -> List[Dict]:
        urls = FileHandler.load_urls_from_file(file_path)
        return self.scrape_multiple(urls, callback)
    
    def scrape_batch(self, file_path: str, batch_size: int = 50, save_interval: int = 10) -> List[Dict]:
        urls = FileHandler.load_urls_from_file(file_path)
        all_results = []
        
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(urls) + batch_size - 1) // batch_size
            
            print(f"Processando lote {batch_num}/{total_batches} ({len(batch_urls)} URLs)")
            
            def batch_callback(current, total, result):
                status = "OK" if result.get('success') else "ERROR"
                title = result.get('title', result.get('url', 'N/A'))[:50]
                print(f"  [{current}/{total}] {status}: {title}")
            
            batch_results = self.scrape_multiple(batch_urls, batch_callback)
            all_results.extend(batch_results)
            
            if batch_num % save_interval == 0:
                FileHandler.save_json(all_results, f"backup_batch_{batch_num}.json")
                print(f"Backup salvo: backup_batch_{batch_num}.json")
        
        return all_results
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        return Statistics.calculate_stats(results)
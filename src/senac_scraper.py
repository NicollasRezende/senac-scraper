import time
from .config.scraping_config import ScrapingConfig, UrlCollectorConfig
from .services.scraping_service import ScrapingService
from .services.url_collector_service import UrlCollectorService
from .utils.file_handler import FileHandler

class SenacScraper:
    def __init__(self, scraping_config: ScrapingConfig = None, url_config: UrlCollectorConfig = None):
        self.scraping_service = ScrapingService(scraping_config)
        self.url_collector = UrlCollectorService(url_config)
    
    def collect_urls(self, start_page: int = 1, end_page: int = 50, filename: str = 'senac_urls.txt'):
        return self.url_collector.collect_and_save(filename, start_page, end_page)
    
    def scrape_urls(self, urls_file: str = 'senac_urls.txt', output_file: str = 'noticias_final.json'):
        print("Iniciando scraping multithread...")
        start_time = time.time()
        
        results = self.scraping_service.scrape_from_file(urls_file)
        
        FileHandler.save_json(results, output_file)
        
        elapsed_time = time.time() - start_time
        stats = self.scraping_service.get_statistics(results)
        
        self._print_statistics(elapsed_time, stats)
        
        return results
    
    def scrape_batch(self, urls_file: str = 'senac_urls.txt', batch_size: int = 30, 
                     save_interval: int = 5, output_file: str = 'noticias_final.json'):
        print("Iniciando scraping em lotes...")
        start_time = time.time()
        
        results = self.scraping_service.scrape_batch(urls_file, batch_size, save_interval)
        
        FileHandler.save_json(results, output_file)
        
        elapsed_time = time.time() - start_time
        stats = self.scraping_service.get_statistics(results)
        
        self._print_statistics(elapsed_time, stats)
        
        return results
    
    def full_pipeline(self, start_page: int = 1, end_page: int = 50, 
                      batch_size: int = 30, save_interval: int = 5):
        print("Executando pipeline completo...")
        
        urls = self.collect_urls(start_page, end_page)
        print(f"URLs coletadas: {len(urls)}")
        
        results = self.scrape_batch(batch_size=batch_size, save_interval=save_interval)
        
        return results
    
    def _print_statistics(self, elapsed_time: float, stats: dict):
        print(f"\nCompleto em {elapsed_time:.1f}s")
        print(f"Taxa de sucesso: {stats['success_rate']}%")
        print(f"Artigos processados: {stats['successful']}/{stats['total']}")
        print(f"Imagens capturadas: {stats['total_content_images']}")
        print(f"Artigos com imagens: {stats['articles_with_images']}")
        print(f"Velocidade: {stats['total']/elapsed_time:.1f} URLs/s")
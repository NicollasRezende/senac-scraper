from src.config.scraping_config import ScrapingConfig, UrlCollectorConfig
from src.senac_scraper import SenacScraper

def main():
    scraping_config = ScrapingConfig(
        max_workers=6,
        delay_between_requests=0.3,
        max_retries=3,
        timeout=20
    )
    
    # Não precisa mais do url_config já que não vamos coletar URLs
    scraper = SenacScraper(scraping_config)
    
    # Use scrape_batch ao invés de full_pipeline
    # Isso vai ler do arquivo senac_urls.txt existente
    scraper.scrape_batch(
        urls_file='senac_urls.txt',  # nome do seu arquivo de URLs
        batch_size=30,
        save_interval=5,
        output_file='noticias_final.json'
    )

if __name__ == "__main__":
    main()
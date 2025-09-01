from src.config.scraping_config import ScrapingConfig, UrlCollectorConfig
from src.senac_scraper import SenacScraper

def main():
    scraping_config = ScrapingConfig(
        max_workers=6,
        delay_between_requests=0.3,
        max_retries=3,
        timeout=20
    )
    
    url_config = UrlCollectorConfig(
        delay=1.0,
        start_page=1,
        end_page=50
    )
    
    scraper = SenacScraper(scraping_config, url_config)
    
    scraper.full_pipeline(
        start_page=1,
        end_page=50,
        batch_size=30,
        save_interval=5
    )

if __name__ == "__main__":
    main()
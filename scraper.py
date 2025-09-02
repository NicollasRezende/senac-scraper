#!/usr/bin/env python3
"""
Senac Web Scraper

Web scraping system for extracting news content from Senac DF website.
Processes URLs from a text file and extracts structured content data.

Author: Content Scraping System
Version: 1.0.0
"""

import logging
import sys
from pathlib import Path

from src.config.scraping_config import ScrapingConfig
from src.senac_scraper import SenacScraper


def configure_logging() -> None:
    """Configure logging for the scraper."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main scraper execution function."""
    configure_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Senac Web Scraper initiated")
    
    # Scraping configuration
    scraping_config = ScrapingConfig(
        max_workers=6,
        delay_between_requests=0.3,
        max_retries=3,
        timeout=20
    )
    
    # Initialize scraper
    scraper = SenacScraper(scraping_config)
    
    # Configuration
    urls_file = 'senac_urls.txt'
    output_file = 'noticias_final.json'
    batch_size = 30
    save_interval = 5
    
    # Validate input file exists
    if not Path(urls_file).exists():
        logger.error(f"URLs file not found: {urls_file}")
        sys.exit(1)
    
    logger.info(f"Starting batch scraping from: {urls_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Save interval: {save_interval}")
    
    try:
        # Execute batch scraping
        scraper.scrape_batch(
            urls_file=urls_file,
            batch_size=batch_size,
            save_interval=save_interval,
            output_file=output_file
        )
        
        logger.info("Scraping process completed successfully")
        
    except Exception as e:
        logger.error(f"Scraping process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
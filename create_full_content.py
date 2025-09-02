#!/usr/bin/env python3
import asyncio
import logging
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.config.liferay_config import LiferayConfig
from src.services.integrated_processor import IntegratedProcessor
import json


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('full_content_creation.log')
        ]
    )


def get_config_from_env() -> LiferayConfig:
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['LIFERAY_BASE_URL', 'LIFERAY_SITE_ID', 'LIFERAY_USERNAME', 'LIFERAY_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing environment variables in .env file: {', '.join(missing_vars)}")
    
    return LiferayConfig(
        base_url=os.getenv('LIFERAY_BASE_URL'),
        site_id=os.getenv('LIFERAY_SITE_ID'),
        username=os.getenv('LIFERAY_USERNAME'),
        password=os.getenv('LIFERAY_PASSWORD'),
        timeout=int(os.getenv('LIFERAY_TIMEOUT', '30')),
        parent_folder_id=int(os.getenv('LIFERAY_PARENT_FOLDER_ID')) if os.getenv('LIFERAY_PARENT_FOLDER_ID') else None
    )


def load_news_from_json(file_path: str) -> list:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        raise ValueError(f"Error loading news from {file_path}: {e}")


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Liferay Complete Content Creation Service")
    logger.info("This will create folders + upload images")
    
    try:
        config = get_config_from_env()
        logger.info("Configuration loaded from .env file")
    except ValueError as e:
        logger.error(str(e))
        logger.error("Please create and configure a .env file based on .env.example")
        return
    
    news_file = "noticias_final.json"
    if not os.path.exists(news_file):
        logger.error(f"News file not found: {news_file}")
        return
    
    try:
        news_list = load_news_from_json(news_file)
        if not news_list:
            logger.error("No news found in file")
            return
    except ValueError as e:
        logger.error(str(e))
        return
    
    # Processing configuration
    batch_size = int(os.getenv('BATCH_SIZE', '3'))  # Smaller batch for complete processing
    delay = float(os.getenv('BATCH_DELAY', '2.0'))  # Longer delay for heavy operations
    
    logger.info(f"Processing configuration:")
    logger.info(f"  - News file: {news_file}")
    logger.info(f"  - Total news: {len(news_list)}")
    logger.info(f"  - Batch size: {batch_size}")
    logger.info(f"  - Batch delay: {delay}s")
    logger.info(f"  - Site ID: {config.site_id}")
    if config.parent_folder_id:
        logger.info(f"  - Parent folder ID: {config.parent_folder_id}")
    
    processor = IntegratedProcessor(config, batch_size=batch_size, delay=delay)
    
    try:
        results = await processor.process_all_news(news_list)
        
        # Summary of results
        successful = sum(1 for r in results if r.success)
        total_folders = sum(1 for r in results if r.folder_info)
        total_images = sum(len(r.uploaded_images) for r in results)
        
        logger.info("="*50)
        logger.info("FINAL SUMMARY")
        logger.info("="*50)
        logger.info(f"Successfully processed: {successful}/{len(results)}")
        logger.info(f"Folders created: {total_folders}")
        logger.info(f"Images uploaded: {total_images}")
        
        # Log failures if any
        failures = [r for r in results if not r.success and r.error]
        if failures:
            logger.info(f"Failed items: {len(failures)}")
            for failure in failures[:5]:  # Show first 5 failures
                logger.warning(f"  - {failure.error}")
        
        logger.info("="*50)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
import asyncio
import logging
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.config.liferay_config import LiferayConfig
from src.services.bulk_processor import BulkFolderProcessor


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('folder_creation.log')
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


def get_config_interactive() -> LiferayConfig:
    print("Configure Liferay Connection:")
    print("-" * 30)
    
    base_url = input("Base URL (ex: https://liferay.example.com): ").strip()
    site_id = input("Site ID: ").strip()
    username = input("Username: ").strip()
    
    parent_folder_input = input("Parent Folder ID (leave empty for root): ").strip()
    parent_folder_id = int(parent_folder_input) if parent_folder_input else None
    
    import getpass
    password = getpass.getpass("Password: ")
    
    return LiferayConfig(
        base_url=base_url,
        site_id=site_id,
        username=username,
        password=password,
        parent_folder_id=parent_folder_id
    )


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Liferay Folder Creation Service")
    
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
    
    batch_size = int(os.getenv('BATCH_SIZE', '5'))
    delay = float(os.getenv('BATCH_DELAY', '1.0'))
    
    logger.info(f"Processing configuration:")
    logger.info(f"  - News file: {news_file}")
    logger.info(f"  - Batch size: {batch_size}")
    logger.info(f"  - Batch delay: {delay}s")
    logger.info(f"  - Site ID: {config.site_id}")
    
    processor = BulkFolderProcessor(config, batch_size=batch_size, delay=delay)
    
    try:
        news_list = processor.load_news_from_json(news_file)
        if not news_list:
            logger.error("No news found in file")
            return
        
        logger.info(f"Loaded {len(news_list)} news items")
        
        folders = await processor.process_news_folders(news_list)
        
        logger.info(f"Successfully created/found {len(folders)} folders")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
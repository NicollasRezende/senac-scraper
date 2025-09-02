import asyncio
import logging
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from src.services.folder_service import FolderService, FolderInfo
from src.services.liferay_client import LiferayClient
from src.config.liferay_config import LiferayConfig


logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    total_news: int = 0
    folders_created: int = 0
    folders_failed: int = 0
    folders_existing: int = 0
    start_time: float = 0
    end_time: float = 0
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        if self.total_news == 0:
            return 0.0
        return (self.folders_created + self.folders_existing) / self.total_news * 100


class BulkFolderProcessor:
    def __init__(self, config: LiferayConfig, batch_size: int = 5, delay: float = 1.0):
        self.config = config
        self.batch_size = batch_size
        self.delay = delay
        self.folder_service = FolderService(config)
        self.stats = ProcessingStats()
    
    def load_news_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading news from {file_path}: {e}")
            return []
    
    def filter_valid_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            news for news in news_list 
            if news.get('success', False) and news.get('title', '').strip()
        ]
    
    async def process_news_folders(self, news_list: List[Dict[str, Any]]) -> List[FolderInfo]:
        self.stats.start_time = asyncio.get_event_loop().time()
        self.stats.total_news = len(news_list)
        
        valid_news = self.filter_valid_news(news_list)
        logger.info(f"Processing {len(valid_news)} valid news from {self.stats.total_news} total")
        
        results = []
        
        async with LiferayClient(self.config) as client:
            for i in range(0, len(valid_news), self.batch_size):
                batch = valid_news[i:i + self.batch_size]
                batch_results = await self._process_batch(client, batch, i // self.batch_size + 1)
                results.extend(batch_results)
                
                if i + self.batch_size < len(valid_news):
                    logger.info(f"Waiting {self.delay}s before next batch...")
                    await asyncio.sleep(self.delay)
        
        self.stats.end_time = asyncio.get_event_loop().time()
        self._log_final_stats()
        return [r for r in results if r is not None]
    
    async def _process_batch(self, client: LiferayClient, batch: List[Dict[str, Any]], 
                           batch_num: int) -> List[FolderInfo]:
        logger.info(f"Processing batch {batch_num} with {len(batch)} items")
        results = []
        
        for news in batch:
            try:
                folder_name = self.folder_service.sanitize_folder_name(news['title'])
                
                if folder_name in self.folder_service.created_folders:
                    results.append(self.folder_service.created_folders[folder_name])
                    self.stats.folders_existing += 1
                    continue
                
                existing_folder = await self.folder_service.folder_exists(client, folder_name)
                if existing_folder:
                    self.folder_service.created_folders[folder_name] = existing_folder
                    results.append(existing_folder)
                    self.stats.folders_existing += 1
                    continue
                
                folder_info = await self.folder_service.create_folder_for_news(client, news['title'])
                
                if folder_info:
                    results.append(folder_info)
                    self.stats.folders_created += 1
                    logger.info(f"✓ Created: {folder_info.name}")
                else:
                    results.append(None)
                    self.stats.folders_failed += 1
                    logger.warning(f"✗ Failed: {news['title'][:50]}...")
                
            except Exception as e:
                logger.error(f"Error processing news '{news.get('title', 'Unknown')}': {e}")
                results.append(None)
                self.stats.folders_failed += 1
        
        return results
    
    def _log_final_stats(self):
        logger.info("="*50)
        logger.info("PROCESSING COMPLETED")
        logger.info("="*50)
        logger.info(f"Total news processed: {self.stats.total_news}")
        logger.info(f"Folders created: {self.stats.folders_created}")
        logger.info(f"Folders already existing: {self.stats.folders_existing}")
        logger.info(f"Folders failed: {self.stats.folders_failed}")
        logger.info(f"Success rate: {self.stats.success_rate:.1f}%")
        logger.info(f"Processing time: {self.stats.duration:.2f}s")
        logger.info("="*50)
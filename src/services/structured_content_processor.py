import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.services.structured_content_folder_service import StructuredContentFolderService, StructuredContentFolderInfo
from src.services.structured_content_service import StructuredContentService
from src.services.liferay_client import LiferayClient
from src.config.liferay_config import LiferayConfig


logger = logging.getLogger(__name__)


@dataclass
class StructuredContentProcessingResult:
    folder_info: Optional[StructuredContentFolderInfo] = None
    content_info: Optional[Dict[str, Any]] = None
    success: bool = False
    error: str = ""


@dataclass
class StructuredContentStats:
    total_news: int = 0
    folders_created: int = 0
    contents_created: int = 0
    images_uploaded: int = 0
    failed_items: int = 0
    start_time: float = 0
    end_time: float = 0
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        if self.total_news == 0:
            return 0.0
        return (self.total_news - self.failed_items) / self.total_news * 100


class StructuredContentProcessor:
    def __init__(self, config: LiferayConfig, batch_size: int = 3, delay: float = 2.0):
        self.config = config
        self.batch_size = batch_size
        self.delay = delay
        self.folder_service = StructuredContentFolderService(config)
        self.content_service = StructuredContentService(config)
        self.stats = StructuredContentStats()
    
    async def process_single_news(self, client: LiferayClient,
                                news_data: Dict[str, Any]) -> StructuredContentProcessingResult:
        """
        Processa uma única notícia: cria pasta + conteúdo estruturado
        """
        result = StructuredContentProcessingResult()
        
        try:
            # Step 1: Criar pasta para a notícia
            folder_info = await self.folder_service.create_folder_for_news(
                client, news_data['title']
            )
            
            if not folder_info:
                result.error = "Failed to create structured content folder"
                return result
            
            result.folder_info = folder_info
            self.stats.folders_created += 1
            
            # Step 2: Criar conteúdo estruturado na pasta
            content_info = await self.content_service.create_news_content(
                client, folder_info.id, news_data
            )
            
            if not content_info:
                result.error = "Failed to create structured content"
                return result
            
            result.content_info = content_info
            self.stats.contents_created += 1
            
            # Contar imagens (featured + gallery)
            image_count = 0
            if news_data.get('featured_image'):
                image_count += 1
            if news_data.get('content_images'):
                image_count += len(news_data['content_images'])
            
            self.stats.images_uploaded += image_count
            
            result.success = True
            return result
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"Error processing news '{news_data.get('title', 'Unknown')}': {e}")
            return result
    
    async def process_news_batch(self, client: LiferayClient,
                               news_batch: List[Dict[str, Any]]) -> List[StructuredContentProcessingResult]:
        """
        Processa um lote de notícias em paralelo
        """
        tasks = []
        for news in news_batch:
            if news.get('success', False) and news.get('title'):
                task = self.process_single_news(client, news)
                tasks.append(task)
            else:
                # Cria resultado falhado para notícia inválida
                async def create_failed_result():
                    result = StructuredContentProcessingResult()
                    result.error = "Invalid news data"
                    return result
                tasks.append(create_failed_result())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converte exceções em resultados falhados
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                failed_result = StructuredContentProcessingResult()
                failed_result.error = str(result)
                processed_results.append(failed_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def process_all_news(self, news_list: List[Dict[str, Any]]) -> List[StructuredContentProcessingResult]:
        """
        Processa todas as notícias em lotes
        """
        self.stats.start_time = asyncio.get_event_loop().time()
        self.stats.total_news = len(news_list)
        
        valid_news = [
            news for news in news_list 
            if news.get('success', False) and news.get('title', '').strip()
        ]
        
        logger.info(f"Processing {len(valid_news)} valid news from {self.stats.total_news} total")
        
        all_results = []
        
        async with LiferayClient(self.config) as client:
            for i in range(0, len(valid_news), self.batch_size):
                batch = valid_news[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                
                logger.info(f"Processing batch {batch_num} with {len(batch)} items")
                
                batch_results = await self.process_news_batch(client, batch)
                all_results.extend(batch_results)
                
                # Conta falhas
                failed_in_batch = sum(1 for r in batch_results if not r.success)
                self.stats.failed_items += failed_in_batch
                
                # Log do resumo do lote
                success_in_batch = len(batch_results) - failed_in_batch
                logger.info(f"Batch {batch_num} completed: {success_in_batch} success, {failed_in_batch} failed")
                
                # Aguarda antes do próximo lote
                if i + self.batch_size < len(valid_news):
                    logger.info(f"Waiting {self.delay}s before next batch...")
                    await asyncio.sleep(self.delay)
        
        self.stats.end_time = asyncio.get_event_loop().time()
        self._log_final_stats()
        return all_results
    
    def _log_final_stats(self):
        """
        Registra estatísticas finais
        """
        logger.info("="*60)
        logger.info("STRUCTURED CONTENT PROCESSING COMPLETED")
        logger.info("="*60)
        logger.info(f"Total news processed: {self.stats.total_news}")
        logger.info(f"Folders created: {self.stats.folders_created}")
        logger.info(f"Contents created: {self.stats.contents_created}")
        logger.info(f"Images uploaded: {self.stats.images_uploaded}")
        logger.info(f"Failed items: {self.stats.failed_items}")
        logger.info(f"Success rate: {self.stats.success_rate:.1f}%")
        logger.info(f"Processing time: {self.stats.duration:.2f}s")
        logger.info("="*60)
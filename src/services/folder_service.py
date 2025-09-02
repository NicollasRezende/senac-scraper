import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.services.liferay_client import LiferayClient
from src.config.liferay_config import LiferayConfig


logger = logging.getLogger(__name__)


@dataclass
class FolderInfo:
    id: int
    name: str
    parent_id: Optional[int] = None


class FolderService:
    def __init__(self, config: LiferayConfig):
        self.config = config
        self.created_folders: Dict[str, FolderInfo] = {}
    
    @staticmethod
    def sanitize_folder_name(title: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*]', ' ', title)
        sanitized = re.sub(r'[^\w\s-]', '', sanitized)
        sanitized = re.sub(r'\s+', ' ', sanitized)
        return sanitized.strip()[:100]
    
    async def folder_exists(self, client: LiferayClient, folder_name: str) -> Optional[FolderInfo]:
        try:
            # Se temos uma pasta pai, lista as pastas filhas; senão lista as principais
            if self.config.parent_folder_id:
                endpoint = f"document-folders/{self.config.parent_folder_id}/document-folders"
                response = await client.get(endpoint)
            else:
                response = await client.get_folders()
                
            folders = response.get('items', [])
            
            for folder in folders:
                if folder['name'] == folder_name:
                    return FolderInfo(
                        id=folder['id'],
                        name=folder['name'],
                        parent_id=folder.get('parentDocumentFolderId')
                    )
            return None
        except Exception as e:
            logger.error(f"Error checking folder existence: {e}")
            return None
    
    async def create_folder_for_news(self, client: LiferayClient, news_title: str) -> Optional[FolderInfo]:
        folder_name = self.sanitize_folder_name(news_title)
        
        if folder_name in self.created_folders:
            return self.created_folders[folder_name]
        
        # Temporariamente desabilitado - o endpoint pode não existir
        # existing_folder = await self.folder_exists(client, folder_name)  
        # if existing_folder:
        #     self.created_folders[folder_name] = existing_folder
        #     return existing_folder
        
        try:
            response = await client.create_folder(
                name=folder_name,
                description=f"Pasta para notícia: {news_title[:200]}",
                parent_folder_id=self.config.parent_folder_id
            )
            
            folder_info = FolderInfo(
                id=response['id'],
                name=response['name'],
                parent_id=response.get('parentDocumentFolderId')
            )
            
            self.created_folders[folder_name] = folder_info
            logger.info(f"Folder created successfully: {folder_name} (ID: {folder_info.id})")
            return folder_info
            
        except Exception as e:
            logger.error(f"Error creating folder '{folder_name}': {e}")
            return None
    
    async def create_folders_batch(self, client: LiferayClient, news_list: List[Dict[str, Any]], 
                                 batch_size: int = 5, delay: float = 1.0) -> List[Optional[FolderInfo]]:
        results = []
        
        for i in range(0, len(news_list), batch_size):
            batch = news_list[i:i + batch_size]
            batch_tasks = []
            
            for news in batch:
                if news.get('success', False) and news.get('title'):
                    task = self.create_folder_for_news(client, news['title'])
                    batch_tasks.append(task)
                else:
                    async def dummy_task():
                        return None
                    batch_tasks.append(dummy_task())
            
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                results.extend(batch_results)
                
                if i + batch_size < len(news_list):
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                results.extend([None] * len(batch))
        
        return results
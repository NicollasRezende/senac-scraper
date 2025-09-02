import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from src.services.liferay_client import LiferayClient
from src.config.liferay_config import LiferayConfig


logger = logging.getLogger(__name__)


@dataclass
class StructuredContentFolderInfo:
    id: int
    name: str
    description: str = ""
    parent_folder_id: Optional[int] = None


class StructuredContentFolderService:
    def __init__(self, config: LiferayConfig):
        self.config = config
        # Temporariamente vamos criar diretamente no site (sem pasta pai)
        self.parent_folder_id = None  # getattr(config, 'structured_content_parent_folder_id', None)
    
    async def create_folder_for_news(self, client: LiferayClient, 
                                   news_title: str) -> Optional[StructuredContentFolderInfo]:
        """
        Cria uma pasta de conteúdo estruturado para uma notícia específica ou retorna a existente
        """
        try:
            # Sanitiza o nome da pasta
            folder_name = self._sanitize_folder_name(news_title)
            
            # Primeiro, tenta encontrar a pasta se já existe
            existing_folder = await self._find_existing_folder(client, folder_name)
            if existing_folder:
                logger.info(f"Using existing structured content folder: {folder_name} (ID: {existing_folder.id})")
                return existing_folder
            
            # Se não existe, cria uma nova
            # Se temos uma pasta pai configurada, criar dentro dela; senão criar no site
            if self.parent_folder_id:
                endpoint = f"structured-content-folders/{self.parent_folder_id}/structured-content-folders"
                payload = {
                    "description": f"Pasta para a notícia: {news_title}",
                    "name": folder_name,
                    "parentStructuredContentFolderId": self.parent_folder_id,
                    "viewableBy": "Anyone"
                }
            else:
                endpoint = "structured-content-folders"
                payload = {
                    "description": f"Pasta para a notícia: {news_title}",
                    "name": folder_name,
                    "viewableBy": "Anyone"
                }
            
            # Faz a requisição
            response = await client.post(endpoint, payload)
            
            if response and 'id' in response:
                folder_info = StructuredContentFolderInfo(
                    id=response['id'],
                    name=response['name'],
                    description=response.get('description', ''),
                    parent_folder_id=response.get('parentStructuredContentFolderId')
                )
                
                logger.info(f"Structured content folder created successfully: {folder_name} (ID: {folder_info.id})")
                return folder_info
            else:
                logger.error(f"Failed to create structured content folder: {news_title}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating structured content folder for '{news_title}': {e}")
            return None
    
    async def _find_existing_folder(self, client: LiferayClient, 
                                  folder_name: str) -> Optional[StructuredContentFolderInfo]:
        """
        Procura uma pasta existente com o nome especificado
        """
        try:
            # Lista todas as pastas do site
            response = await client.get("structured-content-folders")
            if response and 'items' in response:
                for folder in response['items']:
                    if folder.get('name') == folder_name:
                        return StructuredContentFolderInfo(
                            id=folder['id'],
                            name=folder['name'],
                            description=folder.get('description', ''),
                            parent_folder_id=folder.get('parentStructuredContentFolderId')
                        )
            return None
        except Exception as e:
            logger.warning(f"Error searching for existing folder '{folder_name}': {e}")
            return None
    
    async def get_folder_by_id(self, client: LiferayClient, 
                             folder_id: int) -> Optional[StructuredContentFolderInfo]:
        """
        Recupera informações de uma pasta por ID
        """
        try:
            endpoint = f"structured-content-folders/{folder_id}"
            response = await client.get(endpoint)
            
            if response:
                return StructuredContentFolderInfo(
                    id=response['id'],
                    name=response['name'],
                    description=response.get('description', ''),
                    parent_folder_id=response.get('parentStructuredContentFolderId')
                )
            return None
            
        except Exception as e:
            logger.error(f"Error fetching structured content folder {folder_id}: {e}")
            return None
    
    def _sanitize_folder_name(self, name: str) -> str:
        """
        Sanitiza o nome da pasta removendo caracteres inválidos
        """
        # Remove caracteres especiais e limita o tamanho
        import re
        sanitized = re.sub(r'[<>:"/\\|?*]', ' ', name)
        sanitized = re.sub(r'[^\w\s-]', '', sanitized)
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = sanitized.strip()
        
        # Limita o tamanho para evitar nomes muito longos
        if len(sanitized) > 80:
            sanitized = sanitized[:80].rsplit(' ', 1)[0]
        
        return sanitized or "Noticia_Sem_Titulo"
import asyncio
import logging
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path
from src.services.liferay_client import LiferayClient
from src.config.liferay_config import LiferayConfig
from src.core.content_extractor import ContentExtractor


logger = logging.getLogger(__name__)


class StructuredContentService:
    def __init__(self, config: LiferayConfig):
        self.config = config
        self.content_structure_id = config.content_structure_id or 40374
        self.uploaded_images: Dict[int, Dict[str, int]] = {}  # folder_id -> {url: document_id}
        self.content_extractor = ContentExtractor()
    
    async def create_news_content(self, client: LiferayClient, folder_id: int,
                                news_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Cria o conteúdo estruturado da notícia na pasta especificada
        """
        try:
            # Prepara os dados do conteúdo
            content_fields = await self._prepare_content_fields(client, folder_id, news_data)
            
            # Endpoint para criar conteúdo estruturado dentro da pasta
            endpoint = f"structured-content-folders/{folder_id}/structured-contents"
            
            # Payload para criação do conteúdo
            payload = {
                "title": news_data.get('title', 'Título não informado'),
                "contentStructureId": self.content_structure_id,
                "contentFields": content_fields,
                "viewableBy": "Anyone"
            }
            
            # Faz a requisição usando o método específico para folders
            response = await client.post_to_folder(endpoint, payload)
            
            if response and 'id' in response:
                logger.info(f"✓ Structured content created: {news_data.get('title', '')} (ID: {response['id']})")
                return response
            else:
                logger.error(f"Failed to create structured content: {news_data.get('title', '')}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating structured content: {e}")
            return None
    
    async def _prepare_content_fields(self, client: LiferayClient, folder_id: int,
                                    news_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepara os campos de conteúdo baseado na estrutura definida
        """
        content_fields = []
        
        # Campo 1: img (Capa) - featured_image  
        # Verifica se já temos o ID da imagem uploadada
        featured_image_id = news_data.get('featured_image_id')
        if not featured_image_id:
            # Se não temos o ID, tenta fazer upload
            featured_image_id = await self._upload_image_if_needed(
                client, folder_id, news_data.get('featured_image', ''), 'capa'
            )
        if featured_image_id:
            content_fields.append({
                "name": "img",
                "contentFieldValue": {
                    "image": {
                        "id": featured_image_id,
                        "title": "Imagem de capa",
                        "description": "Imagem de capa da notícia"
                    }
                }
            })
        
        # Campo 2: content (Matéria) - content
        content_html = self._prepare_content_html(news_data)
        content_fields.append({
            "name": "content",
            "contentFieldValue": {
                "data": content_html
            }
        })
        
        return content_fields
    
    async def _upload_image_if_needed(self, client: LiferayClient, folder_id: int,
                                    image_url: str, image_type: str) -> Optional[int]:
        """
        Faz upload de uma imagem e retorna o document ID
        """
        if not image_url or not image_url.startswith('http'):
            return None
        
        # Verifica se já foi uploadada
        if folder_id not in self.uploaded_images:
            self.uploaded_images[folder_id] = {}
        
        if image_url in self.uploaded_images[folder_id]:
            return self.uploaded_images[folder_id][image_url]
        
        try:
            # Baixa a imagem
            image_data, filename = await self._download_image(image_url)
            if not image_data:
                return None
            
            # Faz upload para a document library (folder_id do Documents and Media)
            document_folder_id = self.config.parent_folder_id or 32365
            
            upload_result = await client.upload_document(
                folder_id=document_folder_id,
                file_data=image_data,
                file_name=f"{image_type}_{filename}",
                title=f"Imagem {image_type}",
                description=f"Imagem do tipo {image_type} para notícia"
            )
            
            if upload_result and 'id' in upload_result:
                document_id = upload_result['id']
                self.uploaded_images[folder_id][image_url] = document_id
                logger.info(f"✓ Image uploaded for structured content: {filename} (ID: {document_id})")
                return document_id
            
        except Exception as e:
            logger.warning(f"Failed to upload image {image_url}: {e}")
        
        return None
    
    async def _upload_gallery_images(self, client: LiferayClient, folder_id: int,
                                   news_data: Dict[str, Any]) -> List[int]:
        """
        Faz upload das imagens da galeria e retorna lista de document IDs
        """
        gallery_ids = []
        content_images = news_data.get('content_images', [])
        
        for i, img_data in enumerate(content_images):
            if isinstance(img_data, dict) and 'src' in img_data:
                img_url = img_data['src']
            elif isinstance(img_data, str):
                img_url = img_data
            else:
                continue
            
            document_id = await self._upload_image_if_needed(
                client, folder_id, img_url, f'galeria_{i+1}'
            )
            if document_id:
                gallery_ids.append(document_id)
        
        return gallery_ids
    
    async def _download_image(self, image_url: str) -> Tuple[Optional[bytes], str]:
        """
        Baixa uma imagem da URL
        """
        if not image_url or not image_url.startswith('http'):
            return None, ""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        filename = self._extract_filename(image_url)
                        return image_data, filename
        except Exception as e:
            logger.warning(f"Failed to download image {image_url}: {e}")
        
        return None, ""
    
    def _extract_filename(self, url: str) -> str:
        """
        Extrai o nome do arquivo da URL
        """
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename or '.' not in filename:
            filename = f"image_{abs(hash(url)) % 10000}.jpg"
        return filename
    
    def _prepare_content_html(self, news_data: Dict[str, Any]) -> str:
        """
        Prepara o HTML do conteúdo da notícia
        """
        content = news_data.get('content', '')
        url = news_data.get('url', '')
        
        # Sanitiza o conteúdo para remover referências problemáticas
        if content and url:
            content = self.content_extractor.sanitize_content_for_liferay(content, url)
        
        return content
    
    def _format_date(self, date_str: str) -> str:
        """
        Formata a data para o padrão ISO
        """
        if not date_str:
            return "2025-09-02T17:00:00Z"
        
        try:
            # Assumindo formato brasileiro dd/mm/yyyy
            from datetime import datetime
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%dT12:00:00Z")
        except:
            return "2025-09-02T17:00:00Z"
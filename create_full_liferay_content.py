#!/usr/bin/env python3
"""
Script integrado para criar todo o processo no Liferay:
1. Criar pastas de documentos
2. Fazer upload de documentos/imagens
3. Criar pastas de conteúdo estruturado
4. Criar conteúdo estruturado com todas as referências
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from src.config.liferay_config import LiferayConfig
from src.services.liferay_client import LiferayClient
from src.services.document_service import DocumentService
from src.services.folder_service import FolderService
from src.services.structured_content_folder_service import StructuredContentFolderService
from src.services.structured_content_service import StructuredContentService


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('full_liferay_creation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FullLiferayProcessor:
    def __init__(self, config: LiferayConfig, dev_mode: bool = False):
        self.config = config
        self.dev_mode = dev_mode
        self.batch_size = 1 if dev_mode else config.batch_size
        self.max_items = 3 if dev_mode else None
        
        # Serviços
        self.document_service = DocumentService(config)
        self.folder_service = FolderService(config)
        self.structured_content_folder_service = StructuredContentFolderService(config)
        self.structured_content_service = StructuredContentService(config)
    
    async def process_all_news(self, news_file: str):
        """
        Processa todas as notícias fazendo o processo completo
        """
        logger.info("Starting Full Liferay Content Creation Process")
        
        if self.dev_mode:
            logger.info("🚧 DEV MODE: Processing only 3 news items for testing")
        else:
            logger.info("🔄 PRODUCTION MODE: Processing all news items")
        
        # Carrega notícias
        with open(news_file, 'r', encoding='utf-8') as f:
            all_news = json.load(f)
        
        # Limita para dev mode se necessário
        if self.dev_mode and self.max_items:
            all_news = all_news[:self.max_items]
        
        logger.info(f"Processing {len(all_news)} news items")
        
        # Estatísticas
        stats = {
            'total': len(all_news),
            'success': 0,
            'failed': 0,
            'doc_folders_created': 0,
            'docs_uploaded': 0,
            'content_folders_created': 0,
            'contents_created': 0
        }
        
        async with LiferayClient(self.config) as client:
            for i, news_item in enumerate(all_news, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"Processing news {i}/{len(all_news)}: {news_item.get('title', 'No title')[:50]}...")
                logger.info(f"{'='*80}")
                
                success = await self._process_single_news(client, news_item, stats)
                
                if success:
                    stats['success'] += 1
                    logger.info(f"✅ News {i} processed successfully")
                else:
                    stats['failed'] += 1
                    logger.error(f"❌ News {i} failed to process")
                
                # Delay entre processamentos
                if i < len(all_news):
                    logger.info(f"Waiting {self.config.batch_delay}s before next item...")
                    await asyncio.sleep(self.config.batch_delay)
        
        # Log final
        self._log_final_stats(stats)
    
    async def _process_single_news(self, client: LiferayClient, news_item: dict, stats: dict) -> bool:
        """
        Processa uma única notícia com todo o fluxo completo
        """
        try:
            news_title = news_item.get('title', 'No title')
            
            # Etapa 1: Criar pasta de documentos
            logger.info("📁 Step 1: Creating document folder...")
            doc_folder_id = await self._create_document_folder(client, news_item, stats)
            if not doc_folder_id:
                logger.error("Failed to create document folder, skipping news item")
                return False
            
            # Etapa 2: Upload de imagens
            logger.info("🖼️  Step 2: Uploading images...")
            uploaded_images = await self._upload_images(client, doc_folder_id, news_item, stats)
            
            # Etapa 3: Criar pasta de conteúdo estruturado
            logger.info("📂 Step 3: Creating structured content folder...")
            content_folder_id = await self._create_content_folder(client, news_item, stats)
            
            # Etapa 4: Criar conteúdo estruturado
            if content_folder_id:
                logger.info("📄 Step 4: Creating structured content...")
                content_created = await self._create_structured_content(
                    client, content_folder_id, news_item, uploaded_images, stats
                )
                return content_created
            else:
                logger.warning("⚠️  Could not create/find content folder, skipping structured content creation for now")
                return True  # Considera sucesso parcial (pasta doc + images criados)
            
        except Exception as e:
            logger.error(f"Error processing news item '{news_title}': {e}")
            return False
    
    async def _create_document_folder(self, client: LiferayClient, news_item: dict, stats: dict) -> int:
        """
        Cria pasta de documentos para a notícia (ou usa existente)
        """
        try:
            folder_info = await self.folder_service.create_folder_for_news(
                client, news_item.get('title', 'No title')
            )
            if folder_info:
                stats['doc_folders_created'] += 1
                logger.info(f"✅ Document folder ready: {folder_info.name} (ID: {folder_info.id})")
                return folder_info.id
            
            # Se não conseguiu criar, pode ser que já existe - vamos tentar um ID default temporário
            # Isso deve ser melhorado depois, mas por ora vamos usar a pasta pai
            logger.warning("Could not create/find document folder, using parent folder as fallback")
            return self.config.parent_folder_id or 32365
            
        except Exception as e:
            logger.error(f"Error creating document folder: {e}")
            # Fallback para pasta pai
            return self.config.parent_folder_id or 32365
    
    async def _upload_images(self, client: LiferayClient, folder_id: int, news_item: dict, stats: dict) -> dict:
        """
        Faz upload das imagens da notícia
        """
        uploaded_images = {}
        
        try:
            # Upload de todas as imagens da notícia
            logger.info(f"Uploading images for news item...")
            upload_results = await self.document_service.upload_images_to_folder(
                client, folder_id, news_item
            )
            
            # Processa os resultados do upload
            for result in upload_results:
                if result and 'id' in result:
                    # Identifica se é a featured image baseada no nome/título
                    title = result.get('title', '').lower()
                    if 'featured' in title or 'capa' in title:
                        uploaded_images['featured'] = result['id']
                    
                    stats['docs_uploaded'] += 1
                    logger.info(f"✅ Image uploaded: {result.get('title', 'Unknown')} (ID: {result['id']})")
            
            # Se não encontrou uma featured image específica, usa o primeiro resultado
            if upload_results and not uploaded_images.get('featured'):
                first_result = upload_results[0]
                if first_result and 'id' in first_result:
                    uploaded_images['featured'] = first_result['id']
                    logger.info(f"Using first uploaded image as featured: ID {first_result['id']}")
            
        except Exception as e:
            logger.error(f"Error uploading images: {e}")
        
        return uploaded_images
    
    async def _create_content_folder(self, client: LiferayClient, news_item: dict, stats: dict) -> int:
        """
        Cria pasta de conteúdo estruturado para a notícia (ou usa existente)
        """
        try:
            folder_info = await self.structured_content_folder_service.create_folder_for_news(
                client, news_item.get('title', 'No title')
            )
            if folder_info:
                stats['content_folders_created'] += 1
                logger.info(f"✅ Structured content folder ready: {folder_info.name} (ID: {folder_info.id})")
                return folder_info.id
            
            # Se não conseguiu criar, a pasta provavelmente já existe
            logger.warning("Could not create specific content folder, probably already exists")
            return None
            
        except Exception as e:
            logger.error(f"Error with structured content folder: {e}")
            return None
    
    async def _create_structured_content(self, client: LiferayClient, folder_id: int, 
                                       news_item: dict, uploaded_images: dict, stats: dict) -> bool:
        """
        Cria o conteúdo estruturado com todas as referências
        """
        try:
            # Adiciona as imagens uploadadas aos dados da notícia
            enhanced_news_item = news_item.copy()
            if 'featured' in uploaded_images:
                enhanced_news_item['featured_image_id'] = uploaded_images['featured']
            
            content_result = await self.structured_content_service.create_news_content(
                client, folder_id, enhanced_news_item
            )
            
            if content_result:
                stats['contents_created'] += 1
                logger.info(f"✅ Structured content created: ID {content_result['id']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error creating structured content: {e}")
            return False
    
    def _generate_folder_name(self, title: str, max_length: int = 50) -> str:
        """
        Gera nome da pasta baseado no título
        """
        if not title:
            return "Noticia_sem_titulo"
        
        # Remove caracteres especiais e limita o tamanho
        safe_name = "".join(c for c in title if c.isalnum() or c in " -_")
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length].rstrip()
        
        return safe_name or "Noticia"
    
    def _log_final_stats(self, stats: dict):
        """
        Log das estatísticas finais
        """
        logger.info(f"\n{'='*80}")
        logger.info("FINAL STATISTICS")
        logger.info(f"{'='*80}")
        logger.info(f"Total news processed: {stats['total']}")
        logger.info(f"Successfully processed: {stats['success']}")
        logger.info(f"Failed to process: {stats['failed']}")
        logger.info(f"Document folders created: {stats['doc_folders_created']}")
        logger.info(f"Documents uploaded: {stats['docs_uploaded']}")
        logger.info(f"Content folders created: {stats['content_folders_created']}")
        logger.info(f"Contents created: {stats['contents_created']}")
        logger.info(f"Success rate: {(stats['success']/stats['total']*100):.1f}%")
        logger.info(f"{'='*80}")


async def main():
    """
    Função principal
    """
    # Carrega configuração do .env
    load_dotenv()
    
    try:
        config = LiferayConfig(
            base_url=os.getenv('LIFERAY_BASE_URL', 'http://localhost:8080'),
            username=os.getenv('LIFERAY_USERNAME', 'test@liferay.com'),
            password=os.getenv('LIFERAY_PASSWORD', 'test'),
            site_id=int(os.getenv('LIFERAY_SITE_ID', '20117')),
            parent_folder_id=int(os.getenv('LIFERAY_PARENT_FOLDER_ID', '32365')),
            structured_content_parent_folder_id=int(os.getenv('STRUCTURED_CONTENT_PARENT_FOLDER_ID', '40384')),
            content_structure_id=int(os.getenv('STRUCTURED_CONTENT_STRUCTURE_ID', '40374'))
        )
        
        # Configuração adicional para o processador
        config.batch_size = int(os.getenv('BATCH_SIZE', '1'))
        config.batch_delay = float(os.getenv('BATCH_DELAY', '2.0'))
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return
    
    # Escolha do modo (você pode alterar aqui)
    DEV_MODE = True  # Mude para False para processar todas as notícias
    
    # Arquivo de notícias
    news_file = 'noticias_final.json'
    
    if not Path(news_file).exists():
        logger.error(f"News file not found: {news_file}")
        return
    
    # Log da configuração
    logger.info("Starting Liferay Full Content Creation Service")
    logger.info("This will create: doc folders + docs + content folders + structured contents")
    logger.info("Configuration loaded from .env file")
    
    mode_str = "DEVELOPMENT (3 items)" if DEV_MODE else "PRODUCTION (all items)"
    logger.info(f"Running in {mode_str} mode")
    
    # Processa
    processor = FullLiferayProcessor(config, dev_mode=DEV_MODE)
    await processor.process_all_news(news_file)


if __name__ == "__main__":
    asyncio.run(main())
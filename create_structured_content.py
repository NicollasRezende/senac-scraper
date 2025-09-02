#!/usr/bin/env python3
"""
Script para criação de conteúdo estruturado no Liferay a partir dos dados das notícias.
Este script:
1. Cria pastas de conteúdo estruturado para cada notícia
2. Cria o conteúdo estruturado com os campos: Capa, Matéria e Galeria de Fotos
3. Faz upload das imagens necessárias
"""

import asyncio
import json
import logging
import os
import time
from dotenv import load_dotenv
from src.config.liferay_config import LiferayConfig
from src.services.structured_content_processor import StructuredContentProcessor


def setup_logging():
    """Configura o sistema de logging"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('structured_content_creation.log'),
            logging.StreamHandler()
        ]
    )


def load_news_data(filename: str):
    """Carrega os dados das notícias do arquivo JSON"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File {filename} not found!")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file {filename}: {e}")
        return []


async def main():
    """Função principal"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Liferay Structured Content Creation Service")
    logger.info("This will create structured content folders + structured contents + upload images")
    
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
        
        logger.info("Configuration loaded from .env file")
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return
    
    # Parâmetros de processamento
    news_file = os.getenv('NEWS_FILE', 'noticias_final.json')
    batch_size = int(os.getenv('BATCH_SIZE', '3'))
    batch_delay = float(os.getenv('BATCH_DELAY', '2.0'))
    
    # Carrega dados das notícias
    news_data = load_news_data(news_file)
    if not news_data:
        logger.error("No news data loaded. Exiting.")
        return
    
    logger.info("Processing configuration:")
    logger.info(f"  - News file: {news_file}")
    logger.info(f"  - Total news: {len(news_data)}")
    logger.info(f"  - Batch size: {batch_size}")
    logger.info(f"  - Batch delay: {batch_delay}s")
    logger.info(f"  - Site ID: {config.site_id}")
    logger.info(f"  - Content Structure ID: 40374")
    logger.info(f"  - Parent Folder ID: 40384 (Noticias)")
    
    # Inicializa o processador
    processor = StructuredContentProcessor(
        config=config,
        batch_size=batch_size,
        delay=batch_delay
    )
    
    # Processa todas as notícias
    try:
        results = await processor.process_all_news(news_data)
        
        # Salva resultados para análise posterior se necessário
        output_file = 'structured_content_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            # Converte resultados para formato JSON serializável
            json_results = []
            for result in results:
                json_result = {
                    "success": result.success,
                    "error": result.error,
                    "folder_id": result.folder_info.id if result.folder_info else None,
                    "folder_name": result.folder_info.name if result.folder_info else None,
                    "content_id": result.content_info['id'] if result.content_info else None,
                    "content_title": result.content_info['title'] if result.content_info else None
                }
                json_results.append(json_result)
            
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
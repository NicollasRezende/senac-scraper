import asyncio
import logging
import re
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin
from pathlib import Path
from src.services.liferay_client import LiferayClient
from src.config.liferay_config import LiferayConfig


logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, config: LiferayConfig):
        self.config = config
        # Track images uploaded per folder to avoid duplicates within the same folder
        self.folder_uploaded_images: Dict[int, Dict[str, str]] = {}
    
    def generate_html_content(self, news_data: Dict[str, Any]) -> str:
        title = news_data.get('title', 'Sem título')
        author = news_data.get('author', 'Autor não informado')
        date = news_data.get('date', 'Data não informada')
        content = news_data.get('content', '')
        featured_image = news_data.get('featured_image', '')
        
        html_template = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ border-bottom: 2px solid #ccc; padding-bottom: 20px; margin-bottom: 30px; }}
        .title {{ color: #333; font-size: 2em; margin-bottom: 10px; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        .featured-image {{ max-width: 100%; height: auto; margin: 20px 0; }}
        .content {{ line-height: 1.6; color: #444; }}
        .content img {{ max-width: 100%; height: auto; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">{title}</h1>
        <div class="meta">
            <p><strong>Autor:</strong> {author}</p>
            <p><strong>Data:</strong> {date}</p>
        </div>
        {f'<img src="{featured_image}" alt="Imagem destacada" class="featured-image">' if featured_image else ''}
    </div>
    <div class="content">
        {content}
    </div>
</body>
</html>
"""
        return html_template.strip()
    
    async def download_image(self, image_url: str) -> Optional[Tuple[bytes, str]]:
        if not image_url or not image_url.startswith('http'):
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        filename = self._extract_filename(image_url)
                        return image_data, filename
        except Exception as e:
            logger.warning(f"Failed to download image {image_url}: {e}")
        return None
    
    def _extract_filename(self, url: str) -> str:
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename or '.' not in filename:
            filename = f"image_{abs(hash(url)) % 10000}.jpg"
        return filename
    
    def extract_image_urls(self, content: str) -> List[str]:
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(img_pattern, content, re.IGNORECASE)
        return [url for url in matches if url.startswith('http')]
    
    async def upload_html_document(self, client: LiferayClient, folder_id: int, 
                                 news_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            html_content = self.generate_html_content(news_data)
            html_bytes = html_content.encode('utf-8')
            
            title = news_data.get('title', 'Noticia')
            filename = f"{self._sanitize_filename(title)}.html"
            
            result = await client.upload_document(
                folder_id=folder_id,
                file_data=html_bytes,
                file_name=filename,
                title=title,
                description=f"Conteúdo da notícia: {title[:200]}"
            )
            
            logger.info(f"✓ HTML uploaded: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading HTML document: {e}")
            return None
    
    async def upload_images_to_folder(self, client: LiferayClient, folder_id: int, 
                                    news_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        
        # Lista de URLs para baixar
        image_urls = []
        
        # Featured image
        featured_image = news_data.get('featured_image', '')
        if featured_image and isinstance(featured_image, str):
            image_urls.append(featured_image)
        
        # Images from content_images array
        content_images = news_data.get('content_images', [])
        if isinstance(content_images, list):
            for img in content_images:
                if isinstance(img, str):
                    image_urls.append(img)
                elif isinstance(img, dict) and 'src' in img:
                    image_urls.append(img['src'])
        
        # Images from HTML content
        content = news_data.get('content', '')
        if isinstance(content, str):
            content_image_urls = self.extract_image_urls(content)
            image_urls.extend(content_image_urls)
        
        # Remove duplicatas
        unique_urls = list(set(url for url in image_urls if url and isinstance(url, str)))
        
        # Initialize folder tracking if not exists
        if folder_id not in self.folder_uploaded_images:
            self.folder_uploaded_images[folder_id] = {}
        
        for image_url in unique_urls:
            # Skip if already uploaded to this specific folder to avoid duplicates within the same folder
            if image_url in self.folder_uploaded_images[folder_id]:
                logger.info(f"Image already uploaded to folder {folder_id}, skipping: {image_url}")
                continue
                
            try:
                download_result = await self.download_image(image_url)
                if download_result:
                    image_data, filename = download_result
                    
                    # Add news title prefix to make filename unique
                    news_title = self._sanitize_filename(news_data.get('title', ''))[:30]
                    unique_filename = f"{news_title}_{filename}"
                    
                    upload_result = await client.upload_document(
                        folder_id=folder_id,
                        file_data=image_data,
                        file_name=unique_filename,
                        title=unique_filename,
                        description=f"Imagem da notícia: {news_data.get('title', '')[:100]}"
                    )
                    
                    if upload_result:
                        results.append(upload_result)
                        # Track image as uploaded to this specific folder
                        self.folder_uploaded_images[folder_id][image_url] = upload_result.get('contentUrl', '')
                        logger.info(f"✓ Image uploaded to folder {folder_id}: {unique_filename}")
                    
            except Exception as e:
                logger.warning(f"Failed to upload image {image_url}: {e}")
        
        return results
    
    def _sanitize_filename(self, title: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*]', ' ', title)
        sanitized = re.sub(r'[^\w\s-]', '', sanitized)
        sanitized = re.sub(r'\s+', '_', sanitized)
        return sanitized.strip('_')[:50]
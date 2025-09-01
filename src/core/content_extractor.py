from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, List, Tuple
from ..models.news_article import ImageData

class ContentExtractor:
    def __init__(self):
        self.selectors = {
            'title': 'h1.elementor-heading-title.elementor-size-default',
            'author': '.elementor-post-info__item--type-author',
            'date': '.elementor-post-info__item--type-date time',
            'featured_image': '.elementor-widget-image img',
            'content_container': '.elementor-widget-theme-post-content',
            'content_elements': 'p, ul, ol, blockquote, h2, h3, h4, h5, h6, figure.wp-block-image',
            'gallery': '.wp-block-gallery'
        }
    
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        element = soup.select_one(self.selectors['title'])
        return element.get_text(strip=True) if element else None
    
    def extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        element = soup.select_one(self.selectors['author'])
        return element.get_text(strip=True) if element else None
    
    def extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        element = soup.select_one(self.selectors['date'])
        return element.get_text(strip=True) if element else None
    
    def extract_featured_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        element = soup.select_one(self.selectors['featured_image'])
        if element and element.get('src'):
            return urljoin(base_url, element['src'])
        return None
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Tuple[Optional[str], List[ImageData]]:
        container = soup.select_one(self.selectors['content_container'])
        if not container:
            return None, []
        
        content_images = []
        
        individual_imgs = container.select('figure.wp-block-image img')
        for img in individual_imgs:
            if img.get('src'):
                img_data = ImageData(
                    src=urljoin(base_url, img['src']),
                    alt=img.get('alt', ''),
                    width=img.get('width'),
                    height=img.get('height'),
                    type='individual'
                )
                content_images.append(img_data)
        
        gallery_imgs = container.select('.wp-block-gallery img')
        for img in gallery_imgs:
            if img.get('src'):
                img_data = ImageData(
                    src=urljoin(base_url, img['src']),
                    alt=img.get('alt', ''),
                    width=img.get('width'),
                    height=img.get('height'),
                    type='gallery'
                )
                content_images.append(img_data)
        
        elements = container.select('p, ul, ol, blockquote, h2, h3, h4, h5, h6, figure.wp-block-image, figure.wp-block-gallery')
        if elements:
            content_html = ''.join(str(element) for element in elements)
            return content_html, content_images
        
        return str(container), content_images
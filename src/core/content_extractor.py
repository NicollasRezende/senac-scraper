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
        # Try to find the main article image (usually the first large image in the content area)
        main_content_area = soup.select_one('.elementor-col-66, .elementor-widget-theme-post-content')
        if main_content_area:
            # Look for the first image in the main content area
            featured_img = main_content_area.select_one('img[src*="wp-content/uploads"]:not([src*="logo"]):not([src*="icon"])')
            if featured_img and featured_img.get('src'):
                return urljoin(base_url, featured_img['src'])
        
        # Fallback to original method
        element = soup.select_one(self.selectors['featured_image'])
        if element and element.get('src') and 'logo' not in element['src']:
            return urljoin(base_url, element['src'])
        return None
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Tuple[Optional[str], List[ImageData]]:
        # Try to find the main content area more broadly
        container = soup.select_one(self.selectors['content_container'])
        if not container:
            # Fallback to broader content area
            container = soup.select_one('.elementor-col-66, .elementor-section')
            if not container:
                return None, []
        
        content_images = []
        
        # Extract images from the entire content area, not just specific containers
        all_content_imgs = container.select('img[src*="wp-content/uploads"]:not([src*="logo"])')
        for img in all_content_imgs:
            if img.get('src'):
                # Determine image type based on parent elements
                img_type = 'individual'
                if img.find_parent('.wp-block-gallery'):
                    img_type = 'gallery'
                elif img.find_parent('.elementor-widget-image'):
                    img_type = 'individual'
                
                img_data = ImageData(
                    src=urljoin(base_url, img['src']),
                    alt=img.get('alt', ''),
                    width=img.get('width'),
                    height=img.get('height'),
                    type=img_type
                )
                content_images.append(img_data)
        
        # Extract content HTML - look for the theme post content first
        content_container = soup.select_one('.elementor-widget-theme-post-content')
        if content_container:
            elements = content_container.select('p, ul, ol, blockquote, h2, h3, h4, h5, h6, figure.wp-block-image, figure.wp-block-gallery')
            if elements:
                content_html = ''.join(str(element) for element in elements)
                return content_html, content_images
        
        # Fallback - use the broader container
        return str(container), content_images
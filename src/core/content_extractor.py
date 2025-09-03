from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, List, Tuple
import re
from ..models.news_article import ImageData

class ContentExtractor:
    def __init__(self):
        self.selectors = {
            'title': 'h2.titulo.text-center',
            'author': '.elementor-post-info__item--type-author',
            'date': 'p.texto.text-justify',
            'featured_image': '#curso.imgnoticiadetalhe img',
            'content_container': '#ctl00_PlaceHolderMain_ctl06__ControlWrapper_RichHtmlField',
            'content_elements': 'p, ul, ol, blockquote, h2, h3, h4, h5, h6',
            'gallery': '.wp-block-gallery'
        }
    
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        element = soup.select_one(self.selectors['title'])
        return element.get_text(strip=True) if element else None
    
    def extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        element = soup.select_one(self.selectors['author'])
        return element.get_text(strip=True) if element else None
    
    def extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        date_element = soup.select_one(self.selectors['date'])
        if date_element:
            text_content = date_element.get_text(strip=True)
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text_content)
            if date_match:
                return date_match.group(1)
        
        old_date_element = soup.select_one('.elementor-post-info__item--type-date time')
        return old_date_element.get_text(strip=True) if old_date_element else None
    
    def extract_featured_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        featured_img = soup.select_one(self.selectors['featured_image'])
        if featured_img and featured_img.get('src'):
            return urljoin(base_url, featured_img['src'])
        
        main_content_area = soup.select_one('.elementor-col-66, .elementor-widget-theme-post-content')
        if main_content_area:
            old_featured_img = main_content_area.select_one('img[src*="wp-content/uploads"]:not([src*="logo"]):not([src*="icon"])')
            if old_featured_img and old_featured_img.get('src'):
                return urljoin(base_url, old_featured_img['src'])
        
        element = soup.select_one('.elementor-widget-image img')
        if element and element.get('src') and 'logo' not in element['src']:
            return urljoin(base_url, element['src'])
        return None
    
    def extract_content(self, soup: BeautifulSoup, base_url: str) -> Tuple[Optional[str], List[ImageData]]:
        content_images = []
        
        container = soup.select_one(self.selectors['content_container'])
        if not container:
            container = soup.select_one('.elementor-widget-theme-post-content')
            if not container:
                container = soup.select_one('.elementor-col-66, .elementor-section')
                if not container:
                    return None, []
        
        img_selectors = [
            'img[src*="/Noticias/PublishingImages/"]',
            'img[src*="wp-content/uploads"]:not([src*="logo"])'
        ]
        
        for selector in img_selectors:
            all_content_imgs = container.select(selector)
            for img in all_content_imgs:
                if img.get('src') and not any(keyword in img['src'].lower() for keyword in ['logo', 'icon']):
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
        
        if container:
            elements = container.select(self.selectors['content_elements'])
            if elements:
                content_html = ''.join(str(element) for element in elements)
                return content_html, content_images
            else:
                return str(container), content_images
        
        return None, content_images
    
    def sanitize_content_for_liferay(self, html_content: str, base_url: str) -> str:
        """
        Sanitize HTML content to remove/fix references that cause Liferay validation errors.
        - Convert relative links to absolute or remove them
        - Remove problematic layout references
        - Fix image paths
        """
        if not html_content:
            return html_content
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove or fix problematic links
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                # Remove internal layout references that don't exist in target environment
                if href.startswith('/') and any(pattern in href for pattern in [
                    '/Noticias/', '/Unidades/', '/faculdade/', '/PublishingImages/', 
                    '.aspx', '/Paginas/'
                ]):
                    # Convert to absolute URL or remove the link
                    try:
                        absolute_url = urljoin(base_url, href)
                        link['href'] = absolute_url
                    except:
                        # Remove link but keep text content
                        link.unwrap()
                elif href.startswith('#'):
                    # Remove anchor links as they reference layouts that don't exist
                    link.unwrap()
        
        # Fix image references
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.startswith('/'):
                # Convert relative image paths to absolute URLs
                try:
                    absolute_url = urljoin(base_url, src)
                    img['src'] = absolute_url
                except:
                    # Remove problematic images
                    img.decompose()
        
        # Remove empty paragraphs and cleanup
        for p in soup.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()
        
        return str(soup)
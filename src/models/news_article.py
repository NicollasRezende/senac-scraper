from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ImageData:
    src: str
    alt: str = ""
    width: Optional[str] = None
    height: Optional[str] = None
    type: str = "individual"

@dataclass
class NewsArticle:
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    featured_image: Optional[str] = None
    content: Optional[str] = None
    content_images: List[ImageData] = None
    success: bool = False
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.content_images is None:
            self.content_images = []
    
    def to_dict(self) -> Dict:
        return {
            'url': self.url,
            'title': self.title,
            'author': self.author,
            'date': self.date,
            'featured_image': self.featured_image,
            'content': self.content,
            'content_images': [
                {
                    'src': img.src,
                    'alt': img.alt,
                    'width': img.width,
                    'height': img.height,
                    'type': img.type
                } for img in self.content_images
            ],
            'success': self.success,
            'error': self.error
        }
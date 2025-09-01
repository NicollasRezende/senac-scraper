from typing import List, Dict
from ..models.news_article import NewsArticle

class Statistics:
    @staticmethod
    def calculate_stats(results: List[Dict]) -> Dict:
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        failed = total - successful
        
        total_content_images = sum(len(r.get('content_images', [])) for r in results if r.get('success'))
        articles_with_images = sum(1 for r in results if r.get('success') and r.get('content_images'))
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': round((successful / total * 100), 2) if total > 0 else 0,
            'total_content_images': total_content_images,
            'articles_with_images': articles_with_images,
            'avg_images_per_article': round(total_content_images / successful, 2) if successful > 0 else 0
        }
import json
from typing import List, Dict
from ..models.news_article import NewsArticle

class FileHandler:
    @staticmethod
    def save_json(data: List[Dict], file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_urls_from_file(file_path: str) -> List[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    @staticmethod
    def save_urls_to_file(urls: List[str], file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
from dataclasses import dataclass
from typing import Dict

@dataclass
class ScrapingConfig:
    timeout: int = 30
    max_workers: int = 4
    delay_between_requests: float = 0.5
    max_retries: int = 2
    retry_delay: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            'timeout': self.timeout,
            'max_workers': self.max_workers,
            'delay_between_requests': self.delay_between_requests,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        }

@dataclass
class UrlCollectorConfig:
    delay: float = 1.0
    timeout: int = 30
    start_page: int = 1
    end_page: int = 50
    
    def to_dict(self) -> Dict:
        return {
            'delay': self.delay,
            'timeout': self.timeout,
            'start_page': self.start_page,
            'end_page': self.end_page
        }
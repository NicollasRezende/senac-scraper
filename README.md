# Senac News Scraper

Sistema empresarial para coleta e scraping de notícias do portal Senac-DF.

## Estrutura do Projeto

```
src/
├── config/           # Configurações
├── core/            # Componentes centrais
├── models/          # Modelos de dados
├── services/        # Serviços de negócio
└── utils/           # Utilitários
```

## Uso Rápido

```python
from src.senac_scraper import SenacScraper

# Pipeline completo
scraper = SenacScraper()
results = scraper.full_pipeline(start_page=1, end_page=10)

# Apenas coletar URLs
urls = scraper.collect_urls(start_page=1, end_page=5)

# Apenas fazer scraping
results = scraper.scrape_urls('urls.txt')
```

## Configuração Avançada

```python
from src.config.scraping_config import ScrapingConfig
from src.senac_scraper import SenacScraper

config = ScrapingConfig(
    max_workers=6,
    delay_between_requests=0.3,
    max_retries=3,
    timeout=20
)

scraper = SenacScraper(scraping_config=config)
```

## Execução

```bash
python main.py
```

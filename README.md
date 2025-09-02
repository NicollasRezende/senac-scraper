# Senac Content Migration System

Enterprise-grade web scraping and content migration solution for Senac-DF portal. This system provides automated content extraction from the Senac-DF website and seamless migration to Liferay DXP with document management and structured content creation.

## Features

- **Web Scraping**: Automated content extraction from Senac-DF website
- **Content Migration**: Professional migration to Liferay DXP
- **Document Management**: Automated folder creation and file uploads
- **Structured Content**: Automated creation of structured content with proper field mapping
- **Batch Processing**: Configurable batch processing with error handling
- **Professional Architecture**: Enterprise-grade code structure with comprehensive logging

## System Components

### 1. Web Scraping System
- Extract news articles from Senac-DF portal
- Batch processing with rate limiting
- Comprehensive error handling and retry logic

### 2. Content Migration System
- Automated migration to Liferay DXP
- Document folder creation and management
- Structured content creation with image references
- Professional logging and statistics

## Project Structure

```
senac_scrap/
├── scraper.py                          # Web scraping entry point
├── content_migration_system.py         # Liferay migration system (main)
├── config_manager.py                   # Configuration management
├── noticias_final.json                 # Scraped content data
├── .env                                # Environment configuration
├── .env.example                        # Configuration template
└── src/
    ├── config/
    │   ├── scraping_config.py          # Scraping configuration
    │   └── liferay_config.py           # Liferay configuration
    ├── core/
    │   ├── content_extractor.py        # Content extraction logic
    │   └── http_client.py              # HTTP client utilities
    ├── models/
    │   └── news_article.py             # Data models
    ├── services/
    │   ├── scraping_service.py         # Scraping services
    │   ├── liferay_client.py           # Liferay API client
    │   ├── document_service.py         # Document management
    │   ├── folder_service.py           # Folder management
    │   ├── structured_content_service.py    # Content creation
    │   └── structured_content_folder_service.py  # Content folder management
    └── utils/
        ├── file_handler.py             # File utilities
        ├── rate_limiter.py             # Rate limiting
        └── statistics.py               # Statistics tracking
```

## Quick Start

### Prerequisites

1. Python 3.8+
2. Required dependencies (install via requirements.txt if available)
3. Liferay DXP instance (for migration)
4. Environment configuration

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Liferay Configuration
LIFERAY_BASE_URL=http://localhost:8080
LIFERAY_SITE_ID=20117
LIFERAY_USERNAME=your-username
LIFERAY_PASSWORD=your-password

# Document Library Configuration
LIFERAY_PARENT_FOLDER_ID=32365

# Structured Content Configuration
STRUCTURED_CONTENT_STRUCTURE_ID=40374
STRUCTURED_CONTENT_PARENT_FOLDER_ID=40384

# Processing Configuration
BATCH_SIZE=1
BATCH_DELAY=2.0
DEV_MODE=True  # Set to False for production
MAX_DEV_ITEMS=3
```

## Usage

### 1. Web Scraping

Extract content from Senac-DF website:

```bash
# Run the web scraper
python3 scraper.py
```

This will:
- Read URLs from `senac_urls.txt`
- Extract content from each URL
- Save results to `noticias_final.json`
- Generate scraping statistics and logs

### 2. Content Migration

Migrate scraped content to Liferay:

```bash
# Run the migration system
python3 content_migration_system.py
```

This will:
- Create document folders for each news item
- Upload featured images and content images
- Create structured content folders within the "Noticias" parent folder
- Create structured content with proper field mapping (`img` and `content` fields)
- Generate comprehensive migration statistics

### 3. Development vs Production Mode

**Development Mode** (default):
- Processes only 3 items for testing
- Detailed debug logging
- Set `DEV_MODE=True` in `.env`

**Production Mode**:
- Processes all items in the dataset
- Standard logging level
- Set `DEV_MODE=False` in `.env`

## Advanced Configuration

### Scraping Configuration

```python
from src.config.scraping_config import ScrapingConfig
from src.senac_scraper import SenacScraper

config = ScrapingConfig(
    max_workers=6,                    # Concurrent workers
    delay_between_requests=0.3,       # Rate limiting
    max_retries=3,                    # Retry attempts
    timeout=20                        # Request timeout
)

scraper = SenacScraper(scraping_config=config)
```

### Migration Configuration

Configuration is managed through environment variables and the `config_manager.py` system:

```python
from config_manager import ConfigurationManager

# Load development configuration
config = ConfigurationManager.get_development_config()

# Load production configuration
config = ConfigurationManager.get_production_config()
```

## Content Structure

### Scraped Data Format
```json
{
  "url": "https://example.com/news-article",
  "title": "Article Title",
  "author": "Author Name",
  "date": "28/05/2023",
  "featured_image": "https://example.com/image.jpg",
  "content": "<p>Article content...</p>",
  "content_images": [
    {
      "src": "https://example.com/content-image.jpg",
      "alt": "Image description",
      "width": "1024",
      "height": "682"
    }
  ]
}
```

### Liferay Structure Mapping
- **Document Folders**: Created for each news item to store images
- **Structured Content Folders**: Created within "Noticias" parent folder
- **Structured Content Fields**:
  - `img`: Featured image reference (field reference: "img")
  - `content`: Rich text content (field reference: "content")

## Monitoring and Logging

### Log Files
- `scraper.log`: Web scraping operations
- `liferay_content_processor.log`: Migration operations

### Statistics Tracking
The migration system provides comprehensive statistics:
- Total items processed
- Success/failure rates
- Processing duration
- Document folders created
- Images uploaded
- Content folders created
- Structured content items created

## Error Handling

- **Graceful Degradation**: System continues processing even if individual items fail
- **Retry Logic**: Automatic retry for transient failures
- **Comprehensive Logging**: Detailed error information for troubleshooting
- **Fallback Mechanisms**: Uses fallback folders when specific folder creation fails

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check Liferay instance availability and credentials
2. **Permission Errors**: Verify user has necessary permissions in Liferay
3. **Rate Limiting**: Adjust `BATCH_DELAY` if encountering rate limits
4. **Memory Issues**: Reduce `BATCH_SIZE` for large datasets

### Debug Mode

Enable detailed logging by setting `DEV_MODE=True` in your `.env` file.

## Support

For issues and questions:
1. Check the log files for detailed error information
2. Verify environment configuration
3. Ensure Liferay instance is accessible and properly configured

## Version History

- **v1.0.0**: Initial release with professional architecture, comprehensive error handling, and full migration capabilities
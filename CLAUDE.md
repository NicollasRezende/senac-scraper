# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web scraping and content migration system for Senac DF. The project consists of two main components:

1. **Web Scraper** (`scraper.py`, `src/senac_scraper.py`) - Extracts news content from Senac DF website
2. **Content Migration System** (`content_migration_system.py`) - Migrates scraped content to Liferay DXP

## Architecture

### Core Components

- **Entry Points:**
  - `scraper.py` - Main scraper execution with batch processing
  - `content_migration_system.py` - Liferay content migration with enterprise features

- **Services Layer (`src/services/`):**
  - `scraping_service.py` - Web scraping operations
  - `url_collector_service.py` - URL collection and management
  - `liferay_client.py` - Liferay DXP API client
  - `document_service.py` - Document/image upload handling
  - `structured_content_service.py` - Structured content creation
  - `folder_service.py` - Folder management in Liferay
  - `bulk_processor.py` - Batch processing operations

- **Configuration Management:**
  - `config_manager.py` - Centralized configuration with environment variables
  - `src/config/scraping_config.py` - Scraping-specific configuration
  - `.env` - Environment variables (use `.env.example` as template)

### Data Flow

1. **URL Collection:** Collect article URLs from Senac website pagination
2. **Content Scraping:** Extract structured content from individual pages
3. **Content Migration:** Upload content and images to Liferay DXP with proper folder structure

## Common Commands

### Run Web Scraper
```bash
python3 scraper.py
```

### Run Content Migration
```bash
python3 content_migration_system.py
```

### Environment Setup
```bash
# Copy environment template and configure
cp .env.example .env
# Edit .env with your Liferay credentials and configuration
```

## Configuration

- **Scraping Config:** Modify batch sizes, delays, and worker threads in `scraper.py` or `ScrapingConfig`
- **Liferay Config:** Set credentials and endpoints in `.env` file
- **Processing:** Batch sizes and delays can be configured via environment variables

## Key Data Files

- `senac_urls.txt` - Input file containing URLs to scrape
- `noticias_final.json` - Output file with scraped content
- `*.log` - Application logs for debugging

## Development Notes

- The system uses asyncio for concurrent operations in the migration system
- Scraping uses threading for parallel requests
- All services follow dependency injection patterns
- Configuration is centralized and environment-based
- Comprehensive logging is implemented throughout
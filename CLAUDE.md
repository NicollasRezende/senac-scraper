# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web scraping and content migration system for Senac DF/MG. The project consists of three main components:

1. **Web Scraper** (`scraper.py`, `src/senac_scraper.py`) - Extracts news content from Senac DF website
2. **Content Migration System** (`content_migration_system.py`) - Migrates scraped content to Liferay DXP
3. **Document Organization System** (`dynamic_document_organizer.py`, `document_folder_migrator.py`) - Analyzes and migrates documents with automatic folder structure creation

## Architecture

### Core Components

- **Entry Points:**
  - `scraper.py` - Main scraper execution with batch processing
  - `content_migration_system.py` - Liferay content migration with enterprise features
  - `dynamic_document_organizer.py` - Document analysis and organization planning
  - `document_folder_migrator.py` - Automated document migration with folder creation

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

#### News Content Migration
1. **URL Collection:** Collect article URLs from Senac website pagination
2. **Content Scraping:** Extract structured content from individual pages
3. **Content Migration:** Upload content and images to Liferay DXP with proper folder structure

#### Document Migration
1. **Document Analysis:** Parse URLs from `senac_urls_docs.txt` to extract document patterns
2. **Dynamic Organization:** Automatically create folder hierarchy based on document types and metadata
3. **Batch Migration:** Upload documents to Liferay with proper folder structure and metadata

## Common Commands

### Setup and Dependencies
```bash
# Install required Python packages
pip install requests beautifulsoup4 cloudscraper python-dotenv asyncio aiohttp

# Copy environment template and configure
cp .env.example .env
# Edit .env with your Liferay credentials and configuration
```

### Scraping Operations
```bash
# Run web scraper for news content
python3 scraper.py

# Analyze document URLs and create organization plan
python3 dynamic_document_organizer.py
```

### Migration Operations
```bash
# Migrate scraped news content to Liferay
python3 content_migration_system.py

# Migrate documents with automatic folder creation
python3 document_folder_migrator.py

# Test mode for document migration (dry run)
python3 document_folder_migrator.py --test

# Custom batch size for document migration
python3 document_folder_migrator.py --batch-size 5
```

## Configuration

- **Scraping Config:** Modify batch sizes, delays, and worker threads in `scraper.py` or `ScrapingConfig`
- **Liferay Config:** Set credentials and endpoints in `.env` file
- **Processing:** Batch sizes and delays can be configured via environment variables

## Key Data Files

### Input Files
- `senac_urls.txt` - URLs for news content scraping
- `senac_urls_docs.txt` - URLs for document migration
- `.env` - Environment configuration (copy from `.env.example`)

### Output Files
- `noticias_final.json` - Scraped news content in JSON format
- `document_organization_analysis.json` - Document analysis and organization plan
- `*.log` - Application logs for debugging and monitoring

## Development Notes

- **Concurrency:** System uses asyncio for migration operations and threading for scraping requests
- **Architecture:** Services follow dependency injection patterns for modularity
- **Configuration:** Centralized environment-based configuration via `config_manager.py`
- **Document Organization:** Dynamic folder structure creation based on document type patterns (Resolução, Portaria, etc.)
- **Error Handling:** Comprehensive logging and retry mechanisms throughout all operations
- **Testing:** Document migration supports test mode (`--test` flag) for safe validation
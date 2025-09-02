#!/usr/bin/env python3
"""
Liferay Content Migration System

Enterprise-grade content migration solution for Liferay DXP.
Provides automated migration of news articles with document management
and structured content creation capabilities.

Features:
- Batch processing with configurable delays
- Comprehensive error handling and logging
- Development and production modes
- Statistics tracking and reporting
- Professional architecture with separation of concerns

Author: Content Migration System
Version: 1.0.0
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from config_manager import ConfigurationManager, ApplicationConfig, create_legacy_config
from src.services.liferay_client import LiferayClient
from src.services.document_service import DocumentService
from src.services.folder_service import FolderService
from src.services.structured_content_folder_service import StructuredContentFolderService
from src.services.structured_content_service import StructuredContentService


@dataclass
class MigrationResult:
    """Result container for migration operations."""
    success: bool
    message: str
    item_id: Optional[str] = None
    processing_time: Optional[float] = None
    

@dataclass
class MigrationStatistics:
    """Comprehensive statistics for migration operations."""
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    document_folders_created: int = 0
    documents_uploaded: int = 0
    content_folders_created: int = 0
    structured_contents_created: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        return (self.successful_items / self.processed_items * 100) if self.processed_items > 0 else 0.0
    
    @property
    def processing_duration(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def mark_completed(self) -> None:
        """Mark the migration as completed."""
        self.end_time = datetime.now()


class ContentMigrationSystem:
    """
    Main system for content migration operations.
    
    Orchestrates the complete migration workflow with professional
    error handling, logging, and statistics tracking.
    """
    
    def __init__(self, config: ApplicationConfig):
        self.config = config
        self.legacy_config = create_legacy_config(config)
        self.statistics = MigrationStatistics()
        self.logger = self._configure_logging()
        self._initialize_services()
    
    def _configure_logging(self) -> logging.Logger:
        """Configure professional logging system."""
        log_level = logging.DEBUG if self.config.processing.dev_mode else logging.INFO
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configure file handler
        file_handler = logging.FileHandler(self.config.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Configure console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Configure logger
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(log_level)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_services(self) -> None:
        """Initialize all required migration services."""
        self.document_service = DocumentService(self.legacy_config)
        self.folder_service = FolderService(self.legacy_config)
        self.structured_content_folder_service = StructuredContentFolderService(self.legacy_config)
        self.structured_content_service = StructuredContentService(self.legacy_config)
    
    async def execute_migration(self, news_file: str) -> MigrationStatistics:
        """
        Execute the complete content migration process.
        
        Args:
            news_file: Path to the news data JSON file
            
        Returns:
            MigrationStatistics: Complete migration statistics
        """
        self.logger.info("Content Migration System initiated")
        self.logger.info(f"Configuration: {self._get_mode_description()}")
        
        if not Path(news_file).exists():
            raise FileNotFoundError(f"News data file not found: {news_file}")
        
        news_data = self._load_news_data(news_file)
        self.statistics.total_items = len(news_data)
        
        self.logger.info(f"Loaded {len(news_data)} items for processing")
        
        async with LiferayClient(self.legacy_config) as client:
            await self._process_content_batch(client, news_data)
        
        self.statistics.mark_completed()
        self._log_final_results()
        
        return self.statistics
    
    def _load_news_data(self, news_file: str) -> List[Dict]:
        """Load and prepare news data for processing."""
        try:
            with open(news_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if self.config.processing.dev_mode:
                data = data[:self.config.processing.max_dev_items]
                self.logger.info(f"Development mode: Limited to {len(data)} items")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in news file: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Encoding error in news file: {e}")
    
    async def _process_content_batch(self, client: LiferayClient, news_data: List[Dict]) -> None:
        """Process all content items in the batch."""
        for index, news_item in enumerate(news_data, 1):
            self.statistics.processed_items += 1
            
            try:
                result = await self._process_single_content_item(
                    client, news_item, index, len(news_data)
                )
                
                if result.success:
                    self.statistics.successful_items += 1
                    self.logger.info(f"Item {index}/{len(news_data)}: SUCCESS")
                else:
                    self.statistics.failed_items += 1
                    self.logger.warning(f"Item {index}/{len(news_data)}: FAILED - {result.message}")
                
            except Exception as e:
                self.statistics.failed_items += 1
                self.logger.error(f"Item {index}/{len(news_data)}: ERROR - {str(e)}")
            
            # Apply processing delay
            if index < len(news_data):
                await asyncio.sleep(self.config.processing.batch_delay)
    
    async def _process_single_content_item(self, client: LiferayClient, 
                                         news_item: Dict, current: int, total: int) -> MigrationResult:
        """Process a single content item through the migration workflow."""
        title = news_item.get('title', 'Untitled Content')
        self.logger.debug(f"Processing: {title[:50]}...")
        
        try:
            # Step 1: Handle document folder
            doc_folder_result = await self._create_document_folder(client, news_item)
            if not doc_folder_result.success:
                return MigrationResult(False, f"Document folder creation failed: {doc_folder_result.message}")
            
            # Step 2: Handle image uploads
            upload_result = await self._upload_content_images(client, doc_folder_result.item_id, news_item)
            
            # Step 3: Handle structured content folder
            content_folder_result = await self._create_structured_content_folder(client, news_item)
            if not content_folder_result.success:
                return MigrationResult(False, f"Content folder creation failed: {content_folder_result.message}")
            
            # Step 4: Create structured content
            content_result = await self._create_structured_content(
                client, content_folder_result.item_id, news_item, upload_result
            )
            
            if content_result.success:
                return MigrationResult(True, "Content migration completed successfully", content_result.item_id)
            else:
                return MigrationResult(False, f"Content creation failed: {content_result.message}")
                
        except Exception as e:
            return MigrationResult(False, f"Migration error: {str(e)}")
    
    async def _create_document_folder(self, client: LiferayClient, news_item: Dict) -> MigrationResult:
        """Create or retrieve document folder for the content item."""
        try:
            folder_info = await self.folder_service.create_folder_for_news(
                client, news_item.get('title', 'Untitled')
            )
            
            if folder_info:
                self.statistics.document_folders_created += 1
                return MigrationResult(True, "Document folder ready", str(folder_info.id))
            else:
                # Fallback to parent folder
                fallback_id = str(self.config.content_structure.document_parent_folder_id)
                return MigrationResult(True, "Using fallback document folder", fallback_id)
                
        except Exception as e:
            fallback_id = str(self.config.content_structure.document_parent_folder_id)
            self.logger.warning(f"Document folder creation failed, using fallback: {e}")
            return MigrationResult(True, "Using fallback document folder", fallback_id)
    
    async def _upload_content_images(self, client: LiferayClient, folder_id: str, 
                                   news_item: Dict) -> Dict[str, str]:
        """Upload images for the content item."""
        uploaded_images = {}
        
        try:
            upload_results = await self.document_service.upload_images_to_folder(
                client, int(folder_id), news_item
            )
            
            for result in upload_results:
                if result and 'id' in result:
                    self.statistics.documents_uploaded += 1
                    
                    # Identify featured image
                    title = result.get('title', '').lower()
                    if 'featured' in title or 'capa' in title or not uploaded_images.get('featured'):
                        uploaded_images['featured'] = str(result['id'])
                        
        except Exception as e:
            self.logger.warning(f"Image upload failed: {e}")
        
        return uploaded_images
    
    async def _create_structured_content_folder(self, client: LiferayClient, 
                                              news_item: Dict) -> MigrationResult:
        """Create structured content folder for the content item."""
        try:
            folder_info = await self.structured_content_folder_service.create_folder_for_news(
                client, news_item.get('title', 'Untitled')
            )
            
            if folder_info:
                self.statistics.content_folders_created += 1
                return MigrationResult(True, "Structured content folder ready", str(folder_info.id))
            else:
                return MigrationResult(False, "Failed to create structured content folder")
                
        except Exception as e:
            return MigrationResult(False, f"Structured content folder error: {str(e)}")
    
    async def _create_structured_content(self, client: LiferayClient, folder_id: str,
                                       news_item: Dict, uploaded_images: Dict[str, str]) -> MigrationResult:
        """Create the structured content with all associated data."""
        try:
            # Enhance news item with uploaded image references
            enhanced_item = news_item.copy()
            if uploaded_images.get('featured'):
                enhanced_item['featured_image_id'] = int(uploaded_images['featured'])
            
            content_result = await self.structured_content_service.create_news_content(
                client, int(folder_id), enhanced_item
            )
            
            if content_result and 'id' in content_result:
                self.statistics.structured_contents_created += 1
                return MigrationResult(True, "Structured content created", str(content_result['id']))
            else:
                return MigrationResult(False, "Structured content creation returned no result")
                
        except Exception as e:
            return MigrationResult(False, f"Structured content creation error: {str(e)}")
    
    def _get_mode_description(self) -> str:
        """Get a description of the current processing mode."""
        if self.config.processing.dev_mode:
            return f"Development mode (max {self.config.processing.max_dev_items} items)"
        else:
            return "Production mode (all items)"
    
    def _log_final_results(self) -> None:
        """Log comprehensive final results."""
        self.logger.info("Migration process completed")
        self.logger.info(f"Total items: {self.statistics.total_items}")
        self.logger.info(f"Processed: {self.statistics.processed_items}")
        self.logger.info(f"Successful: {self.statistics.successful_items}")
        self.logger.info(f"Failed: {self.statistics.failed_items}")
        self.logger.info(f"Success rate: {self.statistics.success_rate:.1f}%")
        self.logger.info(f"Document folders created: {self.statistics.document_folders_created}")
        self.logger.info(f"Documents uploaded: {self.statistics.documents_uploaded}")
        self.logger.info(f"Content folders created: {self.statistics.content_folders_created}")
        self.logger.info(f"Structured contents created: {self.statistics.structured_contents_created}")
        
        if self.statistics.processing_duration:
            self.logger.info(f"Processing time: {self.statistics.processing_duration:.1f} seconds")


async def main() -> int:
    """Main application entry point."""
    try:
        # Load configuration
        config = ConfigurationManager.load_from_environment()
        
        # Initialize migration system
        migration_system = ContentMigrationSystem(config)
        
        # Execute migration
        statistics = await migration_system.execute_migration(config.news_file)
        
        # Return appropriate exit code
        return 0 if statistics.success_rate > 0 else 1
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
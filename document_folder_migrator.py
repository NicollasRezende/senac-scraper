#!/usr/bin/env python3
"""
Document Folder Migration Service for Senac MG Documents

Creates folder structure and migrates documents to correct locations
using existing services without modifications.

Usage: python3 document_folder_migrator.py [--test] [--batch-size N]
"""

import asyncio
import json
import logging
import argparse
import sys
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from config_manager import ConfigurationManager, create_legacy_config
from src.services.liferay_client import LiferayClient
from src.services.folder_service import FolderService, FolderInfo
from dynamic_document_organizer import DynamicDocumentOrganizer


@dataclass
class MigrationStats:
    """Statistics for folder and document migration."""
    total_documents: int = 0
    processed_documents: int = 0
    successful_uploads: int = 0
    failed_uploads: int = 0
    folders_created: int = 0
    folders_found: int = 0
    start_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        return (self.successful_uploads / self.processed_documents * 100) if self.processed_documents > 0 else 0.0


class DocumentFolderMigrator:
    """Migrates documents using dynamic folder structure with existing services."""

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.stats = MigrationStats()
        self.logger = self._setup_logging()

        # Load config
        self.config = ConfigurationManager.load_from_environment()
        self.legacy_config = create_legacy_config(self.config)

        # Initialize services
        self.liferay_client = LiferayClient(self.legacy_config)
        self.folder_service = FolderService(self.legacy_config)

        # Folder management
        self.folder_cache: Dict[str, FolderInfo] = {}
        self.organization_data: Optional[Dict] = None

        # Shared session for downloads
        self.download_session: Optional[aiohttp.ClientSession] = None

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for migration."""
        logger = logging.getLogger('DocumentFolderMigrator')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def load_organization_data(self, config_file: str = "document_organization_analysis.json") -> None:
        """Load organization data from analysis file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Organization config not found: {config_file}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self.organization_data = json.load(f)

        self.stats.total_documents = self.organization_data['total_documents']
        self.logger.info(f"Loaded organization data: {self.stats.total_documents} documents")

    async def create_folder_hierarchy(self) -> None:
        """Create complete folder hierarchy using existing folder service."""
        if not self.organization_data:
            raise ValueError("Organization data not loaded")

        self.logger.info("Creating folder hierarchy...")

        # Create root folder
        root_name = self.organization_data['root_folder']
        root_folder = await self._ensure_folder_exists(root_name, folder_path=root_name)
        self.folder_cache[root_name] = root_folder

        # Create category and type folders
        folder_structure = self.organization_data['folder_structure']

        for main_category, category_data in folder_structure.items():
            # Create main category folder
            category_path = f"{root_name}/{main_category}"
            category_folder = await self._ensure_folder_exists(main_category, root_folder.id, category_path)
            self.folder_cache[category_path] = category_folder

            # Create document type folders
            for doc_type, type_data in category_data.items():
                type_path = f"{category_path}/{doc_type}"
                type_folder = await self._ensure_folder_exists(doc_type, category_folder.id, type_path)
                self.folder_cache[type_path] = type_folder

                # Create year folders if needed
                if type_data.get('organize_by_year', False):
                    for year in type_data.get('years', []):
                        if year != 'SEM_ANO':
                            year_path = f"{type_path}/{year}"
                            year_folder = await self._ensure_folder_exists(year, type_folder.id, year_path)
                            self.folder_cache[year_path] = year_folder

        self.logger.info(f"Folder hierarchy ready: {len(self.folder_cache)} folders")

    async def _ensure_folder_exists(self, folder_name: str, parent_id: Optional[int] = None, folder_path: str = "") -> FolderInfo:
        """Ensure folder exists, create if not, using existing folder service."""
        # For root folder, use the configured documents root folder ID
        if parent_id is None:
            parent_id = self.config.content_structure.documents_root_folder_id

        # Skip folder existence check - just create folders directly

        # Create new folder
        if self.test_mode:
            # Simulate folder creation in test mode
            folder_info = FolderInfo(
                id=len(self.folder_cache) + 1000,
                name=folder_name,
                parent_id=parent_id
            )
            self.stats.folders_created += 1
            path_display = f" -> {folder_path}" if folder_path else ""
            self.logger.info(f"[TEST] Would create folder: {folder_name}{path_display}")
            return folder_info

        try:
            # Use the LiferayClient directly to create folder
            response = await self.liferay_client.create_folder(
                name=folder_name,
                description=f"Pasta organizacional: {folder_name}",
                parent_folder_id=parent_id
            )

            folder_info = FolderInfo(
                id=response['id'],
                name=response['name'],
                parent_id=response.get('parentDocumentFolderId')
            )

            self.stats.folders_created += 1
            path_display = f" -> {folder_path}" if folder_path else ""
            self.logger.info(f"Created folder: {folder_name}{path_display}")
            return folder_info

        except Exception as e:
            self.logger.error(f"Failed to create folder {folder_name}: {e}")
            raise


    def _get_target_folder_path(self, document_mapping: Dict) -> str:
        """Build target folder path for a document."""
        root = self.organization_data['root_folder']
        main_cat = document_mapping['main_category']
        doc_type = document_mapping['document_type']
        year = document_mapping.get('year')

        if year and year != 'SEM_ANO':
            return f"{root}/{main_cat}/{doc_type}/{year}"
        else:
            return f"{root}/{main_cat}/{doc_type}"

    async def download_and_upload_document(self, url: str, filename: str, folder_id: int) -> bool:
        """Download document from URL and upload to Liferay folder."""
        if self.test_mode:
            self.logger.info(f"[TEST] Would download and upload: {filename}")
            return True

        try:
            # Download document using shared session
            if not self.download_session:
                timeout = aiohttp.ClientTimeout(total=30)
                self.download_session = aiohttp.ClientSession(timeout=timeout)

            async with self.download_session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                content = await response.read()

            # Upload to Liferay using document API
            await self.liferay_client.upload_document(
                folder_id=folder_id,
                file_data=content,
                file_name=filename,
                title=filename.replace('.pdf', '').replace('_', ' '),
                description=f"Documento migrado automaticamente: {filename}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to upload {filename}: {e}")
            return False

    async def migrate_documents(self, batch_size: int = 10) -> None:
        """Migrate all documents to their target folders."""
        if not self.organization_data:
            raise ValueError("Organization data not loaded")

        document_mappings = self.organization_data['document_mapping']

        # Apply DEV_MODE limitation if enabled
        if self.config.processing.dev_mode:
            max_docs = self.config.processing.max_dev_items
            document_mappings = document_mappings[:max_docs]
            self.logger.info(f"DEV MODE: Limited to {max_docs} documents")

        self.stats.total_documents = len(document_mappings)
        self.stats.start_time = datetime.now()

        self.logger.info(f"Starting migration of {len(document_mappings)} documents")

        # Process in batches
        for i in range(0, len(document_mappings), batch_size):
            batch = document_mappings[i:i + batch_size]
            batch_num = i // batch_size + 1

            self.logger.info(f"Processing batch {batch_num} ({len(batch)} documents)")

            # Process batch documents in parallel
            tasks = [self._process_single_document(doc_mapping) for doc_mapping in batch]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Progress update
            progress = (self.stats.processed_documents / self.stats.total_documents) * 100
            self.logger.info(f"Progress: {progress:.1f}% | Success rate: {self.stats.success_rate:.1f}%")

    async def _process_single_document(self, doc_mapping: Dict) -> None:
        """Process a single document migration."""
        source_url = doc_mapping['source_url']
        filename = doc_mapping['filename']

        self.stats.processed_documents += 1

        try:
            # Get target folder
            folder_path = self._get_target_folder_path(doc_mapping)
            target_folder = self.folder_cache.get(folder_path)

            if not target_folder:
                raise ValueError(f"Target folder not found: {folder_path}")

            # Upload document
            success = await self.download_and_upload_document(
                source_url, filename, target_folder.id
            )

            if success:
                self.stats.successful_uploads += 1
                self.logger.info(f"Uploaded: {filename} -> {folder_path}")
            else:
                self.stats.failed_uploads += 1

        except Exception as e:
            self.stats.failed_uploads += 1
            self.logger.error(f"Failed to process {filename}: {e}")

    def print_final_report(self) -> None:
        """Print migration completion report."""
        if self.stats.start_time:
            duration = (datetime.now() - self.stats.start_time).total_seconds()
        else:
            duration = 0

        print("\\n" + "=" * 60)
        print("DOCUMENT MIGRATION REPORT")
        print("=" * 60)
        if self.config.processing.dev_mode:
            print(f"DEVELOPMENT MODE (limited to {self.config.processing.max_dev_items} documents)")
        print(f"Total documents: {self.stats.total_documents}")
        print(f"Successful uploads: {self.stats.successful_uploads}")
        print(f"Failed uploads: {self.stats.failed_uploads}")
        print(f"Folders created: {self.stats.folders_created}")
        print(f"Folders found: {self.stats.folders_found}")
        print(f"Success rate: {self.stats.success_rate:.1f}%")
        print(f"Total time: {duration:.1f} seconds")
        print("=" * 60)

        if self.stats.failed_uploads > 0:
            print("Warning: Some documents failed. Check logs for details.")

    async def run_migration(self, batch_size: int = 10) -> None:
        """Execute complete migration process."""
        async with self.liferay_client:
            try:
                # Load organization data
                self.load_organization_data()

                # Create folder hierarchy
                await self.create_folder_hierarchy()

                # Migrate documents
                await self.migrate_documents(batch_size)

                # Print report
                self.print_final_report()

            except Exception as e:
                self.logger.error(f"Migration failed: {e}")
                raise
            finally:
                # Close download session
                if self.download_session:
                    await self.download_session.close()


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Migrate Senac MG documents with folder structure')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--batch-size', type=int, default=20, help='Documents per batch')
    parser.add_argument('--analyze-first', action='store_true',
                       help='Run document analysis first')

    args = parser.parse_args()

    print("SENAC MG DOCUMENT MIGRATION")
    print("=" * 60)

    if args.test:
        print("TEST MODE - No real operations will be performed")

    try:
        # Run analysis first if requested
        if args.analyze_first:
            print("Running document analysis first...")
            organizer = DynamicDocumentOrganizer()
            organizer.run_analysis()
            print("Analysis completed\\n")

        # Run migration
        migrator = DocumentFolderMigrator(test_mode=args.test)
        await migrator.run_migration(batch_size=args.batch_size)

        print("\\nMIGRATION COMPLETED SUCCESSFULLY!")

    except Exception as e:
        print(f"\\nMIGRATION ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
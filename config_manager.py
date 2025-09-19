#!/usr/bin/env python3
"""
Configuration Manager

Centralized configuration management for the Liferay Content Processor.
Handles environment variables, validation, and configuration defaults.

Author: Content Migration System
Version: 1.0.0
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class ProcessingConfig:
    """Configuration for processing operations."""
    batch_size: int = 1
    batch_delay: float = 2.0
    max_retries: int = 3
    timeout: int = 30
    dev_mode: bool = False
    max_dev_items: int = 3


@dataclass
class LiferayConnectionConfig:
    """Configuration for Liferay connection parameters."""
    base_url: str
    site_id: int
    username: str
    password: str
    timeout: int = 30
    
    @property
    def api_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/o/headless-delivery"


@dataclass
class ContentStructureConfig:
    """Configuration for content structure and folder settings."""
    document_parent_folder_id: int
    structured_content_parent_folder_id: int
    content_structure_id: int
    documents_root_folder_id: int
    
    
@dataclass
class ApplicationConfig:
    """Main application configuration container."""
    connection: LiferayConnectionConfig
    content_structure: ContentStructureConfig
    processing: ProcessingConfig
    news_file: str = "noticias_final.json"
    log_file: str = "liferay_content_processor.log"


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigurationManager:
    """
    Manages application configuration from multiple sources.
    
    Supports:
    - Environment variables
    - .env files
    - Default values
    - Configuration validation
    """
    
    REQUIRED_ENV_VARS = [
        'LIFERAY_BASE_URL',
        'LIFERAY_SITE_ID',
        'LIFERAY_USERNAME',
        'LIFERAY_PASSWORD',
        'LIFERAY_PARENT_FOLDER_ID',
        'STRUCTURED_CONTENT_PARENT_FOLDER_ID',
        'STRUCTURED_CONTENT_STRUCTURE_ID',
        'DOCUMENTS_ROOT_FOLDER_ID'
    ]
    
    @classmethod
    def load_from_environment(cls, env_file: Optional[str] = None) -> ApplicationConfig:
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file
            
        Returns:
            ApplicationConfig: Complete application configuration
            
        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        cls._validate_required_variables()
        
        try:
            connection_config = LiferayConnectionConfig(
                base_url=os.getenv('LIFERAY_BASE_URL'),
                site_id=int(os.getenv('LIFERAY_SITE_ID')),
                username=os.getenv('LIFERAY_USERNAME'),
                password=os.getenv('LIFERAY_PASSWORD'),
                timeout=int(os.getenv('LIFERAY_TIMEOUT', '30'))
            )
            
            content_structure_config = ContentStructureConfig(
                document_parent_folder_id=int(os.getenv('LIFERAY_PARENT_FOLDER_ID')),
                structured_content_parent_folder_id=int(os.getenv('STRUCTURED_CONTENT_PARENT_FOLDER_ID')),
                content_structure_id=int(os.getenv('STRUCTURED_CONTENT_STRUCTURE_ID')),
                documents_root_folder_id=int(os.getenv('DOCUMENTS_ROOT_FOLDER_ID'))
            )
            
            processing_config = ProcessingConfig(
                batch_size=int(os.getenv('BATCH_SIZE', '1')),
                batch_delay=float(os.getenv('BATCH_DELAY', '2.0')),
                max_retries=int(os.getenv('MAX_RETRIES', '3')),
                timeout=int(os.getenv('REQUEST_TIMEOUT', '30')),
                dev_mode=os.getenv('DEV_MODE', 'True').lower() == 'true',
                max_dev_items=int(os.getenv('MAX_DEV_ITEMS', '3'))
            )
            
            return ApplicationConfig(
                connection=connection_config,
                content_structure=content_structure_config,
                processing=processing_config,
                news_file=os.getenv('NEWS_FILE', 'noticias_final.json'),
                log_file=os.getenv('LOG_FILE', 'liferay_content_processor.log')
            )
            
        except (ValueError, TypeError) as e:
            raise ConfigurationError(f"Invalid configuration value: {e}")
    
    @classmethod
    def _validate_required_variables(cls) -> None:
        """Validate that all required environment variables are present."""
        missing_vars = []
        
        for var in cls.REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
    
    @classmethod
    def get_development_config(cls) -> ApplicationConfig:
        """Get a development configuration with safe defaults."""
        config = cls.load_from_environment()
        config.processing.dev_mode = True
        config.processing.batch_size = 1
        config.processing.batch_delay = 2.0
        return config
    
    @classmethod
    def get_production_config(cls) -> ApplicationConfig:
        """Get a production configuration."""
        config = cls.load_from_environment()
        config.processing.dev_mode = False
        return config
    
    @staticmethod
    def display_configuration(config: ApplicationConfig) -> str:
        """
        Generate a human-readable configuration summary.
        
        Args:
            config: Application configuration
            
        Returns:
            str: Formatted configuration summary
        """
        summary = [
            "Liferay Content Processor Configuration",
            "=" * 45,
            f"Mode: {'Development' if config.processing.dev_mode else 'Production'}",
            f"Liferay URL: {config.connection.base_url}",
            f"Site ID: {config.connection.site_id}",
            f"Username: {config.connection.username}",
            f"News File: {config.news_file}",
            f"Batch Size: {config.processing.batch_size}",
            f"Batch Delay: {config.processing.batch_delay}s",
            f"Document Folder ID: {config.content_structure.document_parent_folder_id}",
            f"Content Parent Folder ID: {config.content_structure.structured_content_parent_folder_id}",
            f"Content Structure ID: {config.content_structure.content_structure_id}",
        ]
        
        if config.processing.dev_mode:
            summary.append(f"Max Development Items: {config.processing.max_dev_items}")
            
        return "\n".join(summary)


def create_legacy_config(app_config: ApplicationConfig):
    """
    Create a legacy LiferayConfig object for backward compatibility.
    
    Args:
        app_config: New application configuration
        
    Returns:
        LiferayConfig: Legacy configuration object
    """
    from src.config.liferay_config import LiferayConfig
    
    legacy_config = LiferayConfig(
        base_url=app_config.connection.base_url,
        username=app_config.connection.username,
        password=app_config.connection.password,
        site_id=app_config.connection.site_id,
        timeout=app_config.connection.timeout,
        parent_folder_id=app_config.content_structure.document_parent_folder_id,
        structured_content_parent_folder_id=app_config.content_structure.structured_content_parent_folder_id,
        content_structure_id=app_config.content_structure.content_structure_id
    )
    
    # Add processing configuration as attributes
    legacy_config.batch_size = app_config.processing.batch_size
    legacy_config.batch_delay = app_config.processing.batch_delay
    
    return legacy_config


if __name__ == "__main__":
    try:
        config = ConfigurationManager.load_from_environment()
        print(ConfigurationManager.display_configuration(config))
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        exit(1)
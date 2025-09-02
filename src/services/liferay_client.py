import aiohttp
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from src.config.liferay_config import LiferayConfig


logger = logging.getLogger(__name__)


class LiferayClient:
    def __init__(self, config: LiferayConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        await self.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
    
    async def create_session(self):
        auth = aiohttp.BasicAuth(self.config.username, self.config.password)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        self.session = aiohttp.ClientSession(
            auth=auth,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    try:
                        error_text = await response.text()
                        logger.error(f"HTTP {response.status} error response: {error_text}")
                    except:
                        logger.error(f"HTTP {response.status} error (no response body)")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    async def get_folders(self) -> Dict[str, Any]:
        return await self._make_request('GET', self.config.folders_endpoint)
    
    async def create_folder(self, name: str, description: str = "", 
                          parent_folder_id: Optional[int] = None) -> Dict[str, Any]:
        data = {
            "name": name,
            "description": description,
            "viewableBy": "Anyone"
        }
        
        if parent_folder_id:
            data["parentDocumentFolderId"] = parent_folder_id
            url = self.config.subfolder_endpoint(parent_folder_id)
        else:
            url = self.config.folders_endpoint
        
        return await self._make_request('POST', url, json=data)
    
    async def get_folder_documents(self, folder_id: int) -> Dict[str, Any]:
        url = self.config.documents_endpoint(folder_id)
        return await self._make_request('GET', url)
    
    async def upload_document(self, folder_id: int, file_data: bytes, 
                            file_name: str, title: str = None, 
                            description: str = "") -> Dict[str, Any]:
        url = self.config.documents_endpoint(folder_id)
        
        if not title:
            title = file_name
            
        document_metadata = {
            "title": title,
            "description": description,
            "viewableBy": "Anyone"
        }
        
        data = aiohttp.FormData()
        data.add_field('file', file_data, filename=file_name)
        data.add_field('document', 
                      json.dumps(document_metadata),
                      content_type='application/json')
        
        return await self._upload_request('POST', url, data=data)
    
    async def _upload_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            headers = {}
            
            async with aiohttp.ClientSession(auth=auth) as upload_session:
                async with upload_session.request(method, url, headers=headers, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Upload request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            raise
    
    # Generic HTTP methods for structured content API
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Generic GET request to Liferay API"""
        url = f"{self.config.base_url}/o/headless-delivery/v1.0/sites/{self.config.site_id}/{endpoint}"
        return await self._make_request('GET', url)
    
    async def get_structured_content_folders_by_parent(self, parent_folder_id: int) -> Dict[str, Any]:
        """Get structured content folders by parent ID - uses direct endpoint without site ID"""
        url = f"{self.config.base_url}/o/headless-delivery/v1.0/structured-content-folders/{parent_folder_id}/structured-content-folders"
        return await self._make_request('GET', url)
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic POST request to Liferay API"""
        url = f"{self.config.base_url}/o/headless-delivery/v1.0/sites/{self.config.site_id}/{endpoint}"
        return await self._make_request('POST', url, json=data)
    
    async def post_structured_content_folder_to_parent(self, parent_folder_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured content folder inside parent folder - uses direct endpoint without site ID"""
        url = f"{self.config.base_url}/o/headless-delivery/v1.0/structured-content-folders/{parent_folder_id}/structured-content-folders"
        return await self._make_request('POST', url, json=data)
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic PUT request to Liferay API"""
        url = f"{self.config.base_url}/o/headless-delivery/v1.0/sites/{self.config.site_id}/{endpoint}"
        return await self._make_request('PUT', url, json=data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Generic DELETE request to Liferay API"""
        url = f"{self.config.base_url}/o/headless-delivery/v1.0/sites/{self.config.site_id}/{endpoint}"
        return await self._make_request('DELETE', url)
    
    async def post_to_folder(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request to folder endpoint (without site ID)"""
        url = f"{self.config.base_url}/o/headless-delivery/v1.0/{endpoint}"
        return await self._make_request('POST', url, json=data)
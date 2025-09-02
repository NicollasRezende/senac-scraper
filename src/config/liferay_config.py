from dataclasses import dataclass


@dataclass
class LiferayConfig:
    base_url: str
    site_id: str
    username: str
    password: str
    timeout: int = 30
    # Document Library folders (para upload de imagens/documentos)
    parent_folder_id: int = None
    # Structured Content folders (para conteúdo estruturado)
    structured_content_parent_folder_id: int = None
    # ID da estrutura de conteúdo "Notícia"
    content_structure_id: int = None
    
    @property
    def api_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/o/headless-delivery"
    
    @property
    def folders_endpoint(self) -> str:
        return f"{self.api_url}/v1.0/sites/{self.site_id}/document-folders"
    
    def subfolder_endpoint(self, parent_folder_id: int) -> str:
        return f"{self.api_url}/v1.0/document-folders/{parent_folder_id}/document-folders"
    
    def documents_endpoint(self, folder_id: int) -> str:
        return f"{self.api_url}/v1.0/document-folders/{folder_id}/documents"
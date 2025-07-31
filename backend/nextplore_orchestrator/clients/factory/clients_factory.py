from dataclasses import dataclass, field

from config import settings
from clients.embedding import EmbeddingClient
from clients.integration import IntegrationClient
from clients.vector import VectorClient
from clients.ai_orm_context import AIORMContextClient


@dataclass
class ClientsFactory:
    integration_base_url: str =field(default=settings.integration_base_url)
    embedding_base_url: str = field(default=settings.embedding_base_url)
    vector_base_url: str = field(default=settings.vector_base_url)
    ai_orm_context_base_url: str = field(default=settings.ai_orm_context_base_url)

    def create_integration_client(self) -> IntegrationClient:
        return IntegrationClient(self.integration_base_url)
    
    def create_embedding_client(self) -> EmbeddingClient:
        return EmbeddingClient(self.embedding_base_url)
    
    def create_vector_client(self) -> VectorClient:
        return VectorClient(self.vector_base_url)
    
    def create_ai_orm_context_client(self) -> AIORMContextClient:
        return AIORMContextClient(self.ai_orm_context_base_url)

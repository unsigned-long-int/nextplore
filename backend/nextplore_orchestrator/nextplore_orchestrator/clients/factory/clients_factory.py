from dataclasses import dataclass, field

from nextplore_orchestrator.settings import settings
from nextplore_orchestrator.clients.embedding import EmbeddingClient
from nextplore_orchestrator.clients.integration import IntegrationClient
from nextplore_orchestrator.clients.vector import VectorClient
from nextplore_orchestrator.clients.ai_orm_context import AIORMContextClient


@dataclass
class ClientsFactory:
    integration_base_url: str = field(default=settings.integration_base_url)
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

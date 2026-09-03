from dataclasses import dataclass, field

from nextplore_orchestrator.clients.embedding import EmbeddingClient
from nextplore_orchestrator.clients.integration import IntegrationClient
from nextplore_orchestrator.clients.llm_inference import LlmInferenceClient
from nextplore_orchestrator.clients.vector import VectorClient
from nextplore_orchestrator.settings import settings


@dataclass
class ClientsFactory:
    integration_base_url: str = field(default=settings.integration_base_url)
    embedding_base_url: str = field(default=settings.embedding_base_url)
    vector_base_url: str = field(default=settings.vector_base_url)
    llm_inference_base_url: str = field(default=settings.llm_inference_base_url)

    def create_integration_client(self) -> IntegrationClient:
        return IntegrationClient(self.integration_base_url)

    def create_embedding_client(self) -> EmbeddingClient:
        return EmbeddingClient(self.embedding_base_url)

    def create_vector_client(self) -> VectorClient:
        return VectorClient(self.vector_base_url)

    def create_llm_inference_client(self) -> LlmInferenceClient:
        return LlmInferenceClient(self.llm_inference_base_url)

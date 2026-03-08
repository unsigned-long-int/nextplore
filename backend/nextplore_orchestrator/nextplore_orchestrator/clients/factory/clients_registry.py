from dataclasses import dataclass

from nextplore_orchestrator.clients.embedding import EmbeddingClient
from nextplore_orchestrator.clients.integration import IntegrationClient
from nextplore_orchestrator.clients.vector import VectorClient
from nextplore_orchestrator.clients.llm_inference import LlmInferenceClient


@dataclass
class ClientsRegistry:
    integration_client: IntegrationClient
    embedding_client: EmbeddingClient
    vector_client: VectorClient
    llm_inference_client: LlmInferenceClient

    async def close_clients(self) -> None:
        await self.integration_client.close()
        await self.embedding_client.close()
        await self.vector_client.close()
        await self.llm_inference_client.close()

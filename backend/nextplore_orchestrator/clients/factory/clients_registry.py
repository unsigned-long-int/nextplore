from dataclasses import dataclass

from clients.embedding import EmbeddingClient
from clients.integration import IntegrationClient
from clients.vector import VectorClient
from clients.ai_orm_context import AIORMContextClient


@dataclass
class ClientsRegistry:
    integration_client: IntegrationClient
    embedding_client: EmbeddingClient
    vector_client: VectorClient
    ai_orm_context_client: AIORMContextClient

    async def close_clients(self) -> None:
        await self.integration_client.close()
        await self.embedding_client.close()
        await self.vector_client.close()
        await self.ai_orm_context_client.close()

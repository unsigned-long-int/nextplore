from typing import Optional
from dataclasses import dataclass

from clients import (
    IntegrationClient,
    EmbeddingClient,
    VectorClient
)


@dataclass
class ClientsRegistry:
    integration_client: IntegrationClient
    embedding_client: EmbeddingClient
    vector_client: VectorClient

    async def close_clients(self) -> None:
        await self.integration_client.close()
        await self.embedding_client.close()
        await self.vector_client.close()

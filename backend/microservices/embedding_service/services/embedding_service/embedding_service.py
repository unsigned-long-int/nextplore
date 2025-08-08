from typing import List

from services.embedder_factory import dispatch_embedder


async def embed(datastream: str) -> List[float]:
    embedder_cls = dispatch_embedder()
    embedder = embedder_cls()
    embedding = await embedder.generate_embedding(datastream)
    return embedding

from typing import List

from services.embedder_factory import dispatch_embedder


async def embed(datastream: str, is_query: bool = True) -> List[float]:
    embedder_cls = dispatch_embedder()
    embedder = embedder_cls()
    return await embedder.generate_embedding(datastream, is_query=is_query)

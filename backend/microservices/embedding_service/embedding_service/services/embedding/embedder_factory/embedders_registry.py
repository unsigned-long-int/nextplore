from embedding_service.services.embedding.embedders import EmbedderBase, OpenAIEmbedder

EMBEDDERS_REGISTRY: dict[str, type[EmbedderBase]] = {"open_ai": OpenAIEmbedder}

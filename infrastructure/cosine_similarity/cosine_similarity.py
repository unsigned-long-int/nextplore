from scipy import spatial
from typing import List


def cosine_similarity(query_embedding: List[float], knowledge_embedding: List[float]) -> float:
    return 1 - spatial.distance.cosine(query_embedding, knowledge_embedding)

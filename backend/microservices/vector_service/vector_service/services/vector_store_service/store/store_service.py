import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from qdrant_client.http.models import FieldCondition

from vector_service.api.context import UserIdentity
from vector_service.domain.models import SemanticCacheMeta, SemanticMatch
from vector_service.services.vector_store_service.clients import VectorStoreClient
from vector_service.services.vector_store_service.exceptions import (
    DeleteVectorDBFailed,
    SearchVectorDBFailed,
    UpsertVectorDBFailed,
)
from vector_service.services.vector_store_service.models import Vector, VectorPoint

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self, client: VectorStoreClient) -> None:
        self.client = client

    async def delete_vectors(
        self,
        vector_ids: list[str],
        user_id: str,
        organization_id: str,
        collection: str = "nextplore",
    ) -> None:
        try:
            await self.client.delete_vectors(
                vector_ids=vector_ids,
                user_id=user_id,
                organization_id=organization_id,
                collection=collection,
            )
        except DeleteVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Delete vectors via {self.client.__class__.__name__} failed: {e}"
            logger.error(msg, exc_info=True)
            raise DeleteVectorDBFailed(msg)

    async def lookup_semantic_cache(
        self,
        user_identity: UserIdentity,
        embedding: list[float],
        refine_filters: list[FieldCondition] | None = None,
        score_threshold: float = 0.92,
        top_k: int = 1,
        collection: str = "nextplore-cache",
    ) -> SemanticMatch | None:
        try:
            hits = await self.client.search_nearest_vectors(
                user_identity=user_identity,
                embedding=embedding,
                top_k=top_k,
                collection=collection,
                score_threshold=score_threshold,
                refine_filters=refine_filters,
            )
            logger.info("Store hits: %s", hits.points)

            if not hits.points:
                return None

            best = hits.points[0]
            logger.info(
                "Semantic cache best hit: score=%.4f payload=%s",
                best.score,
                best.payload,
            )

            expires_at_raw = best.payload.get("expires_at")
            logger.info(
                "Semantic cache expires_at raw: %r (type=%s)",
                expires_at_raw,
                type(expires_at_raw).__name__,
            )
            if expires_at_raw:
                expires_at = datetime.fromisoformat(expires_at_raw)
                if datetime.now(timezone.utc) < expires_at:
                    return SemanticMatch(json_payload=best.payload["json_payload"])
            return None
        except SearchVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Search semantic cache match via {self.client.__class__.__name__} failed: {e}"
            logger.error(msg, exc_info=True)
            raise SearchVectorDBFailed(msg)

    async def store_semantic_cache_entry(
        self,
        user_identity: UserIdentity,
        semantic_cache_meta: SemanticCacheMeta,
        collection: str = "nextplore-cache",
    ) -> None:
        vector_point = VectorPoint(
            id=uuid4(),
            user_id=user_identity.user_id,
            organization_id=user_identity.organization_id,
            vector=semantic_cache_meta.embedding,
            extra=semantic_cache_meta.extra,
        )
        try:
            await self.client.upsert_vectors(
                vector_points=[vector_point],
                collection=collection,
            )
        except UpsertVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Upsert semantic fetch via {self.client.__class__.__name__} failed: {e}"
            logger.error(msg, exc_info=True)
            raise UpsertVectorDBFailed(msg)

    async def search_nearest_vectors(
        self,
        user_identity: UserIdentity,
        embedding: list[float],
        top_k: int = 5,
        collection: str = "nextplore",
    ) -> list[Vector]:
        try:
            hits = await self.client.search_nearest_vectors(
                user_identity=user_identity,
                embedding=embedding,
                top_k=top_k,
                collection=collection,
            )

            if not hits.points:
                return []

            return [
                Vector(id=UUID(chunk_id), score=hit.score)
                for hit in hits.points
                if (chunk_id := hit.payload.get("qdrant_vector_id")) is not None
            ]
        except SearchVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Search vectors via {self.client.__class__.__name__} failed: {e}"
            logger.error(msg, exc_info=True)
            raise SearchVectorDBFailed(msg)

    async def upsert_vectors(
        self,
        vector_points: list[VectorPoint],
        collection: str = "nextplore",
    ) -> None:
        try:
            await self.client.upsert_vectors(
                vector_points=vector_points,
                collection=collection,
            )
        except UpsertVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Upsert vectors via {self.client.__class__.__name__} failed: {e}"
            logger.error(msg, exc_info=True)
            raise UpsertVectorDBFailed(msg)

    async def aclose(self) -> None:
        try:
            await self.client.aclose()
        except Exception:
            logger.debug("VectorStoreService close ignored", exc_info=True)

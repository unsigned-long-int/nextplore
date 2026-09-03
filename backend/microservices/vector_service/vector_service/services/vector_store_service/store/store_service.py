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


def _to_vector(hit) -> Vector | None:
    payload = hit.payload or {}
    raw_id = payload.get("qdrant_vector_id")
    if raw_id is None:
        return None
    try:
        return Vector(id=UUID(str(raw_id)), score=hit.score)
    except (TypeError, ValueError):
        logger.warning(
            "Skipping point with unparseable qdrant_vector_id",
            extra={"raw_id": raw_id},
        )
        return None


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
        if not vector_ids:
            logger.debug(
                "Delete skipped: no vector ids supplied",
                extra={"org_id": organization_id, "user_id": user_id},
            )
            return
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
            logger.exception(msg)
            raise DeleteVectorDBFailed(msg) from e

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
            logger.debug("Store hits: %s", hits.points)

            if not hits.points:
                return None

            best = hits.points[0]
            logger.debug(
                "Semantic cache best hit: score=%.4f payload=%s",
                best.score,
                best.payload,
            )

            expires_at_raw = best.payload.get("expires_at")
            if not expires_at_raw:
                return None
            try:
                expires_at = datetime.fromisoformat(expires_at_raw)
            except (TypeError, ValueError):
                logger.debug("Cache entry has unparseable expires_at; treating as miss")
                return None
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) >= expires_at:
                return None

            payload = best.payload.get("json_payload")
            if payload is None:
                return None

            return SemanticMatch(json_payload=payload)
        except SearchVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Search semantic cache match via {self.client.__class__.__name__} failed: {e}"
            logger.exception(msg)
            raise SearchVectorDBFailed(msg) from e

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
            logger.exception(msg)
            raise UpsertVectorDBFailed(msg) from e

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
                vector for hit in hits.points if (vector := _to_vector(hit)) is not None
            ]
        except SearchVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Search vectors via {self.client.__class__.__name__} failed: {e}"
            logger.exception(msg)
            raise SearchVectorDBFailed(msg) from e

    async def upsert_vectors(
        self,
        vector_points: list[VectorPoint],
        collection: str = "nextplore",
    ) -> None:
        if not vector_points:
            logger.debug("Upsert skipped: no vector points supplied")
            return
        try:
            await self.client.upsert_vectors(
                vector_points=vector_points,
                collection=collection,
            )
        except UpsertVectorDBFailed:
            raise
        except Exception as e:
            msg = f"Upsert vectors via {self.client.__class__.__name__} failed: {e}"
            logger.exception(msg)
            raise UpsertVectorDBFailed(msg) from e

    async def aclose(self) -> None:
        try:
            await self.client.aclose()
        except Exception:
            logger.debug("VectorStoreService close ignored", exc_info=True)

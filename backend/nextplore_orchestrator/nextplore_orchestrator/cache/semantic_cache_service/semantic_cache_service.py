import logging
from datetime import datetime, timedelta, timezone

from svc_nextplore_orchestrator_contracts.models import AIQueryRequest, AIQueryResponse
from svc_vector_contracts.models import SemanticCacheEntry, SemanticCacheLookupQuery

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.clients.vector import VectorClient
from nextplore_orchestrator.clients.vector.exceptions import (
    VectorGetSemanticMatchRemoteError,
    VectorUpsertSemanticMatchRemoteError,
)
from nextplore_orchestrator.domain.models import CacheLookupResult

logger = logging.getLogger(__name__)

DEFAULT_TTL = 3600


class SemanticCacheService:
    def __init__(self, vector_client: VectorClient) -> None:
        self._vector_client = vector_client

    async def lookup_semantic_cache(
        self,
        ai_query: AIQueryRequest,
        embedding: list[float],
        user_identity: UserIdentity,
    ) -> CacheLookupResult | None:
        try:
            response = await self._vector_client.lookup_semantic_cache(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                payload=SemanticCacheLookupQuery(
                    embedding=embedding,
                    provider=ai_query.provider,
                    model_id=ai_query.model_id,
                    model_ref_id=ai_query.model_ref_id,
                ),
            )

            if not response.hit:
                logger.info(f"Semantic cache MISS {ai_query.prompt}")
                return None

            cached = CacheLookupResult(
                embedding=embedding,
                json_payload=response.json_payload,
            )
            logger.info(f"Semantic cache HIT {ai_query.prompt}")
            return cached
        except VectorGetSemanticMatchRemoteError as e:
            logger.error(
                f"Semantic cache VECTOR STORE ERROR {ai_query.prompt}: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                f"Semantic cache ERROR lookup({ai_query.prompt}): {e}", exc_info=True
            )
            return None

    async def store_semantic_cache_entry(
        self,
        embedding: list[float],
        request: AIQueryRequest,
        response: AIQueryResponse,
        user_identity: UserIdentity,
        ttl: int = DEFAULT_TTL,
    ) -> None:
        now = datetime.now(timezone.utc)
        try:
            await self._vector_client.store_semantic_cache_entry(
                organization_id=user_identity.organization_id,
                user_id=user_identity.user_id,
                payload=SemanticCacheEntry(
                    embedding=embedding,
                    json_payload=response.model_dump(),
                    expires_at=now + timedelta(seconds=ttl),
                    provider=request.provider,
                    model_id=request.model_id,
                    model_ref_id=request.model_ref_id,
                ),
            )
            logger.info(f"Semantic cache SET {request.prompt}")
        except VectorUpsertSemanticMatchRemoteError as e:
            logger.error(
                f"Semantic cache VECTOR STORE ERROR {request.prompt}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Semantic cache ERROR store({request.prompt}): {e}", exc_info=True
            )

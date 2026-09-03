import logging

from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
    PointStruct,
    QueryResponse,
)

from vector_service.api.context import UserIdentity
from vector_service.services.vector_store_service.exceptions import (
    DeleteVectorDBFailed,
    SearchVectorDBFailed,
    UpsertVectorDBFailed,
)
from vector_service.services.vector_store_service.models import VectorPoint

logger = logging.getLogger(__name__)


class QDrantStoreClient:
    def __init__(self, cluster_host: str, api_key: str) -> None:
        self._client = AsyncQdrantClient(url=cluster_host, api_key=api_key)

    async def search_nearest_vectors(
        self,
        user_identity: UserIdentity,
        embedding: list[float],
        top_k: int = 5,
        collection: str = "nextplore",
        refine_filters: list[FieldCondition] | None = None,
        score_threshold: float | None = None,
    ) -> QueryResponse:
        try:
            qd_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=str(user_identity.user_id)),
                    ),
                    FieldCondition(
                        key="organization_id",
                        match=MatchValue(value=str(user_identity.organization_id)),
                    ),
                    *(refine_filters or []),
                ]
            )
            return await self._client.query_points(
                collection_name=collection,
                query=embedding,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
                query_filter=qd_filter,
                score_threshold=score_threshold,
            )
        except ResponseHandlingException as e:
            msg = f"QDrant response handling failed: {e}"
            logger.error(msg, exc_info=True)
            raise SearchVectorDBFailed(msg) from e
        except UnexpectedResponse as e:
            msg = f"QDrant unexpected response failed with status code {e.status_code}"
            logger.error(msg, exc_info=True)
            raise SearchVectorDBFailed(msg) from e
        except Exception as e:
            msg = f"QDrant search failed with unexpected exception: {e}"
            logger.error(msg, exc_info=True)
            raise SearchVectorDBFailed(msg) from e

    async def delete_vectors(
        self,
        vector_ids: list[str],
        user_id: str,
        organization_id: str,
        collection: str = "nextplore",
    ) -> None:
        try:
            conditions = [
                FieldCondition(key="qdrant_vector_id", match=MatchAny(any=vector_ids)),
                FieldCondition(
                    key="organization_id", match=MatchValue(value=organization_id)
                ),
                FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            ]

            qd_filter = Filter(must=conditions)

            await self._client.delete(
                collection_name=collection,
                points_selector=FilterSelector(filter=qd_filter),
            )
        except Exception as e:
            msg = f"QDrant delete failed with unexpected exception: {e}"
            logger.error(msg, exc_info=True)
            raise DeleteVectorDBFailed(msg) from e

    async def upsert_vectors(
        self, vector_points: list[VectorPoint], collection: str = "nextplore"
    ) -> None:
        try:
            points = [
                PointStruct(
                    id=str(point.id),
                    vector=point.vector,
                    payload={
                        "qdrant_vector_id": str(point.id),
                        "user_id": str(point.user_id),
                        "organization_id": str(point.organization_id),
                        **point.extra,
                    },
                )
                for point in vector_points
            ]
            await self._client.upsert(collection_name=collection, points=points)
        except Exception as e:
            msg = f"QDrant upsert failed with unexpected exception: {e}"
            logger.error(msg, exc_info=True)
            raise UpsertVectorDBFailed(msg) from e

    async def aclose(self) -> None:
        try:
            await self._client.close()
        except Exception:
            logger.debug("Qdrant client close ignored", exc_info=True)

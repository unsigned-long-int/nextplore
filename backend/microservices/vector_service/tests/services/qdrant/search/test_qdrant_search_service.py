# tests/services/qdrant/search/test_qdrant_search_service.py
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from services.qdrant.search.qdrant_search_service import search_nearest_vectors


class FakeMatchValue:
    def __init__(self, value: str):
        self.value = value

class FakeFieldCondition:
    def __init__(self, key: str, match):
        self.key = key
        self.match = match

class FakeFilter:
    def __init__(self, must):
        self.must = must


class TestQdrantSearch(unittest.IsolatedAsyncioTestCase):
    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'http://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.search.qdrant_search_service.AsyncQdrantClient')
    @patch('services.qdrant.search.qdrant_search_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.search.qdrant_search_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.search.qdrant_search_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    async def test_happy_path_builds_filter_calls_search_and_parses_hits(
        self, mock_match_value, mock_field_cond, mock_filter, mock_qdrant_client
    ):
        user_id = uuid.uuid4()
        org_id = uuid.uuid4()
        identity = SimpleNamespace(user_id=user_id, organization_id=org_id)
        embedding = [0.1, 0.2, 0.3]

        client = MagicMock()
        client.search = AsyncMock(return_value=[
            SimpleNamespace(payload={'qdrant_vector_id': str(uuid.uuid4())}),
            SimpleNamespace(payload={'qdrant_vector_id': str(uuid.uuid4())}),
        ])
        mock_qdrant_client.return_value = client

        out = await search_nearest_vectors(identity, embedding)

        mock_qdrant_client.assert_called_once_with(url='http://qdrant.local', api_key='sekret')

        client.search.assert_awaited_once()
        _, kwargs = client.search.call_args
        assert kwargs['collection_name'] == 'nextplore'
        assert kwargs['query_vector'] == embedding
        assert kwargs['limit'] == 5
        assert kwargs['with_payload'] is True
        assert kwargs['with_vectors'] is False

        qf = kwargs['query_filter']
        assert isinstance(qf, FakeFilter)
        assert len(qf.must) == 2
        conds = {c.key: c for c in qf.must}
        assert set(conds.keys()) == {'user_id', 'organization_id'}
        assert conds['user_id'].match.value == str(user_id)
        assert conds['organization_id'].match.value == str(org_id)

        assert all(isinstance(x, uuid.UUID) for x in out)
        assert len(out) == 2

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'http://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.search.qdrant_search_service.AsyncQdrantClient')
    @patch('services.qdrant.search.qdrant_search_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.search.qdrant_search_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.search.qdrant_search_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    async def test_no_hits_returns_empty(self, mock_match_value, mock_field_cond, mock_filter, mock_qdrant_client):
        identity = SimpleNamespace(user_id=uuid.uuid4(), organization_id=uuid.uuid4())
        embedding = [0.9, 0.8]

        client = MagicMock()
        client.search = AsyncMock(return_value=[])
        mock_qdrant_client.return_value = client

        out = await search_nearest_vectors(identity, embedding)
        assert out == []

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'http://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.search.qdrant_search_service.AsyncQdrantClient')
    @patch('services.qdrant.search.qdrant_search_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.search.qdrant_search_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.search.qdrant_search_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    async def test_none_hits_returns_empty(self, mock_match_value, mock_field_cond, mock_filter, mock_qdrant_client):
        identity = SimpleNamespace(user_id=uuid.uuid4(), organization_id=uuid.uuid4())
        embedding = [0.5]

        client = MagicMock()
        client.search = AsyncMock(return_value=None)
        mock_qdrant_client.return_value = client

        out = await search_nearest_vectors(identity, embedding)
        assert out == []

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'http://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.search.qdrant_search_service.AsyncQdrantClient')
    @patch('services.qdrant.search.qdrant_search_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.search.qdrant_search_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.search.qdrant_search_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    async def test_custom_top_k_is_passed_to_search(self, mock_match_value, mock_field_cond, mock_filter, mock_qdrant_client):
        identity = SimpleNamespace(user_id=uuid.uuid4(), organization_id=uuid.uuid4())
        embedding = [0.1, 0.2]

        client = MagicMock()
        client.search = AsyncMock(return_value=[])
        mock_qdrant_client.return_value = client

        await search_nearest_vectors(identity, embedding, top_k=10)
        _, kwargs = client.search.call_args
        assert kwargs['limit'] == 10

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'http://qdrant.local', 'QDRANT_API_KEY': 'sekret'})
    @patch('services.qdrant.search.qdrant_search_service.AsyncQdrantClient')
    @patch('services.qdrant.search.qdrant_search_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.search.qdrant_search_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.search.qdrant_search_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    async def test_client_exception_propagates(self, mock_match_value, mock_field_cond, mock_filter, mock_qdrant_client):
        identity = SimpleNamespace(user_id=uuid.uuid4(), organization_id=uuid.uuid4())
        embedding = [0.3]

        client = MagicMock()
        client.search = AsyncMock(side_effect=RuntimeError('qdrant down'))
        mock_qdrant_client.return_value = client

        with self.assertRaises(RuntimeError):
            await search_nearest_vectors(identity, embedding)
        client.search.assert_awaited_once()


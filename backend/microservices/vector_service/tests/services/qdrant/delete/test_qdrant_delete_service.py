import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from  services.qdrant.delete.qdrant_delete_service import delete_qdrant_vectors


class FakeMatchAny:
    def __init__(self, any: List[str]):
        self.any = any


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


class FakeFilterSelector:
    def __init__(self, filter):
        self.filter = filter


class TestDeleteQdrantVectors(unittest.IsolatedAsyncioTestCase):
    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'https://qdrant.local', 'QDRANT_API_KEY': 'secret'})
    @patch('services.qdrant.delete.qdrant_delete_service.AsyncQdrantClient')
    @patch('services.qdrant.delete.qdrant_delete_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.MatchAny', side_effect=lambda **kw: FakeMatchAny(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.FilterSelector', side_effect=lambda **kw: FakeFilterSelector(**kw))
    async def test_happy_path_builds_filter_and_calls_delete(
        self,
        mock_filter_selector,
        mock_match_any,
        mock_match_value,
        mock_field_condition,
        mock_filter,
        mock_qdrant_client,
    ):
        client_instance = MagicMock(name='AsyncQdrantClientInstance')
        client_instance.delete = AsyncMock()
        mock_qdrant_client.return_value = client_instance

        vector_ids = ['v1', 'v2', 'v3']
        user_id = 'user-123'
        org_id = 'org-456'

        await delete_qdrant_vectors(qdrant_vector_ids=vector_ids, user_id=user_id, organization_id=org_id)

        mock_qdrant_client.assert_called_once_with(
            url='https://qdrant.local', api_key='secret'
        )

        client_instance.delete.assert_awaited_once()
        _, kwargs = client_instance.delete.call_args
        self.assertEqual(kwargs['collection_name'], 'nextplore')

        selector = kwargs['points_selector']
        self.assertIsInstance(selector, FakeFilterSelector)
        filt = selector.filter
        self.assertIsInstance(filt, FakeFilter)

        self.assertEqual(len(filt.must), 3)

        conds = {c.key: c for c in filt.must}
        self.assertCountEqual(list(conds.keys()), ['qdrant_vector_id', 'organization_id', 'user_id'])

        self.assertIsInstance(conds['qdrant_vector_id'].match, FakeMatchAny)
        self.assertEqual(conds['qdrant_vector_id'].match.any, vector_ids)

        self.assertIsInstance(conds['organization_id'].match, FakeMatchValue)
        self.assertEqual(conds['organization_id'].match.value, org_id)

        self.assertIsInstance(conds['user_id'].match, FakeMatchValue)
        self.assertEqual(conds['user_id'].match.value, user_id)

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'http://qdrant.local', 'QDRANT_API_KEY': 'secret'})
    @patch('services.qdrant.delete.qdrant_delete_service.AsyncQdrantClient')
    @patch('services.qdrant.delete.qdrant_delete_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.MatchAny', side_effect=lambda **kw: FakeMatchAny(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.FilterSelector', side_effect=lambda **kw: FakeFilterSelector(**kw))
    async def test_empty_vector_ids_still_calls_delete_with_empty_any(
        self,
        mock_filter_selector,
        mock_match_any,
        mock_match_value,
        mock_field_condition,
        mock_filter,
        mock_qdrant_client,
    ):
        client_instance = MagicMock()
        client_instance.delete = AsyncMock()
        mock_qdrant_client.return_value = client_instance

        await delete_qdrant_vectors(qdrant_vector_ids=[], user_id='u', organization_id='o')

        client_instance.delete.assert_awaited_once()
        _, kwargs = client_instance.delete.call_args
        selector = kwargs['points_selector']
        conds = {c.key: c for c in selector.filter.must}
        self.assertEqual(conds['qdrant_vector_id'].match.any, [])

    @patch.dict('os.environ', {'QDRANT_CLUSTER_HOST': 'https://qdrant.local', 'QDRANT_API_KEY': 'secret'})
    @patch('services.qdrant.delete.qdrant_delete_service.AsyncQdrantClient')
    @patch('services.qdrant.delete.qdrant_delete_service.Filter', side_effect=lambda **kw: FakeFilter(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.FieldCondition', side_effect=lambda **kw: FakeFieldCondition(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.MatchValue', side_effect=lambda **kw: FakeMatchValue(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.MatchAny', side_effect=lambda **kw: FakeMatchAny(**kw))
    @patch('services.qdrant.delete.qdrant_delete_service.FilterSelector', side_effect=lambda **kw: FakeFilterSelector(**kw))
    async def test_exceptions_from_client_delete_propagate(
        self,
        mock_filter_selector,
        mock_match_any,
        mock_match_value,
        mock_field_condition,
        mock_filter,
        mock_qdrant_client,
    ):
        client_instance = MagicMock()
        boom = RuntimeError('qdrant down')
        client_instance.delete = AsyncMock(side_effect=boom)
        mock_qdrant_client.return_value = client_instance

        with self.assertRaises(RuntimeError) as ctx:
            await delete_qdrant_vectors(qdrant_vector_ids=['id'], user_id='u', organization_id='o')
        self.assertIs(ctx.exception, boom)

        mock_qdrant_client.assert_called_once()
        client_instance.delete.assert_awaited_once()

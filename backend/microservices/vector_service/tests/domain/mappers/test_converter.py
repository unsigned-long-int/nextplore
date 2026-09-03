import json
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from qdrant_client.http.models import FieldCondition, MatchValue
from svc_vector_contracts.models import SemanticCacheEntry, SemanticCacheLookupQuery

from vector_service.domain.mappers import (
    orm_to_domain_vector_profile,
    refine_filters_from_dto,
    semantic_cache_meta_from_dto,
)
from vector_service.domain.models import SemanticCacheMeta, VectorProfile


def make_vector_orm(table_meta: str, **overrides):
    orm = MagicMock()
    orm.datastore_id = overrides.get("datastore_id", uuid4())
    orm.schema_name = overrides.get("schema_name", "public")
    orm.table_name = overrides.get("table_name", "orders")
    orm.table_meta = table_meta
    return orm


class TestOrmToDomainVectorProfile(unittest.TestCase):
    def test_maps_all_fields(self):
        datastore_id = uuid4()
        meta = {
            "datastore_id": str(datastore_id),
            "schema_name": "public",
            "table_name": "orders",
            "column_names": ["id", "total", "created_at"],
        }
        orm = make_vector_orm(
            json.dumps(meta),
            datastore_id=datastore_id,
            schema_name="public",
            table_name="orders",
        )

        result = orm_to_domain_vector_profile(orm)

        self.assertIsInstance(result, VectorProfile)
        self.assertEqual(result.datastore_id, datastore_id)
        self.assertEqual(result.schema_name, "public")
        self.assertEqual(result.table_name, "orders")
        self.assertEqual(result.table_meta, meta)

    def test_table_meta_is_parsed_from_json(self):
        orm = make_vector_orm('{"column_names": ["a", "b"]}')

        result = orm_to_domain_vector_profile(orm)

        self.assertEqual(result.table_meta["column_names"], ["a", "b"])

    def test_table_meta_is_a_dict_not_a_table_meta_instance(self):
        orm = make_vector_orm('{"column_names": []}')

        result = orm_to_domain_vector_profile(orm)

        self.assertIsInstance(result.table_meta, dict)

    def test_empty_column_names_are_preserved(self):
        orm = make_vector_orm('{"column_names": []}')

        result = orm_to_domain_vector_profile(orm)

        self.assertEqual(result.table_meta["column_names"], [])

    def test_non_ascii_table_meta_round_trips(self):
        meta = {"table_name": "bestellübersicht", "column_names": ["preis"]}
        orm = make_vector_orm(json.dumps(meta, ensure_ascii=False))

        result = orm_to_domain_vector_profile(orm)

        self.assertEqual(result.table_meta["table_name"], "bestellübersicht")

    def test_invalid_json_raises(self):
        orm = make_vector_orm("not json at all")

        with self.assertRaises(json.JSONDecodeError):
            orm_to_domain_vector_profile(orm)

    def test_none_table_meta_raises_type_error(self):
        orm = make_vector_orm(None)

        with self.assertRaises(TypeError):
            orm_to_domain_vector_profile(orm)

    def test_result_is_frozen(self):
        orm = make_vector_orm("{}")

        result = orm_to_domain_vector_profile(orm)

        with self.assertRaises(FrozenInstanceError):
            result.table_name = "changed"


class TestSemanticCacheMetaFromDto(unittest.TestCase):
    def setUp(self):
        self.expires_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.model_ref_id = uuid4()

    def make_entry(self, **overrides) -> SemanticCacheEntry:
        payload = {
            "embedding": [0.1, 0.2, 0.3],
            "json_payload": {"answer": "42"},
            "expires_at": self.expires_at,
            "provider": "openai",
            "model_id": "gpt-4o",
            "model_ref_id": self.model_ref_id,
        }
        payload.update(overrides)
        return SemanticCacheEntry(**payload)

    def test_maps_embedding_to_top_level(self):
        result = semantic_cache_meta_from_dto(self.make_entry())

        self.assertIsInstance(result, SemanticCacheMeta)
        self.assertEqual(result.embedding, [0.1, 0.2, 0.3])

    def test_maps_remaining_fields_into_extra(self):
        result = semantic_cache_meta_from_dto(self.make_entry())

        self.assertEqual(
            result.extra,
            {
                "json_payload": {"answer": "42"},
                "expires_at": self.expires_at,
                "provider": "openai",
                "model_id": "gpt-4o",
                "model_ref_id": self.model_ref_id,
            },
        )

    def test_extra_contains_exactly_the_expected_keys(self):
        result = semantic_cache_meta_from_dto(self.make_entry())

        self.assertEqual(
            set(result.extra),
            {"json_payload", "expires_at", "provider", "model_id", "model_ref_id"},
        )
        self.assertNotIn("embedding", result.extra)

    def test_null_model_ref_id_is_carried_through(self):
        result = semantic_cache_meta_from_dto(self.make_entry(model_ref_id=None))

        self.assertIsNone(result.extra["model_ref_id"])

    def test_expires_at_keeps_its_timezone(self):
        result = semantic_cache_meta_from_dto(self.make_entry())

        self.assertEqual(result.extra["expires_at"].tzinfo, timezone.utc)

    def test_empty_json_payload_is_preserved(self):
        result = semantic_cache_meta_from_dto(self.make_entry(json_payload={}))

        self.assertEqual(result.extra["json_payload"], {})

    def test_embedding_is_not_copied_defensively(self):
        entry = self.make_entry()
        result = semantic_cache_meta_from_dto(entry)

        entry.embedding.append(0.4)

        self.assertEqual(result.embedding, [0.1, 0.2, 0.3, 0.4])


class TestRefineFiltersFromDto(unittest.TestCase):
    def setUp(self):
        self.model_ref_id = uuid4()

    def make_query(self, **overrides) -> SemanticCacheLookupQuery:
        payload = {
            "embedding": [0.1, 0.2],
            "provider": "openai",
            "model_id": "gpt-4o",
            "model_ref_id": self.model_ref_id,
        }
        payload.update(overrides)
        return SemanticCacheLookupQuery(**payload)

    @staticmethod
    def as_pairs(filters: list[FieldCondition]) -> list[tuple[str, object]]:
        return [(f.key, f.match.value) for f in filters]

    def test_builds_all_three_conditions(self):
        result = refine_filters_from_dto(self.make_query())

        self.assertEqual(len(result), 3)
        self.assertEqual(
            self.as_pairs(result),
            [
                ("provider", "openai"),
                ("model_id", "gpt-4o"),
                ("model_ref_id", str(self.model_ref_id)),
            ],
        )

    def test_conditions_are_field_conditions_with_match_value(self):
        result = refine_filters_from_dto(self.make_query())

        for condition in result:
            self.assertIsInstance(condition, FieldCondition)
            self.assertIsInstance(condition.match, MatchValue)

    def test_model_ref_id_is_stringified(self):
        result = refine_filters_from_dto(self.make_query())

        model_ref_condition = result[2]
        self.assertIsInstance(model_ref_condition.match.value, str)
        self.assertEqual(model_ref_condition.match.value, str(self.model_ref_id))

    def test_omits_model_ref_id_when_none(self):
        result = refine_filters_from_dto(self.make_query(model_ref_id=None))

        self.assertEqual(
            self.as_pairs(result),
            [("provider", "openai"), ("model_id", "gpt-4o")],
        )

    def test_omits_provider_when_empty_string(self):
        result = refine_filters_from_dto(self.make_query(provider=""))

        keys = [key for key, _ in self.as_pairs(result)]
        self.assertNotIn("provider", keys)

    def test_omits_model_id_when_empty_string(self):
        result = refine_filters_from_dto(self.make_query(model_id=""))

        keys = [key for key, _ in self.as_pairs(result)]
        self.assertNotIn("model_id", keys)

    def test_returns_empty_list_when_nothing_to_filter_on(self):
        query = self.make_query(provider="", model_id="", model_ref_id=None)

        result = refine_filters_from_dto(query)

        self.assertEqual(result, [])

    def test_order_is_stable(self):
        first = refine_filters_from_dto(self.make_query())
        second = refine_filters_from_dto(self.make_query())

        self.assertEqual(self.as_pairs(first), self.as_pairs(second))

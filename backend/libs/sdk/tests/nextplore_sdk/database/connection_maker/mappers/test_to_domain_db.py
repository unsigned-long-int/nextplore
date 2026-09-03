import unittest
from unittest.mock import patch

from nextplore_sdk.database.connection_maker.exc.exceptions import MissingDB
from nextplore_sdk.database.connection_maker.mappers.to_domain_db import to_domain_db


class TestToDomainAuth(unittest.TestCase):
    def setUp(self):
        self.DB_MAP_MOCK = patch(
            "nextplore_sdk.database.connection_maker.mappers.to_domain_db.DB_MAP"
        )
        db_map = {
            "mysql": "MYSQL",
            "sqlserver": "SQLSERVER",
            "postgresql": "POSTGRESQL",
            "snowflake": "SNOWFLAKE",
        }
        self.DB_MAP_MOCK = self.DB_MAP_MOCK.start()
        self.DB_MAP_MOCK.__getitem__.side_effect = lambda k: db_map[k]
        self.addCleanup(self.DB_MAP_MOCK.stop)

    def test_to_domain_auth_happy_path(self):
        domain = to_domain_db("snowflake")
        self.assertEqual("SNOWFLAKE", domain)

    def test_raises_missing_if_not_found(self):
        with self.assertRaises(MissingDB) as ctx:
            _ = to_domain_db("non-existing")
        self.assertIn("DB not found in map: non-existing", str(ctx.exception))

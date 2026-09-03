import unittest
from unittest.mock import patch

from nextplore_sdk.database.connection_maker.exc.exceptions import MissingCloud
from nextplore_sdk.database.connection_maker.mappers.to_domain_cloud import (
    to_domain_cloud,
)


class TestToDomainAuth(unittest.TestCase):
    def setUp(self):
        self.CLOUD_MAP_MOCK = patch(
            "nextplore_sdk.database.connection_maker.mappers.to_domain_cloud.CLOUD_MAP"
        )
        cloud_map = {
            "aws": "AWS",
            "azure": "AZURE",
            "gcp": "GCP",
            "snowflake_managed": "SNOWFLAKE_MANAGED",
        }
        self.CLOUD_MAP_MOCK = self.CLOUD_MAP_MOCK.start()
        self.CLOUD_MAP_MOCK.__getitem__.side_effect = lambda k: cloud_map[k]
        self.addCleanup(self.CLOUD_MAP_MOCK.stop)

    def test_to_domain_auth_happy_path(self):
        domain = to_domain_cloud("gcp")
        self.assertEqual("GCP", domain)

    def test_raises_missing_if_not_found(self):
        with self.assertRaises(MissingCloud) as ctx:
            _ = to_domain_cloud("non-existing")
        self.assertIn("Cloud not found in map: non-existing", str(ctx.exception))

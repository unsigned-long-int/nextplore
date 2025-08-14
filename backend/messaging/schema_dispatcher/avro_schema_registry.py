from typing import Dict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / 'schemas'


AVRO_SCHEMA_REGISTRY: Dict[str, Path] = {
    'crawlmeta.embedded': BASE / 'embedding_service' / 'crawl_meta_embedded.avsc',
    'integration.created': BASE / 'integration_service' / 'integration_created.avsc',
    'integration.deleted': BASE / 'integration_service' / 'integration_deleted.avsc',
    'integrationmeta.crawled': BASE / 'integration_service' / 'integration_meta_crawled.avsc'
}

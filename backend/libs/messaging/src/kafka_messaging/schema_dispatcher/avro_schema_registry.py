from typing import Dict
from pathlib import Path

BASE = Path('schemas').resolve()


AVRO_SCHEMA_REGISTRY: Dict[str, Path] = {
    'crawlmeta.embedded': BASE / 'embedding_service' / 'crawl_meta_embedded.avsc',
    'datastore.created': BASE / 'integration_service' / 'datastore_created.avsc',
    'datastore.deleted': BASE / 'integration_service' / 'datastore_deleted.avsc',
    'datastore.meta.crawled': BASE / 'integration_service' / 'datastore_meta_crawled.avsc'
}

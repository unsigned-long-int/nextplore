import json
import logging
from typing import NamedTuple, Dict, Any, Optional


logger = logging.getLogger(__name__)


class Manifest(NamedTuple):
    prog_name: str
    version: str
    description: str
    author: str
    license: str


def load_manifest_map() -> Dict[str, Any]:
    with open('manifest.json', 'r') as manifest_file:
        return json.load(manifest_file)


def load_manifest() -> Optional[Manifest]:
    try:
        manifest_map = load_manifest_map()
        return Manifest(
            prog_name=manifest_map['prog_name'],
            version=manifest_map['version'],
            description=manifest_map['description'],
            author=manifest_map['author'],
            license=manifest_map['license']
        )
    except FileNotFoundError as e:
        logger.error(f'Manifest not found: {str(e)}', exc_info=True)
    except json.JSONDecodeError as e:
        logger.error(f'Decoding failed: {str(e)}', exc_info=True)
    except KeyError as e:
        logger.error(f'Manifest item not found: {str(e)}', exc_info=True)
    except Exception as e:
        logger.error(f'Unknown exception occurred: {str(e)}', exc_info=True)

import json
import traceback
from typing import NamedTuple, Dict, Any, Optional

from infrastructure.event_orchestration_service.events import events
from infrastructure.event_orchestration_service.event_orchestrator import EventOrchestrator


class Manifest(NamedTuple):
    prog_name: str
    version: str
    description: str
    author: str
    license: str


def load_manifest_map() -> Dict[str, Any]:
    with open('manifest.json', 'r') as manifest_file:
        return json.load(manifest_file)


def load_manifest(event_orchestrator: EventOrchestrator) -> Optional[Manifest]:
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
        event = events.ManifestNotFound(str(e))
        event_orchestrator.queue.append(event)
    except json.JSONDecodeError as e:
        event = events.ManifestDecodingFailed(str(e))
        event_orchestrator.queue.append(event)
    except KeyError as e:
        event = events.MissingManifestItemsEncountered(str(e))
        event_orchestrator.queue.append(event)
    except Exception as e:
        message = f'Error: {str(e)}. Traceback: {traceback.format_exc()}'
        event = events.ManifestGenerationFailed(message)
        event_orchestrator.queue.append(event)

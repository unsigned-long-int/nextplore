import logging

from services.events_handler.events import events
from services.events_handler.events_orchestrator import EventOrchestrator

logger = logging.getLogger(__name__)


def log_error(event: events.Event, event_orchestrator: EventOrchestrator) -> None:
    logger.error(event.message)


def abort(event: events.Event, event_orchestrator: EventOrchestrator) -> None:
    raise SystemExit(f'{event} aborted execution')

from typing import Dict, List, Generator, Callable, Type
from functools import singledispatch

from services.events_handler import events, commands

from .event_orchestrator import EventOrchestrator
from .actions import (
    log_error,
    abort
)

EVENTS_HANDLER: Dict[Type[events.Event], List[Callable]] = {
    events.OpenAICredentialsLoadFailed: [log_error],
    events.SQLConnectionStringLoadFailed: [log_error],
    events.OpenAIClientLoadFailed: [log_error],
    events.ManifestNotFound: [log_error],
    events.ManifestDecodingFailed: [log_error],
    events.MissingManifestItemsEncountered: [log_error],
    events.ManifestGenerationFailed: [log_error],
    events.TableSpecGenerationFailed: [log_error],
    events.DatabaseSpecNotFound: [log_error],
    events.SchemaSpecNotFound: [log_error],
    events.TableSpecNotFound: [log_error],
    events.ReflectedColumnNotFound: [log_error]
}

COMMANDS_HANDLER: Dict[Type[commands.Command], Callable] = {
}


def handle_event(
        doable: events.Event | commands.Command,
        event_orchestrator: EventOrchestrator
) -> None:
    queue = [doable]

    while queue:
        entity = queue.pop(0)
        handlers = produce_operations(entity)

        for handler in handlers:
            handler(entity=entity, event_orchestrator=event_orchestrator)
            queue.extend(event_orchestrator.collect_new_events())


@singledispatch
def produce_operations(entity) -> Generator[Callable, None, None]:
    raise NotImplementedError


@produce_operations.register
def _(entity: commands.Command) -> Generator[Callable, None, None]:
    handler = COMMANDS_HANDLER.get(type(entity))
    if handler is None:
        raise NotImplementedError(
            f'No handler found for command: {type(entity)}.')
    yield handler


@produce_operations.register
def _(entity: events.Event) -> Generator[Callable, None, None]:
    handlers = EVENTS_HANDLER.get(type(entity), [])
    if not handlers:
        raise NotImplementedError(
            f'No handlers found for event: {type(entity)}.')

    yield from EVENTS_HANDLER[type(entity)]

def handle_event(event: events.Event, event_orchestrator: EventOrchestrator) -> None:
    queue = [event]
    while queue:
        event = queue.pop(0)
        handlers = EVENTS_HANDLER[type(event)]

        for handler in handlers:
            handler(event=event, event_orchestrator=event_orchestrator)
            queue.extend(event_orchestrator.collect_new_events())

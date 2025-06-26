from openai import OpenAI, OpenAIError
from typing import Optional

from services.event_orchestration_service.event_orchestrator import EventOrchestrator
from services.event_orchestration_service.events import events


def load_open_ai_client(api_key: str, event_orchestrator: EventOrchestrator) -> Optional[OpenAI]:
    try:
        client = OpenAI(api_key=api_key)
        return client
    except OpenAIError as e:
        event = events.OpenAIClientLoadFailed(str(e))
        event_orchestrator.queue.append(event)

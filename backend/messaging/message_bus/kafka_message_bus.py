import json
import logging 
import os

from typing import Dict, List, Optional, Callable, Type
from threading import Thread 
from pydantic.json import pydantic_encoder
from kafka import KafkaProducer, KafkaConsumer

from messaging.events import events 
from messaging.registry import register_event, get_event_cls


logger = logging.getLogger(__name__)


class KafkaMessageBus:
    def __init__(self) -> None:
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            value_serializer=lambda value: json.dumps(value, default=pydantic_encoder).encode('utf-8')
        )
        self.handlers: Dict[str, List[Callable[[events.Event]], None]] = {}

    def publish(self, event: events.Event) -> None:
        for topic in event.get_topics():
            payload = event.model_dump()
            payload.update({
                'event_name': event.event_name,
                'version': event.version
            })
            self.producer.send(topic, payload)
            logger.info(f'Published to topic: {topic}')

        self.producer.flush()

    def subscribe(self, event_cls: Type[events.Event], handler: Callable[[events.Event], None]) -> None:
        register_event(event_cls)
        topic = event_cls.event_name
        self.handlers.setdefault(topic, []).append(handler)

        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            value_deserializer=lambda value: json.loads(value.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id=f'{os.getenv('KAFKA_GROUP_PREFIX')}-{topic}',
            enable_auto_commit=True
        )

        def _consume() -> None:
            for letter in consumer:
                try:
                    data = letter.value
                    event_type = get_event_cls(data['event_name'])
                    event = event_type(**data)
                    for handler in self.handlers[topic]:
                        handler(event)
                except Exception as e:
                    logger.error(f'Event: {event_type} failed: {str(e)}', exc_info=True)
            
        Thread(target=_consume, daemon=True).start()
        logger.info(f'Subscribed to a topic:{topic}')


_kafka_message_bus: Optional[KafkaMessageBus] = None

def get_kafka_message_bus() -> KafkaMessageBus:
    global _kafka_message_bus
    if _kafka_message_bus is None:
        _kafka_message_bus = KafkaMessageBus()
    return _kafka_message_bus
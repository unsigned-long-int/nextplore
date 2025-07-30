import json
import logging 
import os
import asyncio

from typing import Dict, List, Optional, Callable, Type, Awaitable
from pydantic.json import pydantic_encoder
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from messaging.events.base import BaseEvent 
from messaging.registry import register_event, get_event_cls


logger = logging.getLogger(__name__)


class AsyncKafkaMessageBus:
    def __init__(self) -> None:
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumers: List[AIOKafkaConsumer] = []
        self._consume_tasks: List[asyncio.Task] = []
        self._handlers: Dict[str, List[Callable[[BaseEvent]], None | Awaitable[None]]] = {}

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            value_serializer=lambda value: json.dumps(value, default=pydantic_encoder).encode('utf-8')
        )
        await self._producer.start()

    async def stop(self) -> None:
        for consumer in self._consumers:
            await consumer.stop()
        for task in self._consume_tasks:
            task.cancel()
        if self._producer:
            await self._producer.stop()

    async def publish(self, event: BaseEvent) -> None:
        for topic in event.get_topics():
            payload = event.model_dump()
            payload.update({
                'event_name': event.event_name,
                'version': event.version
            })
            await self._producer.send_and_wait(topic, payload)
            logger.info(f'Published to topic: {topic}')


    async def subscribe(self, event_cls: Type[BaseEvent], handler: Callable[[BaseEvent], None | Awaitable[None]]) -> None:
        register_event(event_cls)
        topic = event_cls.event_name
        self._handlers.setdefault(topic, []).append(handler)

        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            value_deserializer=lambda value: json.loads(value.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id=f'{os.getenv('KAFKA_GROUP_PREFIX')}-{topic}',
            enable_auto_commit=True
        )
        await consumer.start()
        self._consumers.append(consumer)

        async def _consume() -> None:
            async for letter in consumer:
                try:
                    data = letter.value
                    event_type = get_event_cls(data['event_name'])
                    event = event_type(**data)
                    for handler in self._handlers[topic]:
                        await handler(event)
                except Exception as e:
                    logger.error(f'Event: {event_type} failed: {str(e)}', exc_info=True)
            
        task = asyncio.create_task(_consume())
        self._consume_tasks.append(task)
        logger.info(f'Subscribed to a topic:{topic}')


_kafka_message_bus: Optional[AsyncKafkaMessageBus] = None

def get_kafka_message_bus() -> AsyncKafkaMessageBus:
    global _kafka_message_bus
    if _kafka_message_bus is None:
        _kafka_message_bus = AsyncKafkaMessageBus()
    return _kafka_message_bus
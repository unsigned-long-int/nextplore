import json
import logging 
import os
import asyncio
import inspect

from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Type, Awaitable
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from kafka_messaging.codec import Codec, AvroCodec, to_avro_values
from kafka_messaging.schema_dispatcher import dispatch_schema
from kafka_messaging.schema_registry_client import ConfluentSchemaRegistryClient
from kafka_messaging.events.base import BaseEvent
from kafka_messaging.registry import register_event, get_event_cls


logger = logging.getLogger(__name__)


class AsyncKafkaMessageBus:
    def __init__(self, codec: Codec) -> None:
        self._codec = codec
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumers: List[AIOKafkaConsumer] = []
        self._consume_tasks: List[asyncio.Task] = []
        self._handlers: Dict[str, List[Callable[[BaseEvent], Awaitable[None] | None]]] = {}

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            acks='all',
            enable_idempotence=True
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
        headers = [(k, v.encode()) for k, v in event.headers().items()]
        for topic in event.get_topics():
            value_bytes = self._codec.serialize(topic, event)

            await self._producer.send_and_wait(topic, value=value_bytes, key=event.partition_key, headers=headers)
            logger.info(f'Published to topic: {topic}')

    async def _create_consumer(self, topic: str) -> AIOKafkaConsumer:
        group_prefix = os.getenv('KAFKA_GROUP_PREFIX', 'nextplore')
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            auto_offset_reset='earliest',
            group_id=f'{group_prefix}-{topic}',
            enable_auto_commit=False,
        )
        await consumer.start()
        self._consumers.append(consumer)
        return consumer
    
    async def _run_handlers(self, topic: str, event: BaseEvent) -> None:
        for handler in self._handlers.get(topic, ()):
            result = handler(event)
            if inspect.isawaitable(result):
                await result

    async def _handle_error(self, e: Exception, record, topic: str, consumer: AIOKafkaConsumer) -> None:
        try:
            data = self._codec.deserialize(record.value)
        except Exception:
            data = {'raw': str(record.value[:128])}

        org_id = data.get('organization_id')
        key = (str(org_id).encode('utf-8') if org_id else None)
        dlq_payload = {
            'original_event': to_avro_values(data),
            'error': str(e),
            'original_topic': record.topic,
            'partition': record.partition,
            'offset': record.offset,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        try:
            await self._producer.send_and_wait(f'{topic}-dlq', value=json.dumps(dlq_payload).encode('utf-8'), key=key)
            logger.error(f'Event failed and sent to DLQ; topic={topic} offset={record.offset}: {e}', exc_info=True)
        except Exception:
            logger.error('DLQ publish failed; leaving offset uncommitted', exc_info=True)
        await consumer.commit()

    async def _process_record(self, record, topic: str, consumer: AIOKafkaConsumer) -> None:
        try:
            data = self._codec.deserialize(record.value)
            event_type = get_event_cls(data['event_name'])
            event = event_type(**data)
            await self._run_handlers(topic, event)
            await consumer.commit()
        except Exception as e:
            await self._handle_error(e, record, topic, consumer)

    async def _consume_loop(self, consumer: AIOKafkaConsumer, topic: str) -> None:
        try:
            async for record in consumer:
                await self._process_record(record, topic, consumer)
        except Exception:
            logger.error(f'Unhandled exception in consume loop for topic: {topic}', exc_info=True)

    async def subscribe(
        self,
        event_cls: Type[BaseEvent],
        handler: Callable[[BaseEvent], Optional[Awaitable[None]]]
    ) -> None:
        register_event(event_cls)
        topic = event_cls.event_name
        self._handlers.setdefault(topic, []).append(handler)

        consumer = await self._create_consumer(topic)
        task = asyncio.create_task(self._consume_loop(consumer, topic))
        self._consume_tasks.append(task)
        logger.info(f'Subscribed to a topic:{topic}')


_kafka_message_bus: Optional[AsyncKafkaMessageBus] = None


def get_kafka_message_bus() -> AsyncKafkaMessageBus:
    global _kafka_message_bus
    if _kafka_message_bus is None:
        sr_url = os.getenv('SCHEMA_REGISTRY_URL', 'http://schema-registry:8081')
        sr_client = ConfluentSchemaRegistryClient(sr_url, dispatch_schema)
        codec = AvroCodec(sr_client, dispatch_schema)
        _kafka_message_bus = AsyncKafkaMessageBus(codec)
    return _kafka_message_bus

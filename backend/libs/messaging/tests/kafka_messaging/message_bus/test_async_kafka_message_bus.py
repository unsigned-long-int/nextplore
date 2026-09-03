import asyncio
import json
import os
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, call, patch

from kafka_messaging.message_bus.async_kafka_message_bus import (
    AsyncKafkaMessageBus,
    get_kafka_message_bus,
)


class TestAsyncKafkaMessageBus(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
                "KAFKA_GROUP_PREFIX": "testprefix",
                "SCHEMA_REGISTRY_URL": "http://schema-registry:8081",
            },
            clear=False,
        )
        self.env_patcher.start()

        self.codec = MagicMock()
        self.bus = AsyncKafkaMessageBus(codec=self.codec)

    def tearDown(self):
        self.env_patcher.stop()

    @patch("kafka_messaging.message_bus.async_kafka_message_bus.AIOKafkaProducer")
    async def test_start_initializes_producer(self, producer_mock):
        producer = AsyncMock()
        producer_mock.return_value = producer

        await self.bus.start()

        producer_mock.assert_called_once_with(
            bootstrap_servers="kafka:9092", acks="all", enable_idempotence=True
        )
        producer.start.assert_awaited_once()

    async def test_stop_stops_consumers_tasks_and_producer(self):
        producer = AsyncMock()
        self.bus._producer = producer

        consumer1 = AsyncMock()
        consumer2 = AsyncMock()
        self.bus._consumers.extend([consumer1, consumer2])

        task1 = asyncio.create_task(asyncio.sleep(0))
        task2 = asyncio.create_task(asyncio.sleep(0))
        self.bus._consume_tasks.extend([task1, task2])

        await self.bus.stop()
        await asyncio.sleep(0)

        consumer1.stop.assert_awaited_once()
        consumer2.stop.assert_awaited_once()
        self.assertTrue(task1.cancelled())
        self.assertTrue(task2.cancelled())
        producer.stop.assert_awaited_once()

    async def test_publish_sends_to_all_topics_with_headers_and_key(self):
        producer = AsyncMock()
        self.bus._producer = producer

        self.codec.serialize.return_value = b"payload"

        class FakeEvent:
            event_name = "fake"
            partition_key = b"key-123"

            def get_topics(self):
                return ["topic-a", "topic-b"]

            def headers(self):
                return {"h1": "v1", "h2": "v2"}

        evt = FakeEvent()

        await self.bus.publish(evt)

        headers = [("h1", b"v1"), ("h2", b"v2")]

        calls_ = [
            call("topic-a", value=b"payload", key=b"key-123", headers=headers),
            call("topic-b", value=b"payload", key=b"key-123", headers=headers),
        ]
        producer.send_and_wait.assert_has_awaits(calls_, any_order=False)

    async def test_process_record_success_invokes_handler_and_commits(self):
        consumer = AsyncMock()
        topic = "user.created"

        data = {"event_name": "UserCreated", "organization_id": "org-1", "foo": "bar"}
        self.codec.deserialize.return_value = data

        with patch(
            "kafka_messaging.message_bus.async_kafka_message_bus.get_event_cls"
        ) as get_event_cls:

            class EV:
                def __init__(self, **kwargs):
                    self.payload = kwargs

            get_event_cls.return_value = EV

            called = asyncio.Event()

            async def handler(ev):
                self.assertIsInstance(ev, EV)
                self.assertEqual(ev.payload, data)
                called.set()

            self.bus._handlers[topic] = [handler]

            record = types.SimpleNamespace(
                value=b"some-binary",
                topic=topic,
                partition=0,
                offset=42,
            )

            await self.bus._process_record(record, topic, consumer)

            self.assertTrue(called.is_set())
            consumer.commit.assert_awaited_once()

    async def test_handle_error_sends_to_dlq_and_commits_when_deserialize_fails(self):
        producer = AsyncMock()
        self.bus._producer = producer

        self.codec.deserialize.side_effect = Exception("boom")

        consumer = AsyncMock()
        topic = "payments.processed"
        record = types.SimpleNamespace(
            value=b"\x00\x01\x02\x03" * 10, topic=topic, partition=2, offset=99
        )

        await self.bus._handle_error(
            RuntimeError("handler fail"), record, topic, consumer
        )

        args, kwargs = producer.send_and_wait.await_args
        self.assertEqual(args[0], f"{topic}-dlq")
        dlq_payload = json.loads(kwargs["value"].decode("utf-8"))
        self.assertEqual(dlq_payload["original_topic"], topic)
        self.assertEqual(dlq_payload["partition"], 2)
        self.assertEqual(dlq_payload["offset"], 99)
        self.assertIn("error", dlq_payload)
        self.assertIsNone(kwargs.get("key"))

        consumer.commit.assert_awaited_once()

    @patch("kafka_messaging.message_bus.async_kafka_message_bus.AIOKafkaConsumer")
    async def test_subscribe_registers_handler_and_starts_consume_loop(
        self, ConsumerMock
    ):
        consumer = AsyncMock()
        ConsumerMock.return_value = consumer

        with patch(
            "kafka_messaging.message_bus.async_kafka_message_bus.register_event"
        ) as register_event:
            self.bus._consume_loop = AsyncMock(return_value=None)

            class Evt:
                event_name = "orders.created"

            def handler(_):
                # empty mockup for test
                pass

            await self.bus.subscribe(Evt, handler)

            register_event.assert_called_once_with(Evt)
            self.assertIn("orders.created", self.bus._handlers)
            self.assertEqual(self.bus._handlers["orders.created"][0], handler)
            self.assertIn(consumer, self.bus._consumers)
            for t in self.bus._consume_tasks:
                t.cancel()
            await asyncio.gather(*self.bus._consume_tasks, return_exceptions=True)

    @patch(
        "kafka_messaging.message_bus.async_kafka_message_bus.ConfluentSchemaRegistryClient"
    )
    @patch("kafka_messaging.message_bus.async_kafka_message_bus.AvroCodec")
    def test_get_kafka_message_bus_singleton(self, avro_codec_mock, src_client_mock):
        from kafka_messaging.message_bus.async_kafka_message_bus import (
            _kafka_message_bus as single_ref,
        )

        if single_ref is not None:
            import kafka_messaging.message_bus.async_kafka_message_bus as kmb

            kmb._kafka_message_bus = None

        bus1 = get_kafka_message_bus()
        bus2 = get_kafka_message_bus()

        self.assertIs(bus1, bus2)
        src_client_mock.assert_called_once()
        avro_codec_mock.assert_called_once()

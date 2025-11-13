import unittest
from unittest.mock import patch
from dataclasses import dataclass
from typing import ClassVar

from kafka_messaging.registry.registry import register_event, get_event_cls

@dataclass
class DummyEvent:
    event_name: ClassVar[str] = 'dummy'

class TestRegistry(unittest.TestCase):

    @patch('kafka_messaging.registry.registry._EVENT_REGISTRY',  new_callable=dict)
    def test_registers_event(self, event_registry_mock):
        register_event(DummyEvent)
        self.assertIs(event_registry_mock[DummyEvent.event_name], DummyEvent)

    def test_gets_event(self):
        register_event(DummyEvent)
        self.assertIs(get_event_cls(DummyEvent.event_name), DummyEvent)
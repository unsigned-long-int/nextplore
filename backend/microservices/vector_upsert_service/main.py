import time

from messaging.message_bus import get_kafka_message_bus
from messaging.events import events
from api.handlers import handle_vector_upsert


def start_kafka_listener() -> None:
    get_kafka_message_bus().subscribe(
        event_cls=events.CrawlMetaVectorized, 
        handler=handle_vector_upsert
    )
    
    while True:
        time.sleep(60)

if __name__ == '__main__':
    start_kafka_listener()

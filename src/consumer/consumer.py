import threading
import pika
import json
from src.domain.events.cat_event import CatCreatedEvent
from src.for_logs.logging_config import setup_logger

logger = setup_logger()


def callback(ch, method, properties, body):
    try:
        event_data = json.loads(body)
        event_type = event_data.get("event_type")

        if event_type == "CatCreatedEvent":
            cat_event = CatCreatedEvent(**event_data["data"])
            logger.info(
                logger_class="CatConsumer",
                event="CatCreatedEventReceived",
                message=f"Received CatCreatedEvent: {cat_event}",
                summary="Cat created event processed successfully",
                params={"cat_event": cat_event.model_dump()},
            )
        else:
            logger.warning(
                logger_class="CatConsumer",
                event="UnknownEvent",
                message=f"Unknown event type: {event_type}",
                summary="Unknown event received from RabbitMQ",
                params={"event_type": event_type},
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(
            logger_class="CatConsumer",
            event="EventProcessingError",
            message=str(e),
            summary=f"Error processing event: {str(e)}",
            params={"error": str(e), "raw_event": body.decode()},
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


class RabbitConsumer:
    def __init__(self):
        self._thread = None
        self._connection = None
        self._channel = None
        self._stopping = False

    def _consume(self):
        try:
            credentials = pika.PlainCredentials("guest", "guest")
            parameters = pika.ConnectionParameters(
                host="localhost",
                port=5672,
                virtual_host="/",
                credentials=credentials,
            )
            self._connection = pika.BlockingConnection(parameters)
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            self._channel = self._connection.channel()

            self._channel.exchange_declare(
                exchange="cat_event", exchange_type="topic", durable=True
            )
            self._channel.queue_declare(queue="cat.*", durable=True)
            self._channel.queue_bind(
                exchange="cat_event", queue="cat.*", routing_key="cat.*"
            )

            self._channel.basic_consume(queue="cat.*", on_message_callback=callback)

            logger.info(
                logger_class="CatConsumer",
                event="ConsumerStarted",
                message="Cat consumer started. Waiting for events...",
                summary="Consumer is waiting for cat events on 'cat.*' queue.",
            )

            while not self._stopping:
                self._connection.process_data_events(time_limit=1)

        except Exception as e:
            logger.error(
                logger_class="CatConsumer",
                event="ConsumerError",
                message=str(e),
                summary=f"Error in consumer loop: {str(e)}",
                params={"exception": str(e)},
            )
            print(e)

    async def start(self):
        self._stopping = False
        self._thread = threading.Thread(target=self._consume, daemon=True)
        self._thread.start()

    async def stop(self):
        self._stopping = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

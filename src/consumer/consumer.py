import pika
import json
from src.domain.events.cat_event import CatCreatedEvent
from src.for_logs.logging_config import setup_logger

logger = setup_logger()


def callback(ch, method, properties, body):
    """Обрабатывает входящее сообщение из очереди."""
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


def start_consumer():
    """Запускает потребителя, слушающего очередь cat.*."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connection.channel()

        channel.exchange_declare(
            exchange="cat_events", exchange_type="topic", durable=True
        )
        channel.queue_declare(queue="cat.*", durable=True)
        channel.queue_bind(
            exchange="cat_events", queue="cat.*", routing_key="cat.*"
        )

        channel.basic_consume(queue="cat.*", on_message_callback=callback)

        logger.info(
            logger_class="CatConsumer",
            event="ConsumerStarted",
            message="Cat consumer started. Waiting for events...",
            summary="Consumer is waiting for cat events on 'cat.*' queue.",
        )

        channel.start_consuming()

    except KeyboardInterrupt:
        logger.info(
            logger_class="CatConsumer",
            event="ConsumerStopped",
            message="Consumer stopped by user.",
            summary="Cat consumer has been stopped.",
        )
    except Exception as e:
        logger.error(
            logger_class="CatConsumer",
            event="ConsumerStartError",
            message=str(e),
            summary=f"Error starting consumer: {str(e)}",
            params={"exception": str(e)},
        )

import json
import pika

from src.domain.repositories.event_repository import AbstractEventPublisher
from src.infrastructure.rabbit_and_celery.message_broker.config import rabbitmq_settings
from src.for_logs.logging_config import setup_logger
from src.application.exceptions.exceptions import AppError
import re

app_logger = setup_logger()


class RabbitMQPublisher(AbstractEventPublisher):
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = rabbitmq_settings.exchange_name
        self.queue_name = rabbitmq_settings.queue_name
        self.routing_key = rabbitmq_settings.routing_key

    def connect(self):
        try:
            credentials = pika.PlainCredentials(
                rabbitmq_settings.username, rabbitmq_settings.password
            )
            parameters = pika.ConnectionParameters(
                host=rabbitmq_settings.host,
                port=rabbitmq_settings.port,
                virtual_host="/",
                credentials=credentials,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type="topic",
                durable=True,
                passive=False,
            )
            print(f"[✓] Exchange '{self.exchange}' создан (или уже существует)")

            self.channel.queue_declare(queue=self.queue_name, durable=True)
            print(f"[✓] Queue '{self.queue_name}' создана (или уже есть)")

            self.channel.queue_bind(
                exchange=self.exchange,
                queue=self.queue_name,
                routing_key=self.routing_key,
            )
            print(f"[✓] Queue привязана к exchange по ключу '{self.routing_key}'")

        except pika.exceptions.ChannelClosedByBroker as e:
            print(f"[✗] Ошибка: Channel closed by broker — {e}")
            raise
        except Exception as e:
            print(f"[✗] Ошибка подключения: {e}")
            raise

    def disconnect(self):
        try:
            if self.connection:
                self.connection.close()
                app_logger.info(
                    logger_class=self.__class__.__name__,
                    event="RabbitMQDisconnected",
                    message="Disconnected from RabbitMQ",
                    summary="RabbitMQ connection closed",
                )
        except Exception as e:
            app_logger.error(
                logger_class=self.__class__.__name__,
                event="RabbitMQDisconnectError",
                message=str(e),
                summary=f"Error disconnecting from RabbitMQ: {str(e)}",
                ErrClass=self.__class__.__name__,
                ErrMethod="disconnect",
            )
            print(e)

    @staticmethod
    def _class_name_to_routing_key(event) -> str:
        name = event.__class__.__name__
        if name.endswith("Event"):
            name = name[:-5]
        parts = re.findall(r"[A-Z][a-z]*", name)
        return ".".join(p.lower() for p in parts)

    def publish(self, event, routing_key):
        routing_key = self._class_name_to_routing_key(event)

        if not self.channel or self.connection is None or self.connection.is_closed:
            self.connect()

        try:
            if not hasattr(event, "to_dict") or not callable(event.to_dict):
                raise ValueError(f"Event must have .to_dict(). Got: {type(event)}")

            payload = event.to_dict()
            message_body = json.dumps(payload, default=str)
            self.channel.confirm_delivery()
            success = self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                ),
            )
            print(success)

            app_logger.info(
                logger_class=self.__class__.__name__,
                event="EventPublished",
                message=f"Published {event.__class__.__name__}",
                summary=f"Event published to {routing_key}",
                params={
                    "event_type": event.__class__.__name__,
                    "routing_key": routing_key,
                    "event_data": payload,
                },
            )

        except Exception as e:
            app_logger.error(
                logger_class=self.__class__.__name__,
                event="EventPublishError",
                message=str(e),
                summary=f"Failed to publish event: {str(e)}",
                params={
                    "event_type": getattr(event, "__class__", type(event).__name__),
                    "routing_key": routing_key,
                },
                ErrClass=self.__class__.__name__,
                ErrMethod="publish",
            )
            print(e)
            raise AppError(f"Failed to publish event: {e}").set_context(
                self.__class__.__name__, "publish"
            ) from e


def get_rabbit_publisher() -> RabbitMQPublisher:
    return RabbitMQPublisher()

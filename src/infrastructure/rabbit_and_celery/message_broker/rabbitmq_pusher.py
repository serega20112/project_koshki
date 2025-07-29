import json
import pika
import re
from typing import Any
from datetime import datetime

from src.domain.repositories.event_repository import AbstractEventPublisher
from src.infrastructure.rabbit_and_celery.message_broker.config import rabbitmq_settings
from src.for_logs.logging_config import setup_logger
from src.application.exceptions.exceptions import AppError

app_logger = setup_logger()

# Имена для DLX и DLQ
DLX_EXCHANGE = "dlx.cat.events"  # Dead-Letter Exchange
DLQ_QUEUE = f"dlq.{rabbitmq_settings.queue_name}"  # Мертвая очередь


class RabbitMQPublisher(AbstractEventPublisher):
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = rabbitmq_settings.exchange_name
        self.queue_name = rabbitmq_settings.queue_name
        self.routing_key = rabbitmq_settings.routing_key

    def connect(self):
        """Подключение и настройка exchange, очереди и DLQ"""
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

            # Объявляем основной exchange
            self.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type="topic",
                durable=True,
            )
            print(f"[✓] Exchange '{self.exchange}' готов")

            # Объявляем основную очередь с DLX
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": DLX_EXCHANGE,
                    "x-dead-letter-routing-key": DLQ_QUEUE,  # Можно использовать общий ключ
                },
            )
            self.channel.queue_bind(
                exchange=self.exchange,
                queue=self.queue_name,
                routing_key=self.routing_key,
            )
            print(f"[✓] Очередь '{self.queue_name}' привязана к '{self.routing_key}'")

            # === Настраиваем DLX и DLQ ===
            self.channel.exchange_declare(
                exchange=DLX_EXCHANGE,
                exchange_type="topic",
                durable=True,
            )
            self.channel.queue_declare(
                queue=DLQ_QUEUE,
                durable=True,
            )
            self.channel.queue_bind(
                exchange=DLX_EXCHANGE,
                queue=DLQ_QUEUE,
                routing_key=DLQ_QUEUE,  # Простой ключ: dlq.cat_events_queue
            )
            print(f"[✓] DLX '{DLX_EXCHANGE}' и DLQ '{DLQ_QUEUE}' настроены")

        except Exception as e:
            app_logger.error(
                logger_class=self.__class__.__name__,
                event="ConnectionFailed",
                message=str(e),
                summary="Не удалось подключиться к RabbitMQ",
                ErrClass=self.__class__.__name__,
                ErrMethod="connect",
            )
            raise

    def disconnect(self):
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                app_logger.info(
                    logger_class=self.__class__.__name__,
                    event="Disconnected",
                    message="RabbitMQ connection closed",
                )
        except Exception as e:
            app_logger.error(
                logger_class=self.__class__.__name__,
                event="DisconnectError",
                message=str(e),
                summary="Ошибка при закрытии соединения",
                ErrClass=self.__class__.__name__,
                ErrMethod="disconnect",
            )

    @staticmethod
    def _class_name_to_routing_key(event: Any) -> str:
        name = event.__class__.__name__
        if name.endswith("Event"):
            name = name[:-5]
        parts = re.findall(r"[A-Z][a-z]*", name)
        return ".".join(p.lower() for p in parts)

    def _send_to_dlq(self, bad_payload: str, error_reason: str, original_routing_key: str):
        """Отправляет 'битое' сообщение в мертвую очередь как строку"""
        if not self.channel or not self.connection or self.connection.is_closed:
            self.connect()

        try:
            self.channel.basic_publish(
                exchange=DLX_EXCHANGE,
                routing_key=DLQ_QUEUE,
                body=bad_payload,  # как строка
                properties=pika.BasicProperties(
                    content_type="text/plain",
                    delivery_mode=2,
                    headers={
                        "x-error-reason": error_reason,
                        "original-routing-key": original_routing_key,
                        "timestamp": datetime.now().isoformat(),
                    },
                ),
            )
            app_logger.warning(
                logger_class=self.__class__.__name__,
                event="SentToDLQ",
                message="Сообщение отправлено в DLQ",
                summary="Некорректное сообщение перенаправлено в мертвую очередь",
                params={
                    "dlq_exchange": DLX_EXCHANGE,
                    "dlq_routing_key": DLQ_QUEUE,
                    "error": error_reason,
                    "original_payload_preview": bad_payload[:500],
                },
            )
        except Exception as e:
            app_logger.critical(
                logger_class=self.__class__.__name__,
                event="DLQSendFailed",
                message="Не удалось отправить в DLQ",
                summary=f"Критическая ошибка: {e}",
                params={"payload": bad_payload[:300], "error": str(e)},
            )

    def publish(self, event, routing_key=None):
        # Автоматически генерируем routing_key, если не передан
        if routing_key is None:
            routing_key = self._class_name_to_routing_key(event)

        # Проверка соединения
        if not self.channel or self.connection is None or self.connection.is_closed:
            self.connect()

        try:
            # Проверяем, что у события есть to_dict
            if not hasattr(event, "to_dict") or not callable(getattr(event, "to_dict")):
                raw_repr = repr(event)
                self._send_to_dlq(
                    bad_payload=raw_repr,
                    error_reason="Event does not have callable .to_dict()",
                    original_routing_key=routing_key,
                )
                app_logger.error(
                    logger_class=self.__class__.__name__,
                    event="InvalidEvent",
                    message="Event must have .to_dict()",
                    params={"event_type": type(event).__name__, "value": raw_repr},
                )
                return  # Не кидаем исключение, просто в DLQ

            # Сериализуем
            payload = event.to_dict()
            message_body = json.dumps(payload, default=str)

            # Включаем подтверждение доставки
            self.channel.confirm_delivery()

            # Отправляем
            confirmation = self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # Устойчивое сообщение
                ),
                mandatory=True,  # Чтобы сработало return, если некуда маршрутизировать
            )

            if confirmation is None:
                app_logger.info(
                    logger_class=self.__class__.__name__,
                    event="EventPublished",
                    message=f"Published {event.__class__.__name__}",
                    params={"routing_key": routing_key, "payload": payload},
                )
            else:
                # Сообщение не было доставлено (например, нет привязки)
                self._send_to_dlq(
                    bad_payload=message_body,
                    error_reason=f"Unroutable message (Nack from broker): {confirmation}",
                    original_routing_key=routing_key,
                )

        except TypeError as e:
            # Ошибки сериализации JSON
            bad_payload = repr(event)
            self._send_to_dlq(
                bad_payload=bad_payload,
                error_reason=f"JSON serialization failed: {str(e)}",
                original_routing_key=routing_key,
            )
            app_logger.error(
                logger_class=self.__class__.__name__,
                event="SerializationError",
                message="Failed to serialize event",
                params={"event": bad_payload, "error": str(e)},
            )

        except Exception as e:
            # Любая другая ошибка (сеть, брокер и т.д.)
            bad_payload = getattr(event, "__dict__", {}) if hasattr(event, "__dict__") else repr(event)
            try:
                bad_str = json.dumps(bad_payload, default=str)
            except:
                bad_str = str(bad_payload)

            self._send_to_dlq(
                bad_payload=bad_str,
                error_reason=f"Unexpected error in publish: {type(e).__name__}: {str(e)}",
                original_routing_key=routing_key,
            )

            app_logger.error(
                logger_class=self.__class__.__name__,
                event="PublishFailed",
                message="Не удалось опубликовать событие",
                summary=str(e),
                params={"event_type": type(event).__name__, "error": str(e)},
            )
            raise AppError(f"Failed to publish event: {e}") from e


def get_rabbit_publisher() -> RabbitMQPublisher:
    return RabbitMQPublisher()
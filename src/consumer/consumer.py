# src/consumer/consumer.py
import threading
import pika
import json
from datetime import datetime, timedelta, timezone
from typing import Dict

from src.domain.events.cat_event import CatCreatedEvent
from src.for_logs.logging_config import setup_logger
from src.infrastructure.rabbit_and_celery.scheduler.scheduler import scheduler
from src.infrastructure.rabbit_and_celery.message_broker.config import rabbitmq_settings  # Импортируем настройки

logger = setup_logger()

def handle_cat_created_event(event_data):
    """Выполняется через 2 секунды"""
    try:
        cat_name = event_data["name"]
        cat_id = event_data["cat_id"]
        print(f"[Консюмер] Показываю кота: '{cat_name}' (ID={cat_id})! Прошло 2 секунды ")
    except Exception as e:
        print(f"[Консюмер] Ошибка в отложенной обработке: {e}")


def callback(ch, method, properties, body):
    try:
        print(f"🔍 [Консюмер] Вижу новое сообщение! Обработка началась...")

        event_data = json.loads(body)
        event_type = event_data.get("event_type")

        if event_type == "cat.created":
            cat_event = CatCreatedEvent(
                cat_id=event_data["cat_id"],
                name=event_data["name"],
                age=event_data["age"],
                breed_id=event_data["breed_id"],
                created_at=datetime.fromisoformat(event_data["created_at"].replace("Z", "+00:00"))
            )

            job_id = f"cat_created_delay_{cat_event.cat_id}"

            scheduler.add_job(
                func=handle_cat_created_event,
                trigger="date",
                run_date=datetime.now(timezone.utc) + timedelta(seconds=2),
                args=[cat_event.to_dict()],
                id=job_id,
                replace_existing=True,
            )

            print(f"[Консюмер] Запланирован показ кота '{cat_event.name}' через 2 секунды...")

        else:
            print(f"[Консюмер] Неизвестный тип события: {event_type}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[Консюмер] Ошибка при обработке: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


class RabbitConsumer:
    def __init__(self):
        self._thread = None
        self._connection = None
        self._channel = None
        self._stopping = False
        self.settings = rabbitmq_settings  # 🎯 Используем общие настройки

    def _consume(self):
        try:
            credentials = pika.PlainCredentials(
                self.settings.username, self.settings.password
            )
            parameters = pika.ConnectionParameters(
                host=self.settings.host,
                port=self.settings.port,
                virtual_host="/",
                credentials=credentials,
            )

            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()

            self._channel.exchange_declare(
                exchange=self.settings.exchange_name,
                exchange_type="topic",
                durable=True,
            )

            self._channel.queue_declare(
                queue=self.settings.queue_name,
                durable=True,
            )

            self._channel.queue_bind(
                exchange=self.settings.exchange_name,
                queue=self.settings.queue_name,
                routing_key=self.settings.routing_key,
            )

            self._channel.basic_consume(
                queue=self.settings.queue_name,
                on_message_callback=callback,
            )

            print(f"[Консюмер] Запущен: слушает exchange='{self.settings.exchange_name}', "
                  f"queue='{self.settings.queue_name}', routing_key='{self.settings.routing_key}'")

            logger.info(
                logger_class="CatConsumer",
                event="ConsumerStarted",
                message="Cat consumer started",
                summary=f"Ожидание событий из {self.settings.exchange_name} с ключом {self.settings.routing_key}",
                params={
                    "exchange": self.settings.exchange_name,
                    "queue": self.settings.queue_name,
                    "routing_key": self.settings.routing_key,
                },
            )

            while not self._stopping:
                self._connection.process_data_events(time_limit=1)

        except Exception as e:
            print(f"[Консюмер] Ошибка в цикле потребления: {e}")
            logger.error(
                logger_class="CatConsumer",
                event="ConsumerError",
                message=str(e),
                summary="Ошибка в основном цикле консьюмера",
                params={"exception": str(e)},
            )

    async def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stopping = False
            self._thread = threading.Thread(target=self._consume, daemon=True)
            self._thread.start()
            print("[Консюмер] Поток запущен")

    async def stop(self):
        self._stopping = True
        if self._connection and self._connection.is_open:
            self._connection.close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        print("[Консюмер] Остановлен")
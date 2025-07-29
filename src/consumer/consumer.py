from datetime import datetime, timedelta, timezone
from typing import Dict

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitExchange
from src.domain.events.cat_event import CatCreatedEvent
from src.for_logs.logging_config import setup_logger
from src.infrastructure.rabbit_and_celery.scheduler.scheduler import scheduler
from src.infrastructure.rabbit_and_celery.message_broker.config import rabbitmq_settings

logger = setup_logger()

broker = RabbitBroker(
    url=f"amqp://{rabbitmq_settings.username}:{rabbitmq_settings.password}@{rabbitmq_settings.host}:{rabbitmq_settings.port}/",
)

class Consumer:
    def __init__(self):
        self.app: FastStream = None

    def handle_cat_created_event(event_data: Dict):
        """Отложенная обработка события о коте"""
        try:
            cat_name = event_data["name"]
            cat_id = event_data["cat_id"]
            age = event_data["age"]
            color = event_data["color"]
            breed = event_data["breed"]
            breed_id = event_data["breed_id"]
            print(
                f"[Consumer] Показываю кота: '{cat_name}'\n"
                f" ID={cat_id}\n"
                f"age = {age}\n"
                f"color = {color}\n"
                f"breed = {breed}\n"
                f"breed_id = {breed_id}"
            )
        except Exception as e:
            print(f"[Consumer] Ошибка в отложенной обработке: {e}")


    # === Очереди ===

    # Основная очередь
    main_queue = RabbitQueue(
        name=rabbitmq_settings.queue_name,
        durable=True,
        routing_key=rabbitmq_settings.routing_key,
    )

    # Мертвая очередь (обычно именуется как dlq.<queue_name>)
    dlq_queue = RabbitQueue(
        name=f"dlq.{rabbitmq_settings.queue_name}",
        durable=True,
    )

    # Обмен (exchange)
    exchange = RabbitExchange(
        name=rabbitmq_settings.exchange_name,
        type="topic",
        durable=True,
    )


    # === Обработчики ===


    @broker.subscriber(queue=main_queue, exchange=exchange)
    async def consume_cat_event(message: Dict):
        """
        Обработка сообщений из основной очереди
        Ожидается JSON с event_type = 'cat.created'
        """
        try:
            print("🔍 [FastStream] Получено сообщение из основной очереди")

            event_type = message.get("event_type")
            if event_type == "cat.created":
                created_at = message["created_at"]
                if isinstance(created_at, str):
                    if created_at.endswith("Z"):
                        created_at = created_at.replace("Z", "+00:00")
                    created_at = datetime.fromisoformat(created_at)

                cat_event = CatCreatedEvent(
                    cat_id=message["cat_id"],
                    name=message["name"],
                    age=message["age"],
                    breed=message["breed"],
                    breed_id=message["breed_id"],
                    color=message["color"],
                    created_at=created_at,
                )

                job_id = f"cat_created_delay_{cat_event.cat_id}"

                scheduler.add_job(
                    func=Consumer.handle_cat_created_event,
                    trigger="date",
                    run_date=datetime.now(timezone.utc) + timedelta(seconds=2),
                    args=[cat_event.to_dict()],
                    id=job_id,
                    replace_existing=True,
                )

                print(f"[FastStream] Отложено отображение кота: {cat_event.name}")

            else:
                print(f"[FastStream] Неизвестный тип события: {event_type}")

        except Exception as e:
            print(f"[FastStream] Ошибка при обработке основного сообщения: {e}")
            raise


    @broker.subscriber(queue=dlq_queue)
    async def consume_dlq_message(body: str):
        """
        Обработка сообщений из мертвой очереди.
        Выводим как строку — без парсинга.
        """
        print(f"💀 [FastStream DLQ] Получено сообщение из мертвой очереди:\n{body}")

        # Логгируем как строку
        logger.warning(
            logger_class="DLQConsumer",
            event="MessageFromDLQ",
            message="Сообщение из мертвой очереди",
            summary="Сообщение не было обработано и попало в DLQ",
            params={"raw_body": body},
        )
    async def start(self):
        """Запускает консьюмера"""
        print("🚀 Запускаем  consumer...")

    async def stop(self):
        print("consumer stopped")

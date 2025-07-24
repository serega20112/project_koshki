from src.infrastructure.rabbit_and_celery.message_broker.rabbitmq_pusher import (
    RabbitMQPublisher,
)


def send_event_to_rabbit(event: dict, routing_key: str):
    """
    Чистая функция: отправляет событие в RabbitMQ
    Вызывается напрямую из шедулера.
    """
    publisher = RabbitMQPublisher()
    try:
        publisher.connect()
        publisher.publish(event, routing_key)
        print(f"✅ [Scheduler] Отправлено в RabbitMQ: {routing_key}")
    except Exception as e:
        print(f"❌ [Scheduler] Ошибка отправки: {e}")
    finally:
        publisher.disconnect()

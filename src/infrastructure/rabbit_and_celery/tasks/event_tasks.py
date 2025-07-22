from celery import shared_task
from src.infrastructure.rabbit_and_celery.message_broker.rabbitmq_pusher import (
    RabbitMQPublisher,
)


@shared_task
def send_event_to_rabbit(event_dict, routing_key):
    publisher = RabbitMQPublisher()
    try:
        publisher.publish(event_dict, routing_key)
    finally:
        publisher.disconnect()

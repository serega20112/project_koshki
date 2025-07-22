from src.application.services.services import CatService
from src.domain.repositories.repository import AbstractCatRepository
from src.infrastructure.rabbit_and_celery.message_broker.rabbitmq_pusher import (
    RabbitMQPublisher,
)


def initialization():
    repository = AbstractCatRepository
    service = CatService(repository)
    service.event_publisher = RabbitMQPublisher

    if service:
        return (
            service,
            f"Initialization successful repo = {repository}, service = {service}, event+pub = {service.event_publisher}",
        )
    else:
        print("error")

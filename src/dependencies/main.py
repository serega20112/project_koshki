from fastapi import Depends

from sqlalchemy.orm import Session

from src.infrastructure.database.database import get_db
from src.application.services.services import CatService
from src.domain.adapter.adapter import CatRepository
from src.infrastructure.message_broker.rabbitmq_pusher import RabbitMQPublisher


def get_service(db: Session = Depends(get_db)):
    event_publisher = RabbitMQPublisher()
    repo = CatRepository(db)
    service = CatService(repo, event_publisher)
    return service

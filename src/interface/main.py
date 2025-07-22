from fastapi import FastAPI

from src.application.services.services import CatService
from src.infrastructure.database.database import Base, engine
from src.infrastructure.api.routes.routes import router
from src.for_logs.middleware_logging import LoggingMiddleware
from src.infrastructure.message_broker.rabbitmq_pusher import RabbitMQPublisher

event_publisher = RabbitMQPublisher()
CatService.event_publisher = event_publisher
app = FastAPI()

app.include_router(router)
app.add_middleware(LoggingMiddleware)


Base.metadata.create_all(bind=engine)

print(f"Done.\n" "Logs are recording")

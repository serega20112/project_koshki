from fastapi import FastAPI

from src.consumer.consumer import RabbitConsumer
from src.infrastructure.database.database import Base, engine
from src.infrastructure.api.routes.routes import router
from src.for_logs.middleware_logging import LoggingMiddleware
from src.infrastructure.rabbit_and_celery.handler.rac_handler import (
    event_handler_middleware,
)
from src.infrastructure.rabbit_and_celery.init_rac import initialization
from src.infrastructure.rabbit_and_celery.scheduler.scheduler import start_scheduler
from src.infrastructure.rabbit_and_celery.utils.register_events import register_events

app = FastAPI()

start_scheduler()
consumer = RabbitConsumer()
app.include_router(router)
app.add_middleware(LoggingMiddleware)
app.middleware("http")(event_handler_middleware)
initialization()
register_events(app, consumer)
consumer.start()

Base.metadata.create_all(bind=engine)

print(
    f"Done.\n" "Logs are recording \n" f"{consumer} \n",
    f"{app} \n",
    f"{initialization()} \n",
    f"{consumer} \n"
)

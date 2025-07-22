from fastapi import FastAPI

from src.consumer.consumer import RabbitConsumer
from src.infrastructure.database.database import Base, engine
from src.infrastructure.api.routes.routes import router
from src.for_logs.middleware_logging import LoggingMiddleware
from src.infrastructure.rabbit_and_celery.init_rac import initialization
from src.infrastructure.rabbit_and_celery.utils.register_events import register_events

consumer = RabbitConsumer()
app = FastAPI()

app.include_router(router)
app.add_middleware(LoggingMiddleware)
initialization()
register_events(app, consumer)

Base.metadata.create_all(bind=engine)

print(f"Done.\n" "Logs are recording \n" f"{consumer, app, initialization()}")

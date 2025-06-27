from fastapi import FastAPI
from src.infrastructure.database.database import Base, engine
from src.infrastructure.api.routes.routes import router
from middleware_logging import LoggingMiddleware



app = FastAPI()

app.include_router(router)  
app.add_middleware(LoggingMiddleware)


Base.metadata.create_all(bind=engine)

print("Done")
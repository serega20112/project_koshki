from fastapi import FastAPI
from src.infrastructure.database.database import Base, engine
from src.infrastructure.api.routes.routes import router


app = FastAPI()

app.include_router(router)  


Base.metadata.create_all(bind=engine)

print("Done")
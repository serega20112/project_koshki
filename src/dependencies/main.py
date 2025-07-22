from fastapi import Depends

from sqlalchemy.orm import Session

from src.infrastructure.database.database import get_db
from src.application.services.services import CatService
from src.domain.adapter.adapter import CatRepository


def get_service(db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    return service

from fastapi import Depends, Request

from sqlalchemy.orm import Session

from src.infrastructure.database.database import get_db
from src.application.services.services import CatService
from src.domain.adapter.adapter import CatRepository


def get_service(request: Request, db: Session = Depends(get_db)):
    if not hasattr(request.state, "cat_service"):
        repo = CatRepository(db)
        service = CatService(repo)
        request.state.cat_service = service
    return request.state.cat_service

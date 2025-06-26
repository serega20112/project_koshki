from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from sqlalchemy.orm import Session
from src.infrastructure.database.database import get_db
from src.application.dto.dto import CatDTO, BreedDTO
from src.application.services.services import CatService
from src.domain.adapter.adapter import CatRepository


router = APIRouter()


@router.get("/cats")
def get_all_cats(db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    return service.get_all()


@router.post("/cats", response_model=CatDTO)
def reg_new(cat_dto: CatDTO, db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    return service.reg_new(cat_dto)


@router.get("/cats/{id}", response_model=CatDTO)
def get_one_cat(id: int, db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    cat = service.get_one(id=id)
    return cat


@router.put("/cats/{id}", response_model=CatDTO)
def update_cat(cat_dto: CatDTO, db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    cat = service.update_one(cat_dto)
    return cat


@router.delete("/cats/", response_model=dict)
def remove_cat(id: int, db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    cat = service.delete_cat(id=id)
    return {"status": f"deleted {cat}"}


# Операции с породами
@router.get("/breeds", response_model=List[BreedDTO])
def list_breeds(db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    return service.breed_list()


@router.post("/breeds", response_model=BreedDTO)
def add_breed(breed_dto: BreedDTO, db: Session = Depends(get_db)):
    repo = CatRepository(db)
    service = CatService(repo)
    return service.add_breed(breed_dto)

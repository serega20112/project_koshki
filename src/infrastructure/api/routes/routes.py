from fastapi import APIRouter, Depends
from typing import List

from src.application.dto.dto import CatDTO, BreedDTO
from src.application.services.services import CatService
from src.for_logs.logging_config import setup_logger
from src.utils.decorators.decorators import log_service
from src.dependencies.main import get_service

app_logger = setup_logger()
router = APIRouter()


@router.get("/cats")
@log_service
def get_all_cats(service: CatService = Depends(get_service)):
    return service.get_all()


@router.get("/cats/{id}", response_model=CatDTO)
@log_service
def get_one_cat(id: int, service: CatService = Depends(get_service)):
    return service.get_one(id=id)


@router.post("/cats", response_model=CatDTO)
@log_service
def reg_new(cat_dto: CatDTO, service: CatService = Depends(get_service)):
    return service.reg_new(cat_dto)


@router.put("/cats/{id}", response_model=CatDTO)
@log_service
def update_cat(id: int, cat_dto: CatDTO, service: CatService = Depends(get_service)):
    cat_dto.id = id
    return service.update_one(cat_dto)


@router.delete("/cats/", response_model=dict)
@log_service
def remove_cat(id: int, service: CatService = Depends(get_service)):
    service.delete_cat(id=id)
    return {"status": "deleted"}


@router.get("/breeds", response_model=List[BreedDTO])
@log_service
def list_breeds(service: CatService = Depends(get_service)):
    return service.breed_list()


@router.post("/breeds", response_model=BreedDTO)
@log_service
def add_breed(breed_dto: BreedDTO, service: CatService = Depends(get_service)):
    return service.add_breed(breed_dto)
from sqlalchemy.orm import Session
from typing import List, Optional
from src.domain.entitites.cat import Cat
from src.domain.repositories.repository import AbstractCatRepository
from src.infrastructure.database.models.model import CatModel
from src.application.dto.dto import BreedDTO


class CatRepository(AbstractCatRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[Cat]:
        cat_model = self.db.query(CatModel).filter(CatModel.id == id).first()
        return cat_model

    def get_all(self) -> List[Cat]:
        cats = self.db.query(CatModel).all()
        return [c for c in cats]

    def create(self, cat: Cat) -> Cat:
        cat_model = CatModel(
            name=cat.name,
            age=cat.age,
            color=cat.color,
            breed=cat.breed,
            breed_id=cat.breed_id,
        )
        self.db.add(cat_model)
        self.db.commit()
        self.db.refresh(cat_model)
        return cat_model

    def update(self, cat: Cat) -> Cat:
        cat_model = self.db.query(CatModel).filter(CatModel.id == cat.id).first()
        cat_model.name = cat.name
        cat_model.age = cat.age
        cat_model.color = cat.color
        cat_model.breed = cat.breed
        cat_model.breed_id = cat.breed_id

        self.db.commit()
        self.db.refresh(cat_model)
        return cat_model

    def delete(self, id: int) -> bool:
        cat_model = self.db.query(CatModel).filter(CatModel.id == id).first()
        self.db.delete(cat_model)
        self.db.commit()
        return True

    def breed_list(self) -> list[BreedDTO]:
        breeds = (
            self.db.query(CatModel.breed, CatModel.breed_id)
            .filter(CatModel.breed_id.isnot(None))
            .distinct()
            .all()
        )
        return [BreedDTO(breed=b[0], breed_id=b[1]) for b in breeds]

    def add_breed(self, breed_dto: BreedDTO) -> BreedDTO:
        existing_breed = (
            self.db.query(CatModel).filter(CatModel.breed == breed_dto.breed).first()
        )
        return BreedDTO(breed=existing_breed.breed, breed_id=existing_breed.breed_id)

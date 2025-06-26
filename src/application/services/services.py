from typing import List, Dict
from src.domain.repositories.repository import AbstractCatRepository
from src.application.dto.dto import CatDTO, BreedDTO


class CatService:
    def __init__(self, repository):
        self.repository = repository
        
    
    def get_one(self, id: int) -> CatDTO:
        cat = self.repository.get_by_id(id)
        return CatDTO.model_validate(cat)

    
    def reg_new(self, dto: CatDTO) -> CatDTO:
        created_cat = self.repository.create(dto)
        return CatDTO.model_validate(created_cat)

    
    def update_one(self, dto: CatDTO) -> CatDTO:
        updated_cat = self.repository.update(dto)
        return CatDTO.model_validate(updated_cat)

    
    def get_all(self) -> List[CatDTO]:
        cats = self.repository.get_all()
        return [CatDTO.model_validate(cat) for cat in cats]

    
    def delete_cat(self,id: int) -> Dict[str, str]:
        delete = self.repository.delete(id)
        return {"result": "deleted"}

    
    def add_breed(self, breed_dto: BreedDTO) -> BreedDTO:
        return self.repository.add_breed(breed_dto)

    
    def breed_list(self) -> List[BreedDTO]:
        breeds = self.repository.breed_list()
        return [BreedDTO.model_validate(breed) for breed in breeds]
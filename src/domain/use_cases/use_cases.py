from typing import List, Optional
from src.domain.entitites.cat import Cat
from src.domain.repositories.repository import AbstractCatRepository


class CatUseCases:
    def __init__(self, repo: AbstractCatRepository):
        self.repo = repo

    def get_cat(self, id: int) -> Optional[Cat]:
        return self.repo.get_by_id(id)

    def get_all_cats(self) -> List[Cat]:
        return self.repo.get_all()

    def create_cat(self, cat: Cat) -> Cat:
        return self.repo.create(cat)

    def update_cat(self, cat: Cat) -> Cat:
        return self.repo.update(cat)

    def delete_cat(self, id: int) -> bool:
        return self.repo.delete(id)

    def get_breeds(self) -> List[str]:
        return self.repo.get_breeds()

    def get_breeds_with_ids(self) -> List[dict]:
        return self.repo.get_breeds_with_ids()


class BreedUseCases:
    def __init__(self, repo: AbstractCatRepository):
        self.repo = repo

    def add_breed(self, name: str, breed_id: int) -> dict:
        breeds = self.repo.get_breeds_with_ids()
        return {"status": breeds}

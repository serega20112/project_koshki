from abc import ABC, abstractmethod
from src.domain.entitites.cat import Cat
from typing import List, Optional

class AbstractCatRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Cat]:
        ...

    @abstractmethod
    def get_all(self) -> List[Cat]:
        ...

    @abstractmethod
    def create(self, cat: Cat) -> Cat:
        ...

    @abstractmethod
    def update(self, cat: Cat) -> Cat:
        ...

    @abstractmethod
    def delete(self, id: int) -> bool:
        ...

    @abstractmethod
    def breed_list(self) -> List[str]:
        ...
    
    @abstractmethod
    def add_breed(self) -> dict:
        ...
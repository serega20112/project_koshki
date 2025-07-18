from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from src.application.dto.dto import CatDTO


@dataclass
class CatCreatedEvent:
    cat_id: int
    name: str
    age: int
    breed_id: Optional[int]
    created_at: datetime

    @classmethod
    def from_dto(cls, cat_dto: CatDTO) -> "CatCreatedEvent":
        return cls(
            cat_id=cat_dto.id,
            name=cat_dto.name,
            age=cat_dto.age,
            breed_id=cat_dto.breed_id,
            created_at=datetime.utcnow(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "cat.created",
            "cat_id": self.cat_id,
            "name": self.name,
            "age": self.age,
            "breed_id": self.breed_id,
            "created_at": self.created_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }


@dataclass
class CatUpdatedEvent:
    cat_id: int
    name: str
    age: int
    breed_id: Optional[int]
    updated_at: datetime

    @classmethod
    def from_dto(cls, cat_dto: CatDTO) -> "CatUpdatedEvent":
        return cls(
            cat_id=cat_dto.id,
            name=cat_dto.name,
            age=cat_dto.age,
            breed_id=cat_dto.breed_id,
            updated_at=datetime.utcnow(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "cat.updated",
            "cat_id": self.cat_id,
            "name": self.name,
            "age": self.age,
            "breed_id": self.breed_id,
            "updated_at": self.updated_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }


@dataclass
class CatDeletedEvent:
    cat_id: int
    deleted_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "cat.deleted",
            "cat_id": self.cat_id,
            "deleted_at": self.deleted_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

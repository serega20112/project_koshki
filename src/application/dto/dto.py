from pydantic import BaseModel


class CatDTO(BaseModel):
    id: int
    name: str
    age: int
    color: str
    breed: str
    breed_id: int

    class Config:
        from_attributes = True


class BreedDTO(BaseModel):
    breed: str
    breed_id: int

    class Config:
        from_attributes = True

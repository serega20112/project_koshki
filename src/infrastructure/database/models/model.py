from sqlalchemy import Column, Integer, String
from src.infrastructure.database.database import Base


class CatModel(Base):
    __tablename__ = "animals"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    color = Column(String)
    breed = Column(String)
    breed_id = Column(Integer)

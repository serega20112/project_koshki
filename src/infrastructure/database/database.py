from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///./animal.db",
    connect_args={
        "check_same_thread": False,  # разрешаем доступ из разных потоков
        "timeout": 20,  # время ожидания разблокировки БД (в секундах)
    },
    pool_size=500,
    max_overflow=500,
    pool_timeout=1,
    pool_pre_ping=True,
    pool_recycle=20,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()

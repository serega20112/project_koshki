from typing import List, Dict
from src.domain.repositories.repository import AbstractCatRepository
from src.application.dto.dto import CatDTO, BreedDTO
from src.application.exceptions.exceptions import (
    AppError,
    DatabaseError,
    NotFoundError,
    ValidationError
)
from src.for_logs.logging_config import setup_logger


app_logger = setup_logger()


class CatService:
    def __init__(self, repository: AbstractCatRepository):
        self.repository = repository

    def _log_error(self, exc: Exception, method_name: str, error_type: str = "UnknownError", details: dict = None):
        summary = f"Ошибка в методе '{method_name}' сервиса {self.__class__.__name__}: {str(exc)}"
        app_logger.warning(
            logger_class=self.__class__.__name__,
            event=error_type,
            message=str(exc),
            summary=summary,
            params={
                "class": self.__class__.__name__,
                "method": method_name,
                "error_type": error_type,
                "error_message": str(exc),
                "details": details or {}
            }
        )

    def get_one(self, id: int) -> CatDTO:
        try:
            cat = self.repository.get_by_id(id)
            if not cat:
                raise NotFoundError(f"Кошка с id={id} не найдена", details={"id": id})
            return CatDTO.model_validate(cat)
        except NotFoundError as e:
            self._log_error(e, "get_one", error_type="NotFoundError", details={"id": id})
            raise
        except Exception as e:
            self._log_error(e, "get_one", error_type="UnknownError", details={"exception": str(e)})
            raise AppError(f"Неизвестная ошибка при получении кошки: {e}, в сервисе get_one", details={"id": id}) from e

    def reg_new(self, dto: CatDTO) -> CatDTO:
        try:
            # Пример валидации
            if dto.age <= 0:
                raise ValidationError("Возраст должен быть положительным числом", details=dto.model_dump())
            created_cat = self.repository.create(dto)
            return CatDTO.model_validate(created_cat)
        except ValidationError as e:
            self._log_error(e, "reg_new", error_type="ValidationError", details=dto.model_dump())
            raise
        except Exception as e:
            self._log_error(e, "reg_new", error_type="UnknownError", details=dto.model_dump())
            raise AppError(f"Ошибка при регистрации новой кошки: {e}, в сервисе reg_new", details=dto.model_dump()) from e

    def update_one(self, dto: CatDTO) -> CatDTO:
        try:
            updated_cat = self.repository.update(dto)
            return CatDTO.model_validate(updated_cat)
        except Exception as e:
            self._log_error(e, "update_one", error_type="UnknownError", details=dto.model_dump())
            raise AppError(f"Ошибка при обновлении данных кошки: {e}, в сервисе update_one", details=dto.model_dump()) from e

    def get_all(self) -> List[CatDTO]:
        try:
            cats = self.repository.get_all()
            if not cats:
                raise NotFoundError("В базе нет кошек", details={"method": "get_all"})
            return [CatDTO.model_validate(cat) for cat in cats]
        except ConnectionRefusedError as e:
            self._log_error(e, "get_all", error_type="DatabaseError", details={"reason": "Connection refused"})
            raise DatabaseError("Connection to DB failed", details={"method": "get_all"}) from e
        except Exception as e:
            self._log_error(e, "get_all", error_type="UnknownError", details={"exception": str(e)})
            raise AppError(f"Неизвестная ошибка при получении списка кошек: {e}, в сервисе get_all", details={}) from e

    def delete_cat(self, id: int) -> Dict[str, str]:
        try:
            result = self.repository.delete(id)
            if not result:
                raise NotFoundError(f"Кошка с id={id} не найдена, в сервисе delete_cat", details={"id": id})
            return {"result": "deleted"}
        except NotFoundError as e:
            self._log_error(e, "delete_cat", error_type="NotFoundError", details={"id": id})
            raise
        except Exception as e:
            self._log_error(e, "delete_cat", error_type="UnknownError", details={"id": id, "exception": str(e)})
            raise AppError(f"Ошибка при удалении кошки с id={id}: {e}", details={"id": id}) from e

    def add_breed(self, breed_dto: BreedDTO) -> BreedDTO:
        try:
            return self.repository.add_breed(breed_dto)
        except Exception as e:
            self._log_error(e, "add_breed", error_type="UnknownError", details=breed_dto.model_dump())
            raise AppError(f"Ошибка при добавлении породы: {e}", details=breed_dto.model_dump()) from e

    def breed_list(self) -> List[BreedDTO]:
        try:
            breeds = self.repository.breed_list()
            if not breeds:
                raise NotFoundError("Список пород пуст", details={"method": "breed_list"})
            return [BreedDTO.model_validate(breed) for breed in breeds]
        except Exception as e:
            self._log_error(e, "breed_list", error_type="UnknownError", details={"exception": str(e)})
            raise AppError(f"Ошибка при получении списка пород: {e}", details={}) from e
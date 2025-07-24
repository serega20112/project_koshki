from typing import List, Dict

from src.domain.repositories.repository import AbstractCatRepository
from src.application.dto.dto import CatDTO, BreedDTO
from src.application.exceptions.exceptions import (
    AppError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from src.domain.events.cat_event import (
    CatCreatedEvent,
    CatUpdatedEvent,
    CatDeletedEvent,
)
from src.for_logs.logging_config import setup_logger

app_logger = setup_logger()


class CatService:
    def __init__(self, repository: AbstractCatRepository):
        self.repository = repository

    def _log_error(
        self,
        exc: Exception,
        method_name: str,
        error_type: str = "UnknownError",
        details: dict = None,
    ):
        summary = f"Ошибка {error_type}: {str(exc)}"
        err_class = getattr(exc, "ErrClass", self.__class__.__name__)
        err_method = getattr(exc, "ErrMethod", method_name)

        app_logger.warning(
            logger_class=self.__class__.__name__,
            event=error_type,
            message=str(exc),
            summary=summary,
            params={
                "method": method_name,
                "class": self.__class__.__name__,
                "error_type": error_type,
                "error_message": str(exc),
                "details": details or {},
            },
            ErrClass=err_class,
            ErrMethod=err_method,
        )

    def get_one(self, id: int) -> CatDTO:
        try:
            cat = self.repository.get_by_id(id)
            if not cat:
                raise NotFoundError(f"Кошка с id={id} не найдена", details={"id": id})
            return CatDTO.model_validate(cat)
        except NotFoundError as e:
            self._log_error(
                e, "get_one", error_type="NotFoundError", details={"id": id}
            )
            raise
        except Exception as e:
            self._log_error(
                e, "get_one", error_type="ServerError", details={"exception": str(e)}
            )
            raise AppError(
                f"Ошибка в сервисе {self.__class__.__name__}, метод: get_one — {e}"
            ).set_context(self.__class__.__name__, "get_one") from e

    def reg_new(self, dto: CatDTO) -> CatDTO:
        try:
            if dto.age <= 0:
                raise ValidationError(
                    "Возраст должен быть положительным числом", details=dto.model_dump()
                )

            created_cat = self.repository.create(dto)
            result_dto = CatDTO.model_validate(created_cat)
            self.event = CatCreatedEvent.from_dto(result_dto)

            app_logger.info(
                logger_class=self.__class__.__name__,
                event="CatCreated",
                message=f"Кошка создана с id={result_dto.id}",
                summary="Кошка успешно зарегистрирована",
                params=result_dto.model_dump(),
            )
            print(f"🎯 [CatService] Event set: {self.event}")
            return result_dto

        except ValidationError as e:
            self._log_error(
                e, "reg_new", error_type="ValidationError", details=e.details
            )
            raise
        except Exception as e:
            self._log_error(
                e, "reg_new", error_type="ServerError", details=dto.model_dump()
            )
            raise AppError(f"Ошибка регистрации кошки: {e}").set_context(
                self.__class__.__name__, "reg_new"
            ) from e

    def update_one(self, dto: CatDTO) -> CatDTO:
        try:
            updated_cat = self.repository.update(dto)
            result_dto = CatDTO.model_validate(updated_cat)
            self.event = CatUpdatedEvent.from_dto(updated_cat)

            app_logger.info(
                logger_class=self.__class__.__name__,
                event="CatUpdated",
                message=f"Кошка обновлена с id={result_dto.id}",
                summary="Кошка успешно обновлена",
                params=result_dto.model_dump(),
            )
            print(f"🎯 [CatService] Event set: {self.event}")
            return result_dto

        except Exception as e:
            self._log_error(
                e, "update_one", error_type="ServerError", details=dto.model_dump()
            )
            raise AppError(f"Ошибка обновления кошки: {e}").set_context(
                self.__class__.__name__, "update_one"
            ) from e

    def delete_cat(self, id: int) -> Dict[str, str]:
        try:
            cat = self.repository.get_by_id(id)
            if not cat:
                raise NotFoundError(f"Кошка с id={id} не найдена", details={"id": id})
            result = self.repository.delete(id)
            if not result:
                raise NotFoundError(f"Кошка с id={id} не найдена", details={"id": id})

            self.event = CatDeletedEvent(cat_id=id)

            app_logger.info(
                logger_class=self.__class__.__name__,
                event="CatDeleted",
                message=f"Кошка удалена с id={id}",
                summary="Кошка успешно удалена",
                params={"id": id},
            )
            print(f"🎯 [CatService] Event set: {self.event}")
            return {"result": "deleted"}

        except NotFoundError as e:
            self._log_error(
                e, "delete_cat", error_type="NotFoundError", details={"id": id}
            )
            raise
        except Exception as e:
            self._log_error(
                e,
                "delete_cat",
                error_type="ServerError",
                details={"id": id, "exception": str(e)},
            )
            raise AppError(f"Ошибка удаления кошки с id={id}: {e}").set_context(
                self.__class__.__name__, "delete_cat"
            ) from e

    def get_all(self) -> List[CatDTO]:
        try:
            cats = self.repository.get_all()
            if not cats:
                raise NotFoundError("Список кошек пуст", details={"method": "get_all"})
            return [CatDTO.model_validate(cat) for cat in cats]
        except ConnectionRefusedError as e:
            self._log_error(
                e,
                "get_all",
                error_type="DatabaseError",
                details={"reason": "Connection refused"},
            )
            raise DatabaseError(
                "Connection to DB failed", details={"method": "get_all"}
            ).set_context(self.__class__.__name__, "get_all") from e
        except Exception as e:
            self._log_error(
                e, "get_all", error_type="ServerError", details={"exception": str(e)}
            )
            raise AppError(f"Неизвестная ошибка в методе get_all: {e}").set_context(
                self.__class__.__name__, "get_all"
            ) from e

    def add_breed(self, breed_dto: BreedDTO) -> BreedDTO:
        try:
            return self.repository.add_breed(breed_dto)
        except Exception as e:
            self._log_error(
                e, "add_breed", error_type="ServerError", details=breed_dto.model_dump()
            )
            raise AppError(f"Ошибка добавления породы: {e}").set_context(
                self.__class__.__name__, "add_breed"
            ) from e

    def breed_list(self) -> List[BreedDTO]:
        try:
            breeds = self.repository.breed_list()
            if not breeds:
                raise NotFoundError(
                    "Список пород пуст", details={"method": "breed_list"}
                )
            return [BreedDTO.model_validate(breed) for breed in breeds]
        except Exception as e:
            self._log_error(
                e, "breed_list", error_type="ServerError", details={"exception": str(e)}
            )
            raise AppError(f"Ошибка получения списка пород: {e}").set_context(
                self.__class__.__name__, "breed_list"
            ) from e

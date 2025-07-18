from typing import List, Dict, Optional, Any

from src.domain.repositories.event_repository import AbstractEventPublisher
from src.domain.repositories.repository import AbstractCatRepository
from src.application.dto.dto import CatDTO, BreedDTO
from src.application.exceptions.exceptions import (
    AppError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from src.domain.events.cat_event import CatCreatedEvent, CatUpdatedEvent, CatDeletedEvent
from src.for_logs.logging_config import setup_logger
from datetime import datetime

from src.infrastructure.message_broker.rabbitmq_pusher import RabbitMQPublisher

app_logger = setup_logger()


class CatService:
    def __init__(
            self,
            repository: AbstractCatRepository,
            event_publisher: AbstractEventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher

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

    def _publish_event(self, event: Any, routing_key: str) -> None:
        """Публикует событие, если publisher доступен"""
        if self.event_publisher:
            try:
                self.event_publisher.publish(event, routing_key)
            except Exception as e:
                # Логируем ошибку, но не прерываем основной процесс
                app_logger.error(
                    logger_class=self.__class__.__name__,
                    event="EventPublishError",
                    message=str(e),
                    summary=f"Failed to publish event, but continuing: {str(e)}",
                    params={
                        "event_type": event.__class__.__name__,
                        "routing_key": routing_key
                    }
                )
                print(e)
        else:
            print("ошибка какая то или лог не отправлен")

    def get_one(self, id: int) -> CatDTO:
        try:
            cat = self.repository.get_by_id(id)
            if not cat:
                raise NotFoundError(
                    f"Кошка с id={id} не найдена", details={"id": id}
                ).set_context("CatService", "get_one")
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
                ).set_context(self.__class__.__name__, "reg_new")

            created_cat = self.repository.create(dto)
            result_dto = CatDTO.model_validate(created_cat)

            # Публикуем событие о создании кошки
            event = CatCreatedEvent.from_dto(result_dto)
            self._publish_event(event, "cat.created")

            app_logger.info(
                logger_class=self.__class__.__name__,
                event="CatCreated",
                message=f"Cat created with id={result_dto.id}",
                summary="New cat registered successfully",
                params=result_dto.model_dump()
            )

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

            # Публикуем событие об обновлении кошки
            event = CatUpdatedEvent.from_dto(result_dto)
            self._publish_event(event, "cat.updated")

            app_logger.info(
                logger_class=self.__class__.__name__,
                event="CatUpdated",
                message=f"Cat updated with id={result_dto.id}",
                summary="Cat updated successfully",
                params=result_dto.model_dump()
            )

            return result_dto
        except Exception as e:
            self._log_error(
                e, "update_one", error_type="ServerError", details=dto.model_dump()
            )
            raise AppError(f"Ошибка обновления кошки: {e}").set_context(
                self.__class__.__name__, "update_one"
            ) from e

    def get_all(self) -> List[CatDTO]:
        try:
            cats = self.repository.get_all()
            if not cats:
                raise NotFoundError(
                    "Список кошек пуст", details={"method": "get_all"}
                ).set_context(self.__class__.__name__, "get_all")
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

    def delete_cat(self, id: int) -> Dict[str, str]:
        try:
            result = self.repository.delete(id)
            if not result:
                raise NotFoundError(
                    f"Кошка с id={id} не найдена", details={"id": id}
                ).set_context(self.__class__.__name__, "delete_cat")

            # Публикуем событие об удалении кошки
            event = CatDeletedEvent(cat_id=id, deleted_at=datetime.utcnow())
            self._publish_event(event, "cat.deleted")

            app_logger.info(
                logger_class=self.__class__.__name__,
                event="CatDeleted",
                message=f"Cat deleted with id={id}",
                summary="Cat deleted successfully",
                params={"id": id}
            )

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
                ).set_context(self.__class__.__name__, "breed_list")
            return [BreedDTO.model_validate(breed) for breed in breeds]
        except Exception as e:
            self._log_error(
                e, "breed_list", error_type="ServerError", details={"exception": str(e)}
            )
            raise AppError(f"Ошибка получения списка пород: {e}").set_context(
                self.__class__.__name__, "breed_list"
            ) from e
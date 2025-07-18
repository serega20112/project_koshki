from abc import ABC, abstractmethod
from typing import Any


class AbstractEventPublisher(ABC):
    @abstractmethod
    def publish(self, event: Any, routing_key: str) -> None:
        """Публикует событие в очередь"""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Устанавливает соединение с брокером"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Закрывает соединение с брокером"""
        pass

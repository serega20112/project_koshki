class AppError(Exception):
    """Базовый класс для всех ошибок приложения"""
    def __init__(self, message: str = "Ошибка в приложении", details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.__class__.__name__}] {self.message}"


class DatabaseError(AppError):
    """Ошибка подключения или работы с БД"""
    def __init__(self, message: str = "Ошибка базы данных", details: dict = None):
        super().__init__(message=message, details=details)


class NotFoundError(AppError):
    """Объект не найден"""
    def __init__(self, message: str = "Не найдено", details: dict = None):
        super().__init__(message=message, details=details)


class ValidationError(AppError):
    """Ошибка валидации данных"""
    def __init__(self, message: str = "Ошибка валидации", details: dict = None):
        super().__init__(message=message, details=details)
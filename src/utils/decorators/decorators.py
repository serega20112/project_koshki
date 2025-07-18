from functools import wraps
from fastapi import HTTPException

from src.application.exceptions.exceptions import (
    AppError,
    NotFoundError,
    ValidationError,
    DatabaseError,
)
from src.for_logs.logging_config import setup_logger

app_logger = setup_logger()


def log_service(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        service = kwargs.get("service") or args[0] if len(args) > 0 else None
        service_name = service.__class__.__name__ if service else "UnknownService"

        app_logger.info(
            logger_class="Route",
            event=func.__name__,
            message=f"Вызов метода {func.__name__}",
            params={"kwargs": kwargs},
        )

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            err_class = getattr(e, "ErrClass", service_name)
            err_method = getattr(e, "ErrMethod", func.__name__)

            summary = f"Ошибка в {err_class}.{err_method}: {str(e)}"

            app_logger.warning(
                logger_class="Route",
                event="ServerError",
                message=str(e),
                summary=summary,
                params={
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                    "args": args,
                    "kwargs": kwargs,
                },
                ErrClass=err_class,
                ErrMethod=err_method,
            )

            if isinstance(e, NotFoundError):
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "NotFoundError",
                        "message": str(e),
                        "details": getattr(e, "details", {}),
                    },
                )
            elif isinstance(e, ValidationError):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "ValidationError",
                        "message": str(e),
                        "details": getattr(e, "details", {}),
                    },
                )
            elif isinstance(e, DatabaseError):
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "DatabaseError",
                        "message": str(e),
                        "details": getattr(e, "details", {}),
                    },
                )
            else:
                raise HTTPException(
                    status_code=500, detail={"error": "ServerError", "message": str(e)}
                )

    return wrapper

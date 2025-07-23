from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from src.for_logs.logging_config import setup_logger
from src.application.exceptions.exceptions import AppError, NotFoundError


app_logger = setup_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Миддлвэйр для логирования действий юзера в фастапи"""

    async def dispatch(self, request: Request, call_next):
        app_logger.info(
            logger_class="LoggingMiddleware",
            event="IncomingRequest",
            message="Received HTTP request",
            params={
                "method": request.method,
                "path": request.url.path,
                "headers": dict(request.headers),
                "action": request.method,
            },
        )

        try:
            response = await call_next(request)

            status_code = response.status_code
            app_logger.info(
                logger_class="LoggingMiddleware",
                event="OutgoingResponse",
                message="Sent HTTP response",
                params={
                    "status_code": status_code,
                    "headers": dict(response.headers),
                    "action": request.method,
                    "result": status_code,
                },
            )

            if 500 <= status_code < 600:
                app_logger.warning(
                    logger_class="LoggingMiddleware",
                    event="ServerErrorDetected",
                    message=f"Server error response sent: {status_code}",
                    summary=f"Ошибка на уровне сервера: код {status_code}",
                    params={
                        "status_code": status_code,
                        "method": request.method,
                        "path": request.url.path,
                        "action": request.method,
                        "result": status_code,
                    },
                    ErrClass="Request",
                    ErrMethod="dispatch",
                )

            return response

        except AppError as e:
            status_code = 404 if isinstance(e, NotFoundError) else 500

            response = JSONResponse(
                status_code=status_code,
                content={
                    "error": e.__class__.__name__,
                    "message": e.message,
                    "details": e.details,
                },
            )

            return response

        except Exception as e:
            app_logger.warning(
                logger_class="LoggingMiddleware",
                event="ServerError",
                message=f"Unhandled exception: {str(e)}",
                summary=f"Неизвестная ошибка: {str(e)}",
                params={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "method": request.method,
                    "path": request.url.path,
                    "action": request.method,
                    "result": 500,
                },
                ErrClass="UnknownClass",
                ErrMethod="UnknownMethod",
            )
            return Response(content="Internal Server Error", status_code=500)

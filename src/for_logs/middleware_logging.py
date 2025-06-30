from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from src.for_logs.logging_config import setup_logger
from src.application.exceptions.exceptions import AppError, NotFoundError


app_logger = setup_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
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
            }
        )

        try:
            response = await call_next(request)
        except AppError as e:
            error_type = e.__class__.__name__
            app_logger.warning(
                logger_class="LoggingMiddleware",
                event=error_type,
                message=str(e),
                summary=f"Ошибка {error_type}: {e.message}",
                params={
                    "error_type": error_type,
                    "error_message": e.message,
                    "error_details": e.details,
                    "method": request.method,
                    "path": request.url.path,
                    "action": request.method,
                    "result": 500 if not isinstance(e, NotFoundError) else 404
                }
            )
            response = JSONResponse(
                status_code=500 if not isinstance(e, NotFoundError) else 404,
                content={"error": error_type, "message": e.message, "details": e.details}
            )
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
                    "result": 500
                }
            )
            response = Response(content="Internal Server Error", status_code=500)

        status_code = response.status_code
        app_logger.info(
            logger_class="LoggingMiddleware",
            event="OutgoingResponse",
            message="Sent HTTP response",
            params={
                "status_code": status_code,
                "headers": dict(response.headers),
                "action": request.method,
                "result": status_code
            }
        )

        if 500 <= status_code < 600:
            app_logger.warning(
                logger_class="LoggingMiddleware",
                event="ServerErrorDetected",
                message=f"Server error response sent: {status_code}",
                params={
                    "status_code": status_code,
                    "method": request.method,
                    "path": request.url.path,
                    "action": request.method,
                    "result": status_code
                }
            )

        return response
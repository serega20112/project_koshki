from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from src.for_logs.logging_config import setup_logger

app_logger = setup_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        app_logger.info(
            logger_class="LoggingMiddleware",
            event="IncomingRequest",
            message="Received HTTP request",
            params={
                "ip": request.client.host,
                "method": request.method,
                "path": request.url.path,
                "headers": dict(request.headers)
            }
        )

        response: Response = await call_next(request)

        app_logger.info(
            logger_class="LoggingMiddleware",
            event="OutgoingResponse",
            message="Sent HTTP response",
            params={
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
        )

        return response

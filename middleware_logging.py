import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from logging_config import setup_logger

logger = setup_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Request data
        ip = request.client.host
        method = request.method
        path = request.url.path
        user_agent = request.headers.get('user-agent', '')

        try:
            body_bytes = await request.body()
            body = body_bytes.decode('utf-8')
        except Exception:
            body = ""

        request_id = request.headers.get('X-Request-ID', '')

        logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "ip": ip,
                "user_agent": user_agent,
                "method": method,
                "path": path,
                "request_body": body
            }
        )

        response: Response = await call_next(request)

        try:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            response.body_iterator = iterate_in_chunks(response_body)
            response_text = response_body.decode()
        except Exception:
            response_text = ""

        logger.info(
            "Outgoing response",
            extra={
                "request_id": request_id,
                "ip": ip,
                "user_agent": user_agent,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "response_body": response_text
            }
        )

        return response

async def iterate_in_chunks(data: bytes, chunk_size: int = 4096):
    for i in range(0, len(data), chunk_size):
        yield data[i:i+chunk_size]

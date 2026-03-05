import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_chars: int = 500):
        super().__init__(app)
        self.max_body_chars = max_body_chars

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        body_bytes = await request.body()
        body_preview = body_bytes.decode("utf-8", errors="ignore")[: self.max_body_chars]

        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request = Request(request.scope, receive)

        logger.debug(
            "request.start id=%s method=%s path=%s query=%s body_slice=%s",
            request_id,
            request.method,
            request.url.path,
            dict(request.query_params),
            body_preview,
        )

        try:
            response = await call_next(request)
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "request.end id=%s status=%s duration_ms=%s",
                request_id,
                response.status_code,
                process_time_ms,
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            return response
        except Exception:
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "request.error id=%s duration_ms=%s method=%s path=%s",
                request_id,
                process_time_ms,
                request.method,
                request.url.path,
            )
            raise

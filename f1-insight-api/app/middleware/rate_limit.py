import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_store: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        route_key = f"{client_ip}:{request.url.path}"
        now = time.time()

        request_times = self._request_store[route_key]
        while request_times and request_times[0] <= now - self.window_seconds:
            request_times.popleft()

        if len(request_times) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                },
            )

        request_times.append(now)
        return await call_next(request)

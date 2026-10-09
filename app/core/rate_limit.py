import time
from collections import OrderedDict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._window: float = 60.0
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()
        self._max_clients = 10_000
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next):
        client_ip: str = request.client.host if request.client else "unknown"
        now = time.monotonic()
        is_auth = request.url.path.rstrip("/").lower() in {"/auth/login", "/login"}
        limit = min(self.requests_per_minute, 10) if is_auth else self.requests_per_minute
        with self._lock:
            timestamps = self._requests.pop(client_ip, deque())
            while timestamps and now - timestamps[0] >= self._window:
                timestamps.popleft()
            if len(self._requests) >= self._max_clients and client_ip not in self._requests:
                self._requests.popitem(last=False)
            blocked = len(timestamps) >= limit
            if not blocked:
                timestamps.append(now)
            self._requests[client_ip] = timestamps
            remaining = max(0, limit - len(timestamps))

        if blocked:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data": None,
                    "message": "Rate limit exceeded. Please try again later.",
                    "errors": ["Too many requests"],
                },
                headers={
                    "Retry-After": str(max(1, int(self._window - (now - timestamps[0])))),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

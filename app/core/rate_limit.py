import time
from collections import OrderedDict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.auth_service import AuthService


class RateLimitMiddleware(BaseHTTPMiddleware):
    _instances: list["RateLimitMiddleware"] = []
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        authenticated_requests_per_minute: int = 600,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.authenticated_requests_per_minute = authenticated_requests_per_minute
        self._window: float = 60.0
        self._requests: OrderedDict[str, deque[float]] = OrderedDict()
        self._max_clients = 10_000
        self._lock = Lock()
        RateLimitMiddleware._instances.append(self)

    @classmethod
    def reset_all(cls) -> None:
        """Reset in-memory rate limits across all middleware instances (for test isolation)."""
        for inst in cls._instances:
            with inst._lock:
                inst._requests.clear()

    async def dispatch(self, request: Request, call_next):
        client_ip: str = request.client.host if request.client else "unknown"
        now = time.monotonic()
        is_auth = request.url.path.rstrip("/").lower() in {"/auth/login", "/login"}
        token_subject = None
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            payload = AuthService.verify_token(token)
            subject = payload.get("sub") if payload else None
            if isinstance(subject, str) and subject:
                token_subject = subject

        if is_auth:
            bucket_key = f"ip:{client_ip}"
            limit = min(self.requests_per_minute, 10)
        elif token_subject:
            # Authenticated users need a separate budget so one busy browser or a
            # shared proxy IP cannot throttle every dashboard user at once.
            bucket_key = f"user:{token_subject}"
            limit = self.authenticated_requests_per_minute
        else:
            bucket_key = f"ip:{client_ip}"
            limit = self.requests_per_minute
        with self._lock:
            timestamps = self._requests.pop(bucket_key, deque())
            while timestamps and now - timestamps[0] >= self._window:
                timestamps.popleft()
            if len(self._requests) >= self._max_clients and bucket_key not in self._requests:
                self._requests.popitem(last=False)
            blocked = len(timestamps) >= limit
            if not blocked:
                timestamps.append(now)
            self._requests[bucket_key] = timestamps
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

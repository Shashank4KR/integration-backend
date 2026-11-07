import json
from datetime import UTC, datetime, timezone
from typing import Any, Generic, TypeVar

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_request_id

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: dict[str, Any] | None = None
    message: str | None = None
    errors: list[str] | None = None
    meta: dict[str, Any] | None = None


def success_response(
    data: Any = None,
    message: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict:
    resolved_meta = {
        "timestamp": datetime.now(UTC).isoformat(),
        "requestId": get_request_id(),
    }
    if meta:
        resolved_meta.update(meta)
    encoded_data = jsonable_encoder(data)
    payload: dict[str, Any] = {
        "success": True,
        "data": encoded_data,
        "error": None,
        "message": message,
        "meta": resolved_meta,
    }
    if isinstance(encoded_data, dict):
        for k, v in encoded_data.items():
            if k not in payload:
                payload[k] = v
    return payload


class APIException(HTTPException):
    def __init__(self, status_code: int, message: str, errors: list[str] | None = None):
        super().__init__(status_code=status_code, detail=message)
        self.errors = errors


def _format_validation_errors(exc: RequestValidationError) -> list[str]:
    return [
        f"{'.'.join(str(p) for p in err['loc'][1:])}: {err['msg']}"
        for err in exc.errors()
    ]


def _error_response(
    request: Request,
    status_code: int,
    message: str,
    errors: list[str] | None = None,
) -> JSONResponse:
    meta = {
        "timestamp": datetime.now(UTC).isoformat(),
        "requestId": get_request_id(),
    }
    error_payload = {
        "message": message,
        "code": status_code,
        "details": errors or [],
    }
    payload: dict[str, Any] = {
        "success": False,
        "data": None,
        "error": error_payload,
        "message": message,
        "detail": message,
        "errors": errors or [],
        "meta": meta,
    }
    return JSONResponse(
        status_code=status_code,
        content=payload,
    )


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a unified response envelope across all JSON endpoints:
    {
        "success": bool,
        "data": ...,
        "error": null | { "message": str, "code": int, "details": [...] },
        "meta": { "timestamp": str, "requestId": str }
    }
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Do not wrap OpenAPI docs, health probes, or binary/static files
        path = request.url.path
        if (
            path in {"/docs", "/redoc", "/openapi.json", "/health", "/ready", "/api/v1/health", "/api/v1/ready"}
            or path.startswith("/docs/")
            or path.startswith("/chapter-notes/files/")
        ):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Read the body
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        if not body_bytes:
            return response

        try:
            body = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Check if already enveloped
        if isinstance(body, dict) and "success" in body and "data" in body and "meta" in body:
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        req_id = get_request_id()
        now_iso = datetime.now(UTC).isoformat()
        meta = {
            "timestamp": now_iso,
            "requestId": req_id,
        }

        if response.status_code < 400:
            if isinstance(body, dict):
                enveloped = {
                    **body,
                    "success": True,
                    "data": body,
                    "error": None,
                    "meta": meta,
                }
            else:
                enveloped = {
                    "success": True,
                    "data": body,
                    "error": None,
                    "meta": meta,
                }
        else:
            msg = "An error occurred"
            details = None
            if isinstance(body, dict):
                msg = body.get("message") or body.get("detail") or msg
                details = body.get("errors") or body.get("details")
            enveloped = {
                **(body if isinstance(body, dict) else {}),
                "success": False,
                "data": None,
                "error": {
                    "message": str(msg),
                    "code": response.status_code,
                    "details": details or [],
                },
                "meta": meta,
            }

        new_bytes = json.dumps(enveloped, default=str).encode("utf-8")
        headers = dict(response.headers)
        headers["content-length"] = str(len(new_bytes))
        headers["x-request-id"] = req_id
        return Response(
            content=new_bytes,
            status_code=response.status_code,
            headers=headers,
            media_type="application/json",
        )


def register_exception_handlers(app: Any) -> None:
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return _error_response(
            request, exc.status_code, str(exc.detail), getattr(exc, "errors", None)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return _error_response(request, exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Request validation failed",
            _format_validation_errors(exc),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return _error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred",
        )

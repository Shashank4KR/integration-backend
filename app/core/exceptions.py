from typing import Any, Generic, TypeVar

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    errors: list[str] | None = None


def success_response(data: Any = None, message: str | None = None) -> dict:
    return {
        "success": True,
        "data": jsonable_encoder(data),
        "message": message,
    }


class APIException(HTTPException):
    def __init__(self, status_code: int, message: str, errors: list[str] | None = None):
        super().__init__(status_code=status_code, detail=message)
        self.errors = errors


def _format_validation_errors(exc: RequestValidationError) -> list[str]:
    return [
        f"{'.'.join(str(p) for p in err['loc'][1:])}: {err['msg']}"
        for err in exc.errors()
    ]


def _error_response(request: Request, status_code: int, message: str, errors: list[str] | None = None) -> JSONResponse:
    payload = jsonable_encoder(
        APIResponse(
            success=False,
            data=None,
            message=message,
            errors=errors,
        )
    )
    # Keep the envelope for clients that use it while exposing FastAPI's
    # conventional `detail` field for existing frontend service clients.
    payload["detail"] = message
    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers={"X-Error": message},
    )


def register_exception_handlers(app: Any) -> None:
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return _error_response(request, exc.status_code, str(exc.detail), getattr(exc, "errors", None))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return _error_response(request, exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
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

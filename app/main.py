from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import RateLimitMiddleware
from app.services.audit_service import audit_log_service
from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Auth Service API",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


@app.middleware("http")
async def audit_business_actions(request, call_next):
    response = await call_next(request)
    if response.status_code >= 400 or request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return response
    if request.url.path.startswith(("/login", "/logout", "/audit", "/login-history", "/audit-logs")):
        return response
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return response
    payload = AuthService.verify_token(authorization.split(" ", 1)[1])
    try:
        user_id = UUID(payload["sub"]) if payload else None
    except (KeyError, ValueError, TypeError):
        user_id = None
    if user_id is None:
        return response
    activity = {
        "POST": "Create Record",
        "PUT": "Update Record",
        "PATCH": "Update Record",
        "DELETE": "Delete Record",
    }[request.method]
    path = request.url.path.lower()
    if "approve" in path and "leave" in path:
        activity = "Approve Leave"
    elif "reject" in path and "leave" in path:
        activity = "Reject Leave"
    elif path.startswith("/payments") and request.method == "POST":
        activity = "Fee Payment"
    elif "issue" in path and "book" in path and request.method == "POST":
        activity = "Book Issue"
    elif "return" in path and "book" in path:
        activity = "Book Return"
    elif "reservation" in path and "library" in path and request.method == "POST":
        activity = "Reservation Created"
    elif "approve" in path and "reservation" in path:
        activity = "Reservation Approved"
    elif "reject" in path and "reservation" in path:
        activity = "Reservation Rejected"
    elif "pay-fine" in path:
        activity = "Fine Payment"
    elif "approve" in path and "admission" in path:
        activity = "Admission Approval"
    try:
        async with AsyncSessionLocal() as audit_session:
            await audit_log_service.create_log(
                audit_session,
                {
                    "user_id": user_id,
                    "activity": activity,
                    "details": f"{request.method} {request.url.path}",
                },
            )
    except Exception:
        # Auditing must never turn a completed business action into a failed response.
        pass
    return response


# Mount all modular v1 routers
app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}

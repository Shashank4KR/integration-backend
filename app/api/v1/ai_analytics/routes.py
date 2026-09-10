from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_analytics_schema import AIAnalyticsResponse, AIChatHistoryCreate, AIChatHistoryResponse
from app.services.ai_analytics_service import ai_analytics_service, ai_chat_history_service

ai_analytics_router = APIRouter()
ai_chat_history_router = APIRouter()
user_chat_history_router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@ai_analytics_router.post("/generate-all", response_model=list[AIAnalyticsResponse], status_code=status.HTTP_201_CREATED)
async def generate_all(session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await ai_analytics_service.generate_all_student_analytics(session)


@ai_analytics_router.post("/generate/{student_id}", response_model=AIAnalyticsResponse, status_code=status.HTTP_201_CREATED)
async def generate_student(student_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    return await ai_analytics_service.generate_student_analytics(session, student_id)


@ai_analytics_router.get("/high-risk-students")
async def high_risk_students(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_analytics_service.high_risk_students(session)


@ai_analytics_router.get("/dashboard")
async def dashboard(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_analytics_service.dashboard(session)


@ai_analytics_router.get("", response_model=list[AIAnalyticsResponse])
async def list_analytics(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_analytics_service.get_all_analytics(session)


@ai_analytics_router.get("/{analytics_id}", response_model=AIAnalyticsResponse)
async def get_analytics(analytics_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_analytics_service.get_analytics(session, analytics_id)


@ai_analytics_router.delete("/{analytics_id}")
async def delete_analytics(analytics_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await ai_analytics_service.delete_analytics(session, analytics_id)
    return {"message": "Deleted successfully"}


@ai_chat_history_router.post("", response_model=AIChatHistoryResponse, status_code=status.HTTP_201_CREATED)
async def save_chat(payload: AIChatHistoryCreate, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_chat_history_service.save_chat(session, payload.model_dump())


@ai_chat_history_router.get("", response_model=list[AIChatHistoryResponse])
async def list_chat_history(session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_chat_history_service.get_all_chat_history(session)


@ai_chat_history_router.get("/{chat_id}", response_model=AIChatHistoryResponse)
async def get_chat_history(chat_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_chat_history_service.get_chat_history(session, chat_id)


@ai_chat_history_router.delete("/{chat_id}")
async def delete_chat_history(chat_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin(current_user)
    await ai_chat_history_service.delete_chat(session, chat_id)
    return {"message": "Deleted successfully"}


@user_chat_history_router.get("/{user_id}/chat-history", response_model=list[AIChatHistoryResponse])
async def user_chat_history(user_id: UUID, session: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await ai_chat_history_service.get_user_chat_history(session, user_id)

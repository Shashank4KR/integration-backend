from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.settings_schema import (
    CategorySettingsUpdate,
    SettingsCategoryResponse,
)
from app.services.settings_service import settings_service

settings_router = APIRouter()


def _ensure_admin_or_privileged(user: User) -> None:
    allowed_roles = {"ADMIN", "SUPERADMIN"}
    role_name = user.role.role_name if user.role else ""
    if role_name.upper() not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify system settings.",
        )


@settings_router.get("", response_model=dict[str, Any])
async def get_all_settings(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await settings_service.get_all_settings(session)


@settings_router.put("", response_model=dict[str, Any])
async def update_all_settings(
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    _ensure_admin_or_privileged(current_user)
    # Check if payload has a top level 'settings' key or is directly a dict of categories
    settings_dict = payload.get("settings", payload)
    return await settings_service.bulk_update_settings(session, settings_dict)


@settings_router.get("/{category}", response_model=dict[str, Any])
async def get_category_settings(
    category: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await settings_service.get_category_settings(session, category)


@settings_router.put("/{category}", response_model=SettingsCategoryResponse)
async def update_category_settings(
    category: str,
    payload: CategorySettingsUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    _ensure_admin_or_privileged(current_user)
    return await settings_service.update_category_settings(
        session, category, payload.config
    )

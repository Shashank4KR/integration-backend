from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.user import User
from app.schemas.parent_student_schema import (
    ParentStudentCreate,
    ParentStudentResponse,
    ParentStudentUpdate,
)
from app.schemas.student_schema import StudentResponse
from app.services.parent_student_service import parent_student_service

router = build_crud_router(
    parent_student_service,
    ParentStudentCreate,
    ParentStudentUpdate,
    ParentStudentResponse,
)


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@router.post("", response_model=ParentStudentResponse, status_code=status.HTTP_201_CREATED)
async def create_parent_student(
    payload: ParentStudentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await parent_student_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=ParentStudentResponse)
async def update_parent_student(
    item_id: UUID,
    payload: ParentStudentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await parent_student_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_parent_student(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await parent_student_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/parent/{parent_id}/students", response_model=list[StudentResponse])
async def get_students_by_parent(
    parent_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name == "PARENT":
        parent_result = await session.execute(
            select(ParentStudent).where(ParentStudent.parent_id == parent_id)
        )
        parent_students = parent_result.scalars().all()
        if not any(ps.parent_id == parent_id for ps in parent_students):
            if str(current_user.id) != str(parent_id):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own children",
                )
    result = await session.execute(
        select(Student)
        .join(ParentStudent, ParentStudent.student_id == Student.id)
        .where(ParentStudent.parent_id == parent_id)
    )
    return result.scalars().all()

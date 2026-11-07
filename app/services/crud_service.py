from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_model import Class
from app.models.department_model import Department
from app.models.parent_model import Parent
from app.models.student_model import Student
from app.models.subject_model import Subject
from app.models.teacher_model import Teacher
from app.models.user import User
from app.repositories.crud_repository import CRUDRepository


class CRUDService:
    def __init__(
        self,
        repository: CRUDRepository,
        entity_name: str,
        unique_fields: tuple[str, ...] = (),
        unique_constraints: tuple[tuple[str, ...], ...] = (),
        foreign_keys: dict[str, type] | None = None,
    ):
        self.repository = repository
        self.entity_name = entity_name
        self.unique_fields = unique_fields
        self.unique_constraints = unique_constraints
        self.foreign_keys = foreign_keys or {}

    async def create(self, session: AsyncSession, data: dict[str, Any]) -> Any:
        await self._validate_foreign_keys(session, data)
        await self._validate_unique(session, data)
        item = await self.repository.create(session, data)
        await session.commit()
        return item

    async def list(
        self, session: AsyncSession, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        return await self.repository.list(session, limit=limit, offset=offset)

    async def get(self, session: AsyncSession, item_id: UUID) -> Any:
        item = await self.repository.get(session, item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name} not found",
            )
        return item

    async def update(
        self, session: AsyncSession, item_id: UUID, data: dict[str, Any]
    ) -> Any:
        item = await self.get(session, item_id)
        await self._validate_foreign_keys(session, data)
        await self._validate_unique(session, data, exclude_id=item_id)
        item = await self.repository.update(session, item, data)
        await session.commit()
        return item

    async def delete(self, session: AsyncSession, item_id: UUID) -> None:
        item = await self.get(session, item_id)
        await self.repository.delete(session, item)
        await session.commit()

    async def _validate_unique(
        self,
        session: AsyncSession,
        data: dict[str, Any],
        exclude_id: UUID | None = None,
    ) -> None:
        for field in self.unique_fields:
            value = data.get(field)
            if value is None:
                continue
            existing = await self.repository.get_by_field(
                session, field, value, exclude_id=exclude_id
            )
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{field} already exists",
                )
        for fields in self.unique_constraints:
            if not all(field in data and data[field] is not None for field in fields):
                continue
            values = {field: data[field] for field in fields}
            existing = await self.repository.get_by_fields(
                session, values, exclude_id=exclude_id
            )
            if existing is not None:
                joined_fields = ", ".join(fields)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{self.entity_name} with this {joined_fields} already exists",
                )

    async def _validate_foreign_keys(
        self, session: AsyncSession, data: dict[str, Any]
    ) -> None:
        for field, model in self.foreign_keys.items():
            value = data.get(field)
            if value is None:
                continue
            result = await session.get(model, value)
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{field} does not reference an existing record",
                )


USER_FK = {"user_id": User}
STUDENT_FKS = {"user_id": User, "class_id": Class}
TEACHER_FKS = {"user_id": User, "department_id": Department}
PARENT_STUDENT_FKS = {"parent_id": Parent, "student_id": Student}
CLASS_FKS = {"class_teacher_id": Teacher}
CLASS_SUBJECT_FKS = {"class_id": Class, "subject_id": Subject}
TEACHER_SUBJECT_FKS = {"teacher_id": Teacher, "subject_id": Subject, "class_id": Class}
TIMETABLE_FKS = {"teacher_id": Teacher, "subject_id": Subject, "class_id": Class}

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.class_subject_schema import ClassSubjectCreate, ClassSubjectResponse
from app.services.class_subject_service import class_subject_service

router = APIRouter()


@router.post("", response_model=ClassSubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_class_subject(
    payload: ClassSubjectCreate, session: AsyncSession = Depends(get_db)
):
    return await class_subject_service.create(session, payload.model_dump())


@router.get("", response_model=list[ClassSubjectResponse])
async def list_class_subjects(session: AsyncSession = Depends(get_db)):
    return await class_subject_service.list(session)


@router.get("/{item_id}", response_model=ClassSubjectResponse)
async def get_class_subject(item_id: UUID, session: AsyncSession = Depends(get_db)):
    return await class_subject_service.get(session, item_id)


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_class_subject(item_id: UUID, session: AsyncSession = Depends(get_db)):
    await class_subject_service.delete(session, item_id)
    return {"message": "Deleted successfully"}

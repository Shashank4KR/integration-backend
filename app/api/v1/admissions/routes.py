from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.admission_schema import (
    AdmissionApplicationCreate,
    AdmissionApplicationResponse,
    AdmissionApplicationUpdate,
    AdmissionDocumentCreate,
    AdmissionDocumentResponse,
    AdmissionDocumentUpdate,
    AdmissionDocumentVerify,
    AdmissionSummaryResponse,
)
from app.services.admission_service import (
    admission_application_service,
    admission_document_service,
)

application_router = APIRouter()
document_router = APIRouter()


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@application_router.post(
    "", response_model=AdmissionApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def create_application(
    payload: AdmissionApplicationCreate, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admission_application_service.create_application(
        session, payload.model_dump()
    )


@application_router.get("", response_model=list[AdmissionApplicationResponse])
async def get_applications(session: AsyncSession = Depends(get_db)):
    return await admission_application_service.get_applications(session)


@application_router.get("/summary", response_model=AdmissionSummaryResponse)
async def get_admission_summary(session: AsyncSession = Depends(get_db)):
    return await admission_application_service.get_summary(session)


@application_router.get(
    "/status/{status_value}", response_model=list[AdmissionApplicationResponse]
)
async def get_applications_by_status(
    status_value: str, session: AsyncSession = Depends(get_db),
):
    return await admission_application_service.get_by_status(session, status_value)


@application_router.get(
    "/{application_id}/documents", response_model=list[AdmissionDocumentResponse]
)
async def get_application_documents(
    application_id: UUID, session: AsyncSession = Depends(get_db),
):
    return await admission_document_service.get_by_application(session, application_id)


@application_router.post(
    "/{application_id}/approve", response_model=AdmissionApplicationResponse
)
async def approve_application(
    application_id: UUID, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admission_application_service.approve_application(
        session, application_id
    )


@application_router.get("/{application_id}", response_model=AdmissionApplicationResponse)
async def get_application(
    application_id: UUID, session: AsyncSession = Depends(get_db),
):
    return await admission_application_service.get_application(session, application_id)


@application_router.put("/{application_id}", response_model=AdmissionApplicationResponse)
async def update_application(
    application_id: UUID,
    payload: AdmissionApplicationUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admission_application_service.update_application(
        session, application_id, payload.model_dump(exclude_unset=True)
    )


@application_router.delete("/{application_id}", status_code=status.HTTP_200_OK)
async def delete_application(
    application_id: UUID, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await admission_application_service.delete_application(session, application_id)
    return {"message": "Deleted successfully"}


@document_router.post(
    "", response_model=AdmissionDocumentResponse, status_code=status.HTTP_201_CREATED
)
async def create_document(
    payload: AdmissionDocumentCreate, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admission_document_service.create_document(
        session, payload.model_dump()
    )


@document_router.get("", response_model=list[AdmissionDocumentResponse])
async def get_documents(session: AsyncSession = Depends(get_db)):
    return await admission_document_service.get_documents(session)


@document_router.patch("/{document_id}/verify", response_model=AdmissionDocumentResponse)
async def verify_document(
    document_id: UUID,
    payload: AdmissionDocumentVerify,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admission_document_service.verify_document(
        session, document_id, payload.model_dump()
    )


@document_router.get("/{document_id}", response_model=AdmissionDocumentResponse)
async def get_document(document_id: UUID, session: AsyncSession = Depends(get_db)):
    return await admission_document_service.get_document(session, document_id)


@document_router.put("/{document_id}", response_model=AdmissionDocumentResponse)
async def update_document(
    document_id: UUID,
    payload: AdmissionDocumentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await admission_document_service.update_document(
        session, document_id, payload.model_dump(exclude_unset=True)
    )


@document_router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: UUID, session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await admission_document_service.delete_document(session, document_id)
    return {"message": "Deleted successfully"}

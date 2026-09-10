from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.v1.auth.routes import get_current_user
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.user import User
from app.schemas.fee_schema import FeeInvoiceCreate, FeeInvoiceResponse, FeeInvoiceUpdate, FeeStructureCreate, FeeStructureResponse, FeeStructureUpdate, FeeSummaryResponse, PaymentCreate, PaymentResponse, PaymentUpdate
from app.services.fee_service import fee_invoice_service, fee_structure_service, payment_service

def _ensure_admin_or_accountant(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "ACCOUNTANT"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or accountant users can perform this action",
        )


async def _ensure_student_fee_access(
    session: AsyncSession,
    current_user: User,
    student_id: UUID,
) -> None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name in ("ADMIN", "ACCOUNTANT"):
        return
    if role_name == "STUDENT":
        result = await session.execute(
            select(Student).where(Student.id == student_id, Student.user_id == current_user.id)
        )
        if result.scalar_one_or_none() is not None:
            return
    if role_name == "PARENT":
        result = await session.execute(
            select(ParentStudent)
            .join(Parent, Parent.id == ParentStudent.parent_id)
            .where(Parent.user_id == current_user.id, ParentStudent.student_id == student_id)
        )
        if result.scalar_one_or_none() is not None:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this student's fees",
    )

accountant_fee_router = APIRouter()

@accountant_fee_router.get("/summary", response_model=dict)
async def get_fee_summary(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    from app.models.fee_model import FeeInvoice, Payment
    total_invoiced = await session.scalar(select(func.coalesce(func.sum(FeeInvoice.amount), 0))) or 0
    total_paid = await session.scalar(select(func.coalesce(func.sum(Payment.amount_paid), 0))) or 0
    pending = total_invoiced - total_paid
    total_students = await session.scalar(select(func.count(FeeInvoice.student_id))) or 0
    return {
        "total_invoiced": float(total_invoiced),
        "total_paid": float(total_paid),
        "pending_amount": float(pending),
        "total_students": total_students,
    }

fee_structure_router = APIRouter()
@fee_structure_router.post("", response_model=FeeStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_structure(payload: FeeStructureCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    return await fee_structure_service.create(session, payload.model_dump())
@fee_structure_router.get("", response_model=list[FeeStructureResponse])
async def list_fee_structures(session: AsyncSession = Depends(get_db)): return await fee_structure_service.list(session)
@fee_structure_router.get("/{item_id}", response_model=FeeStructureResponse)
async def get_fee_structure(item_id: UUID, session: AsyncSession = Depends(get_db)): return await fee_structure_service.get(session, item_id)
@fee_structure_router.put("/{item_id}", response_model=FeeStructureResponse)
async def update_fee_structure(item_id: UUID, payload: FeeStructureUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    return await fee_structure_service.update(session, item_id, payload.model_dump(exclude_unset=True))
@fee_structure_router.delete("/{item_id}")
async def delete_fee_structure(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    await fee_structure_service.delete(session, item_id); return {"message": "Deleted successfully"}

fee_invoice_router = APIRouter()
@fee_invoice_router.post("", response_model=FeeInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_invoice(payload: FeeInvoiceCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    return await fee_invoice_service.create(session, payload.model_dump())
@fee_invoice_router.get("", response_model=list[FeeInvoiceResponse])
async def list_fee_invoices(session: AsyncSession = Depends(get_db)): return await fee_invoice_service.list(session)
@fee_invoice_router.get("/{item_id}", response_model=FeeInvoiceResponse)
async def get_fee_invoice(item_id: UUID, session: AsyncSession = Depends(get_db)): return await fee_invoice_service.get(session, item_id)
@fee_invoice_router.put("/{item_id}", response_model=FeeInvoiceResponse)
async def update_fee_invoice(item_id: UUID, payload: FeeInvoiceUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    return await fee_invoice_service.update(session, item_id, payload.model_dump(exclude_unset=True))
@fee_invoice_router.delete("/{item_id}")
async def delete_fee_invoice(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    await fee_invoice_service.delete(session, item_id); return {"message": "Deleted successfully"}
@fee_invoice_router.get("/{invoice_id}/payments", response_model=list[PaymentResponse])
async def invoice_payments(invoice_id: UUID, session: AsyncSession = Depends(get_db)): return await payment_service.get_by_invoice(session, invoice_id)

payment_router = APIRouter()
@payment_router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payload: PaymentCreate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    return await payment_service.create(session, payload.model_dump())
@payment_router.get("", response_model=list[PaymentResponse])
async def list_payments(session: AsyncSession = Depends(get_db)): return await payment_service.list(session)
@payment_router.get("/{item_id}", response_model=PaymentResponse)
async def get_payment(item_id: UUID, session: AsyncSession = Depends(get_db)): return await payment_service.get(session, item_id)
@payment_router.put("/{item_id}", response_model=PaymentResponse)
async def update_payment(item_id: UUID, payload: PaymentUpdate, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    return await payment_service.update(session, item_id, payload.model_dump(exclude_unset=True))
@payment_router.delete("/{item_id}")
async def delete_payment(item_id: UUID, session: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_accountant(current_user)
    await payment_service.delete(session, item_id); return {"message": "Deleted successfully"}

student_fee_router = APIRouter()
@student_fee_router.get("/{student_id}/fee-invoices", response_model=list[FeeInvoiceResponse])
async def student_invoices(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_student_fee_access(session, current_user, student_id)
    return await fee_invoice_service.get_by_student(session, student_id)
@student_fee_router.get("/{student_id}/payments", response_model=list[PaymentResponse])
async def student_payments(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_student_fee_access(session, current_user, student_id)
    return await payment_service.get_by_student(session, student_id)
@student_fee_router.get("/{student_id}/outstanding-fees", response_model=list[FeeInvoiceResponse])
async def outstanding_fees(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_student_fee_access(session, current_user, student_id)
    return [invoice for invoice in await fee_invoice_service.get_by_student(session, student_id) if invoice.status != "PAID"]
@student_fee_router.get("/{student_id}/fee-summary", response_model=FeeSummaryResponse)
async def fee_summary(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _ensure_student_fee_access(session, current_user, student_id)
    return await payment_service.summary(session, student_id)

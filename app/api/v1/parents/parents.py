from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.user import User
from app.schemas.parent_schema import ParentCreate, ParentResponse, ParentUpdate
from app.schemas.student_schema import StudentResponse
from app.services.fee_service import fee_invoice_service, payment_service, _invoice_total_paid
from app.services.parent_service import parent_service

router = build_crud_router(parent_service, ParentCreate, ParentUpdate, ParentResponse)


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )


@router.post("", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_parent(
    payload: ParentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await parent_service.create(session, payload.model_dump())


@router.put("/{item_id}", response_model=ParentResponse)
async def update_parent(
    item_id: UUID,
    payload: ParentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    return await parent_service.update(session, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}")
async def delete_parent(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await parent_service.delete(session, item_id)
    return {"message": "Deleted successfully"}


@router.get("/me", response_model=ParentResponse)
async def get_current_parent(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name != "PARENT":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parent users can access this endpoint",
        )
    result = await session.execute(
        select(Parent).where(Parent.user_id == current_user.id)
    )
    parent_obj = result.scalar_one_or_none()
    if not parent_obj:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found",
        )
    return parent_obj


@router.get("/me/students", response_model=list[StudentResponse])
async def get_my_students(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name != "PARENT":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parent users can access this endpoint",
        )
    result = await session.execute(
        select(Student)
        .join(ParentStudent, ParentStudent.student_id == Student.id)
        .join(Parent, Parent.id == ParentStudent.parent_id)
        .where(Parent.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/me/fees")
async def get_my_children_fees(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name != "PARENT":
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parent users can access this endpoint",
        )
    result = await session.execute(
        select(Student)
        .join(ParentStudent, ParentStudent.student_id == Student.id)
        .join(Parent, Parent.id == ParentStudent.parent_id)
        .where(Parent.user_id == current_user.id)
    )
    children = result.scalars().all()

    children_data = []
    total_outstanding = 0.0
    for child in children:
        invoices = await fee_invoice_service.get_by_student(session, child.id)
        child_outstanding = 0.0
        invoice_list = []
        for inv in invoices:
            net = float(inv.net_amount if inv.net_amount else inv.amount)
            paid = float(await _invoice_total_paid(session, inv.id))
            balance = max(0.0, net - paid)
            if inv.status != "CANCELLED":
                child_outstanding += balance
            invoice_list.append(
                {
                    "invoice_id": str(inv.id),
                    "invoice_number": inv.invoice_number or "",
                    "amount": net,
                    "paid": paid,
                    "balance": balance,
                    "status": inv.status,
                    "due_date": str(inv.due_date) if inv.due_date else None,
                }
            )
        total_outstanding += child_outstanding
        children_data.append(
            {
                "student_id": str(child.id),
                "name": f"{child.first_name or ''} {child.last_name or ''}".strip(),
                "class": child.class_name,
                "admission_no": child.admission_no,
                "outstanding": child_outstanding,
                "invoices": invoice_list,
            }
        )

    return {
        "children": children_data,
        "total_outstanding": total_outstanding,
    }

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.student_model import Student
from app.models.class_model import Class
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.teacher_model import Teacher
from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.core.exceptions import APIException, success_response
from app.models.fee_model import (
    FeeInvoice,
    FeeStructure,
    Payment,
)
from app.models.finance_model import (
    Expense,
    ExpenseCategory,
    LateFeeRule,
    OtherIncome,
    RefundRequest,
    StudentCategory,
    StudentFeeAssignment,
    StudentLedger,
    StudentScholarship,
    ScholarshipType,
)
from app.models.user import User
from app.repositories.fee_repository import fee_invoice_repository, payment_repository
from app.repositories.finance_repository import (
    expense_category_repository,
    expense_repository,
    fee_installment_repository,
    late_fee_rule_repository,
    other_income_repository,
    refund_request_repository,
    salary_repository,
    student_category_repository,
    student_fee_assignment_repository,
    student_ledger_repository,
    scholarship_type_repository,
    student_scholarship_repository,
)
from app.schemas.fee_schema import (
    FeeInvoiceCreate,
    FeeInvoiceResponse,
    FeeInvoiceUpdate,
    FeeInstallmentCreate,
    FeeInstallmentResponse,
    FeeInstallmentUpdate,
    FeeStructureCreate,
    FeeStructureResponse,
    FeeStructureUpdate,
    FeeSummaryResponse,
    PaymentCreate,
    PaymentResponse,
    PaymentUpdate,
    StudentFeeAssignmentCreate,
    StudentFeeAssignmentResponse,
    StudentFeeAssignmentUpdate,
    StudentLedgerResponse,
    StudentLedgerSummaryResponse,
)
from app.schemas.finance_schema import (
    AdminDashboardResponse,
    ExpenseCategoryCreate,
    ExpenseCategoryResponse,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    FinanceOverviewResponse,
    FinanceTransaction,
    FinanceTransactionListResponse,
    InvoiceResponse,
    LateFeeRuleCreate,
    LateFeeRuleResponse,
    LateFeeRuleUpdate,
    OtherIncomeCreate,
    OtherIncomeResponse,
    OtherIncomeUpdate,
    ParentDashboardResponse,
    ReceiptResponse,
    RefundRequestCreate,
    RefundRequestResponse,
    RefundRequestUpdate,
    ReportPaginationParams,
    ScholarshipTypeCreate,
    ScholarshipTypeResponse,
    ScholarshipTypeUpdate,
    StudentCategoryCreate,
    StudentCategoryResponse,
    StudentCategoryUpdate,
    StudentDashboardResponse,
    StudentScholarshipCreate,
    SalaryCreate,
    StudentScholarshipResponse,
    StudentScholarshipUpdate,
)
from app.services.fee_service import (
    _invoice_total_paid,
    fee_invoice_service,
    fee_structure_service,
    payment_service,
    refund_service,
    student_scholarship_service,
    late_fee_rule_service,
)
from app.services.finance_service import (
    expense_category_service,
    fee_installment_service,
    finance_service,
    other_income_service,
    salary_service,
    student_category_service,
    student_ledger_service,
    scholarship_type_service,
    student_fee_assignment_service,
)
from app.repositories.finance_repository import (
    student_fee_assignment_repository,
    student_ledger_repository,
)


def _ensure_admin_or_accountant(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "ACCOUNTANT"):
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Only admin or accountant users can perform this action",
        )


def _ensure_admin(current_user: User) -> None:
    if current_user.role.role_name != "ADMIN":
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Only admin users can perform this action",
        )


finance_router = APIRouter()


@finance_router.get("/overview")
async def get_finance_overview(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_finance_overview(session)
    return success_response(data)


@finance_router.get("/transactions")
async def list_transactions(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await finance_service.get_transactions(session)
    return success_response({"items": items, "total": len(items)})


@finance_router.get("/expenses")
async def list_expenses(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await finance_service.get_expenses(session)
    return success_response(items)


@finance_router.post("/expenses", status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await finance_service.create_expense(session, payload.model_dump())
    return success_response(item, message="Expense created successfully")


@finance_router.get("/expenses/{item_id}")
async def get_expense(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await finance_service.get_expense(session, item_id)
    return success_response(item)


@finance_router.put("/expenses/{item_id}")
async def update_expense(
    item_id: UUID,
    payload: ExpenseUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await finance_service.get_expense(session, item_id)
    from app.services.crud_service import CRUDService
    crud = CRUDService(expense_repository, "Expense")
    updated = await crud.update(session, item_id, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(updated)
    return success_response(updated, message="Expense updated successfully")


@finance_router.delete("/expenses/{item_id}")
async def delete_expense(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await finance_service.get_expense(session, item_id)
    from app.services.crud_service import CRUDService
    crud = CRUDService(expense_repository, "Expense")
    await crud.delete(session, item_id)
    return success_response(message="Expense deleted successfully")


@finance_router.get("/salary")
async def list_salary_records(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    items = await finance_service.get_salaries(session)
    return success_response(items)


@finance_router.post("/salary", status_code=status.HTTP_201_CREATED)
async def process_salary(
    payload: SalaryCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await finance_service.create_salary(session, payload.model_dump())
    return success_response(item, message="Salary processed successfully")


# Fee structures
@finance_router.get("/fee-structures")
async def list_fee_structures(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await fee_structure_service.list(session)
    return success_response(items)


@finance_router.get("/fee-structures/{item_id}")
async def get_fee_structure(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await fee_structure_service.get(session, item_id)
    return success_response(item)


@finance_router.post("/fee-structures", status_code=status.HTTP_201_CREATED)
async def create_fee_structure(
    payload: FeeStructureCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await fee_structure_service.create(session, payload.model_dump())
    return success_response(item, message="Fee structure created successfully")


@finance_router.put("/fee-structures/{item_id}")
async def update_fee_structure(
    item_id: UUID,
    payload: FeeStructureUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await fee_structure_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Fee structure updated successfully")


@finance_router.delete("/fee-structures/{item_id}")
async def delete_fee_structure(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    await fee_structure_service.delete(session, item_id)
    return success_response(message="Fee structure deleted successfully")


# Invoices
@finance_router.get("/invoices")
async def list_invoices(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = (current_user.role.role_name if current_user.role else "STUDENT").upper()
    if role in ("ADMIN", "SUPER_ADMIN", "ACCOUNTANT"):
        items = await fee_invoice_service.list(session)
    elif role == "STUDENT":
        stud_res = await session.execute(select(Student).where(Student.user_id == current_user.id))
        stud = stud_res.scalar_one_or_none()
        if not stud:
            return success_response([])
        items = await fee_invoice_service.get_by_student(session, stud.id)
    elif role == "PARENT":
        parent_res = await session.execute(select(Parent).where(Parent.user_id == current_user.id))
        parent = parent_res.scalar_one_or_none()
        if not parent:
            return success_response([])
        children_res = await session.execute(
            select(Student.id).join(ParentStudent, ParentStudent.student_id == Student.id).where(ParentStudent.parent_id == parent.id)
        )
        child_ids = children_res.scalars().all()
        if not child_ids:
            return success_response([])
        items_res = await session.execute(select(FeeInvoice).where(FeeInvoice.student_id.in_(child_ids)))
        items = items_res.scalars().all()
    elif role == "TEACHER":
        teacher_res = await session.execute(select(Teacher).where(Teacher.user_id == current_user.id))
        teacher = teacher_res.scalar_one_or_none()
        if not teacher:
            return success_response([])
        classes_res = await session.execute(select(Class.id).where(Class.class_teacher_id == teacher.id))
        class_ids = classes_res.scalars().all()
        if not class_ids:
            return success_response([])
        students_res = await session.execute(select(Student.id).where(Student.class_id.in_(class_ids)))
        student_ids = students_res.scalars().all()
        if not student_ids:
            return success_response([])
        items_res = await session.execute(select(FeeInvoice).where(FeeInvoice.student_id.in_(student_ids)))
        items = items_res.scalars().all()
    else:
        items = []

    result = []
    for item in items:
        total_paid = float(await _invoice_total_paid(session, item.id))
        net = float(item.net_amount if item.net_amount is not None else item.amount)
        bal = max(0.0, net - total_paid)
        student = await session.get(Student, item.student_id)
        student_name = f"{student.first_name or ''} {student.last_name or ''}".strip() if student else "Student"
        student_adm = student.admission_no if student else str(item.student_id)
        fee_struct = await session.get(FeeStructure, item.fee_type_id)
        fee_type_name = fee_struct.fee_type if fee_struct else "Fee Invoice"

        class_grade = ""
        if student:
            if student.class_name:
                class_grade = student.class_name
            elif student.class_id:
                cls_obj = await session.get(Class, student.class_id)
                if cls_obj:
                    class_grade = f"{cls_obj.class_name} - {cls_obj.section}".strip()
            elif student.class_:
                class_grade = f"{student.class_.class_name} - {student.class_.section}".strip()
        if not class_grade and fee_struct:
            if fee_struct.class_id:
                cls_obj = await session.get(Class, fee_struct.class_id)
                if cls_obj:
                    class_grade = f"{cls_obj.class_name} - {cls_obj.section}".strip()
            elif fee_struct.section:
                class_grade = fee_struct.section
        if not class_grade:
            class_grade = "General"

        result.append({
            "id": str(item.id),
            "invoice_number": item.invoice_number,
            "invoice_date": str(item.invoice_date),
            "due_date": str(item.due_date),
            "amount": float(item.amount),
            "net_amount": net,
            "paid": total_paid,
            "balance": bal,
            "status": item.status,
            "student_id": student_adm,
            "student_name": student_name,
            "class_grade": class_grade,
            "fee_type_id": str(item.fee_type_id),
            "fee_type": fee_type_name,
        })
    return success_response(result)


@finance_router.get("/invoices/{item_id}")
async def get_invoice(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await fee_invoice_service.get(session, item_id)
    role = (current_user.role.role_name if current_user.role else "STUDENT").upper()
    if role not in ("ADMIN", "SUPER_ADMIN", "ACCOUNTANT"):
        # verify student / parent ownership
        if role == "STUDENT":
            stud_res = await session.execute(select(Student).where(Student.user_id == current_user.id))
            stud = stud_res.scalar_one_or_none()
            if not stud or item.student_id != stud.id:
                raise APIException(status_code=status.HTTP_403_FORBIDDEN, message="Not authorized to view this invoice")
        elif role == "PARENT":
            parent_res = await session.execute(select(Parent).where(Parent.user_id == current_user.id))
            parent = parent_res.scalar_one_or_none()
            if not parent:
                raise APIException(status_code=status.HTTP_403_FORBIDDEN, message="Not authorized to view this invoice")
            rel_res = await session.execute(
                select(ParentStudent).where(ParentStudent.parent_id == parent.id, ParentStudent.student_id == item.student_id)
            )
            if not rel_res.scalar_one_or_none():
                raise APIException(status_code=status.HTTP_403_FORBIDDEN, message="Not authorized to view this invoice")

    total_paid = float(await _invoice_total_paid(session, item.id))
    net = float(item.net_amount if item.net_amount is not None else item.amount)
    bal = max(0.0, net - total_paid)
    student = await session.get(Student, item.student_id)
    student_name = f"{student.first_name or ''} {student.last_name or ''}".strip() if student else "Student"
    student_adm = student.admission_no if student else str(item.student_id)
    fee_struct = await session.get(FeeStructure, item.fee_type_id)
    fee_type_name = fee_struct.fee_type if fee_struct else "Fee Invoice"

    class_grade = ""
    if student:
        if student.class_name:
            class_grade = student.class_name
        elif student.class_id:
            cls_obj = await session.get(Class, student.class_id)
            if cls_obj:
                class_grade = f"{cls_obj.class_name} - {cls_obj.section}".strip()
        elif student.class_:
            class_grade = f"{student.class_.class_name} - {student.class_.section}".strip()
    if not class_grade and fee_struct:
        if fee_struct.class_id:
            cls_obj = await session.get(Class, fee_struct.class_id)
            if cls_obj:
                class_grade = f"{cls_obj.class_name} - {cls_obj.section}".strip()
        elif fee_struct.section:
            class_grade = fee_struct.section
    if not class_grade:
        class_grade = "General"

    return success_response({
        "id": str(item.id),
        "invoice_number": item.invoice_number,
        "invoice_date": str(item.invoice_date),
        "due_date": str(item.due_date),
        "amount": float(item.amount),
        "net_amount": net,
        "paid": total_paid,
        "balance": bal,
        "status": item.status,
        "student_id": student_adm,
        "student_name": student_name,
        "class_grade": class_grade,
        "fee_type_id": str(item.fee_type_id),
        "fee_type": fee_type_name,
    })


@finance_router.post("/invoices/generate", status_code=status.HTTP_201_CREATED)
async def generate_invoice(
    payload: FeeInvoiceCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = payload.model_dump()
    item = await fee_invoice_service.create(session, data)
    return success_response(item, message="Invoice generated successfully")


@finance_router.put("/invoices/{item_id}")
async def update_invoice(
    item_id: UUID,
    payload: FeeInvoiceUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await fee_invoice_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Invoice updated successfully")


@finance_router.delete("/invoices/{item_id}")
async def delete_invoice(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    await fee_invoice_service.delete(session, item_id)
    return success_response(message="Invoice deleted successfully")


# Payments
@finance_router.get("/payments")
async def list_payments(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await payment_service.list(session)
    return success_response(items)


@finance_router.post("/payments", status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = payload.model_dump()
    method_str = str(data.get("payment_method", "ONLINE")).upper().replace(" ", "_").replace("/", "_")
    if "UPI" in method_str:
        data["payment_method"] = "UPI"
    elif "CASH" in method_str:
        data["payment_method"] = "CASH"
    elif "CARD" in method_str:
        data["payment_method"] = "CARD"
    elif "CHEQUE" in method_str:
        data["payment_method"] = "CHEQUE"
    elif "BANK" in method_str or "NET" in method_str:
        data["payment_method"] = "BANK_TRANSFER"
    else:
        data["payment_method"] = "ONLINE"
    item = await payment_service.create(session, data)
    return success_response(item, message="Payment recorded successfully")


# Student Categories
@finance_router.get("/student-categories")
async def list_student_categories(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await student_category_service.list(session)
    return success_response(items)


@finance_router.post("/student-categories", status_code=status.HTTP_201_CREATED)
async def create_student_category(
    payload: StudentCategoryCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await student_category_service.create(session, payload.model_dump())
    return success_response(item, message="Student category created successfully")


@finance_router.get("/student-categories/{item_id}")
async def get_student_category(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await student_category_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/student-categories/{item_id}")
async def update_student_category(
    item_id: UUID,
    payload: StudentCategoryUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await student_category_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Student category updated successfully")


@finance_router.delete("/student-categories/{item_id}")
async def delete_student_category(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await student_category_service.delete(session, item_id)
    return success_response(message="Student category deleted successfully")


# Fee Installments
@finance_router.get("/fee-installments")
async def list_fee_installments(
    fee_structure_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    if fee_structure_id is not None:
        items = await fee_installment_repository.get_by_fee_structure(session, fee_structure_id)
    else:
        items = await fee_installment_service.list(session)
    return success_response(items)


@finance_router.post("/fee-installments", status_code=status.HTTP_201_CREATED)
async def create_fee_installment(
    payload: FeeInstallmentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await fee_installment_service.create(session, payload.model_dump())
    return success_response(item, message="Fee installment created successfully")


@finance_router.get("/fee-installments/{item_id}")
async def get_fee_installment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await fee_installment_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/fee-installments/{item_id}")
async def update_fee_installment(
    item_id: UUID,
    payload: FeeInstallmentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await fee_installment_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Fee installment updated successfully")


@finance_router.delete("/fee-installments/{item_id}")
async def delete_fee_installment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    await fee_installment_service.delete(session, item_id)
    return success_response(message="Fee installment deleted successfully")


# Student Fee Assignments
@finance_router.get("/student-fee-assignments")
async def list_student_fee_assignments(
    student_id: UUID | None = Query(None),
    academic_year: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    if student_id is not None:
        items = await student_fee_assignment_repository.get_by_student(session, student_id)
    else:
        items = await student_fee_assignment_service.list(session)
    return success_response(items)


@finance_router.post("/student-fee-assignments", status_code=status.HTTP_201_CREATED)
async def create_student_fee_assignment(
    payload: StudentFeeAssignmentCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await student_fee_assignment_service.create(session, payload.model_dump())
    return success_response(item, message="Student fee assignment created successfully")


@finance_router.get("/student-fee-assignments/{item_id}")
async def get_student_fee_assignment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await student_fee_assignment_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/student-fee-assignments/{item_id}")
async def update_student_fee_assignment(
    item_id: UUID,
    payload: StudentFeeAssignmentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await student_fee_assignment_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Student fee assignment updated successfully")


@finance_router.delete("/student-fee-assignments/{item_id}")
async def delete_student_fee_assignment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    await student_fee_assignment_service.delete(session, item_id)
    return success_response(message="Student fee assignment deleted successfully")


@finance_router.post("/student-fee-assignments/bulk-assign")
async def bulk_assign_fee(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    student_ids = payload.get("student_ids", [])
    fee_structure_id = payload.get("fee_structure_id")
    academic_year = payload.get("academic_year")
    due_date = payload.get("due_date")
    if not student_ids or not fee_structure_id:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="student_ids and fee_structure_id are required")
    created = []
    for sid in student_ids:
        try:
            invoices = await fee_invoice_service.assign_fee_to_student(
                session, UUID(sid), {"fee_structure_id": UUID(fee_structure_id), "academic_year": academic_year, "due_date": due_date}
            )
            created.extend(invoices)
        except Exception:
            continue
    return success_response({"created_count": len(created)}, message=f"Assigned fees to {len(created)} students")


# Student Ledgers
@finance_router.get("/ledgers/{student_id}")
async def get_student_ledger(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await student_ledger_repository.get_by_student(session, student_id)
    return success_response(items)


@finance_router.get("/ledgers/{student_id}/summary")
async def get_student_ledger_summary(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    summary = await student_ledger_repository.get_ledger_summary(session, student_id)
    return success_response(summary)


# Scholarships
@finance_router.get("/scholarship-types")
async def list_scholarship_types(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await scholarship_type_service.list(session)
    return success_response(items)


@finance_router.post("/scholarship-types", status_code=status.HTTP_201_CREATED)
async def create_scholarship_type(
    payload: ScholarshipTypeCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await scholarship_type_service.create(session, payload.model_dump())
    return success_response(item, message="Scholarship type created successfully")


@finance_router.get("/scholarships")
async def list_scholarships(
    student_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    if student_id is not None:
        items = await student_scholarship_repository.get_by_student(session, student_id)
    else:
        items = await student_scholarship_service.list(session)
    return success_response(items)


@finance_router.post("/scholarships", status_code=status.HTTP_201_CREATED)
async def create_scholarship(
    payload: StudentScholarshipCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await student_scholarship_service.create(session, payload.model_dump())
    return success_response(item, message="Scholarship assigned successfully")


@finance_router.get("/scholarships/{item_id}")
async def get_scholarship(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await student_scholarship_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/scholarships/{item_id}")
async def update_scholarship(
    item_id: UUID,
    payload: StudentScholarshipUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await student_scholarship_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Scholarship updated successfully")


@finance_router.post("/scholarships/{item_id}/approve")
async def approve_scholarship(
    item_id: UUID,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await student_scholarship_service.approve(session, item_id, {"approved_by": current_user.id, **payload})
    return success_response(item, message="Scholarship approved successfully")


@finance_router.post("/scholarships/{item_id}/reject")
async def reject_scholarship(
    item_id: UUID,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await student_scholarship_service.reject(session, item_id, payload)
    return success_response(item, message="Scholarship rejected")


# Late Fee Rules
@finance_router.get("/late-fee-rules")
async def list_late_fee_rules(
    fee_structure_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    if fee_structure_id is not None:
        items = await late_fee_rule_repository.get_by_fee_structure(session, fee_structure_id)
    else:
        items = await late_fee_rule_service.list(session)
    return success_response(items)


@finance_router.post("/late-fee-rules", status_code=status.HTTP_201_CREATED)
async def create_late_fee_rule(
    payload: LateFeeRuleCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await late_fee_rule_service.create(session, payload.model_dump())
    return success_response(item, message="Late fee rule created successfully")


@finance_router.get("/late-fee-rules/{item_id}")
async def get_late_fee_rule(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await late_fee_rule_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/late-fee-rules/{item_id}")
async def update_late_fee_rule(
    item_id: UUID,
    payload: LateFeeRuleUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await late_fee_rule_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Late fee rule updated successfully")


@finance_router.post("/late-fee-rules/apply")
async def apply_late_fees(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    applied = await late_fee_rule_service.apply_late_fees(session)
    return success_response({"applied_count": applied}, message=f"Applied late fees to {applied} invoices")


# Refunds
@finance_router.get("/refunds")
async def list_refunds(
    status: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    if status is not None:
        items = await refund_request_repository.get_by_status(session, status)
    else:
        items = await refund_service.list(session)
    return success_response(items)


@finance_router.post("/refunds", status_code=status.HTTP_201_CREATED)
async def create_refund(
    payload: RefundRequestCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await refund_service.create(session, payload.model_dump())
    return success_response(item, message="Refund request created successfully")


@finance_router.get("/refunds/{item_id}")
async def get_refund(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await refund_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/refunds/{item_id}")
async def update_refund(
    item_id: UUID,
    payload: RefundRequestUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await refund_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Refund updated successfully")


@finance_router.post("/refunds/{item_id}/approve")
async def approve_refund(
    item_id: UUID,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await refund_service.approve(session, item_id, {"approved_by": current_user.id, **payload})
    return success_response(item, message="Refund approved successfully")


@finance_router.post("/refunds/{item_id}/process")
async def process_refund(
    item_id: UUID,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await refund_service.process_refund(session, item_id, payload)
    return success_response(item, message="Refund processed successfully")


@finance_router.post("/refunds/{item_id}/reject")
async def reject_refund(
    item_id: UUID,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await refund_service.reject(session, item_id, payload)
    return success_response(item, message="Refund rejected")


# Other Income
@finance_router.get("/incomes")
async def list_incomes(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await other_income_service.list(session)
    return success_response(items)


@finance_router.post("/incomes", status_code=status.HTTP_201_CREATED)
async def create_income(
    payload: OtherIncomeCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await other_income_service.create(session, payload.model_dump())
    return success_response(item, message="Income recorded successfully")


@finance_router.get("/incomes/{item_id}")
async def get_income(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await other_income_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/incomes/{item_id}")
async def update_income(
    item_id: UUID,
    payload: OtherIncomeUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await other_income_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Income updated successfully")


@finance_router.delete("/incomes/{item_id}")
async def delete_income(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await other_income_service.delete(session, item_id)
    return success_response(message="Income deleted successfully")


# Expense Categories
@finance_router.get("/expense-categories")
async def list_expense_categories(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    items = await expense_category_service.list(session)
    return success_response(items)


@finance_router.post("/expense-categories", status_code=status.HTTP_201_CREATED)
async def create_expense_category(
    payload: ExpenseCategoryCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await expense_category_service.create(session, payload.model_dump())
    return success_response(item, message="Expense category created successfully")


@finance_router.get("/expense-categories/{item_id}")
async def get_expense_category(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = await expense_category_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/expense-categories/{item_id}")
async def update_expense_category(
    item_id: UUID,
    payload: ExpenseCategoryUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    item = await expense_category_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Expense category updated successfully")


@finance_router.delete("/expense-categories/{item_id}")
async def delete_expense_category(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    await expense_category_service.delete(session, item_id)
    return success_response(message="Expense category deleted successfully")


# Reports
@finance_router.get("/reports/daily-collection")
async def report_daily_collection(
    date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_daily_collection(session, date)
    return success_response(data)


@finance_router.get("/reports/monthly-collection")
async def report_monthly_collection(
    year: int | None = Query(None),
    month: int | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_monthly_collection(session, year, month)
    return success_response(data)


@finance_router.get("/reports/yearly-collection")
async def report_yearly_collection(
    year: int | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_yearly_collection(session, year)
    return success_response(data)


@finance_router.get("/reports/outstanding-fees")
async def report_outstanding_fees(
    class_id: UUID | None = Query(None),
    section: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_outstanding_fees(session, class_id, section)
    return success_response(data)


@finance_router.get("/reports/student-ledger")
async def report_student_ledger(
    student_id: UUID | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_student_ledger(session, student_id, start_date, end_date)
    return success_response(data)


@finance_router.get("/reports/income-report")
async def report_income(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_income(session, start_date, end_date)
    return success_response(data)


@finance_router.get("/reports/expense-report")
async def report_expense(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_expense(session, start_date, end_date)
    return success_response(data)


@finance_router.get("/reports/profit-loss")
async def report_profit_loss(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_profit_loss(session, start_date, end_date)
    return success_response(data)


@finance_router.get("/reports/payment-mode")
async def report_payment_mode(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_payment_mode(session, start_date, end_date)
    return success_response(data)


@finance_router.get("/reports/class-wise-collection")
async def report_class_wise(
    academic_year: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_class_wise_collection(session, academic_year)
    return success_response(data)


@finance_router.get("/reports/section-wise-collection")
async def report_section_wise(
    academic_year: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_section_wise_collection(session, academic_year)
    return success_response(data)


@finance_router.get("/reports/transport-fee")
async def report_transport_fee(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_transport_fee(session, start_date, end_date)
    return success_response(data)


@finance_router.get("/reports/hostel-fee")
async def report_hostel_fee(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_hostel_fee(session, start_date, end_date)
    return success_response(data)


@finance_router.get("/reports/library-fine")
async def report_library_fine(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    data = await finance_service.get_report_library_fine(session, start_date, end_date)
    return success_response(data)


# Receipts
@finance_router.get("/receipts/{payment_id}")
async def get_receipt(
    payment_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await finance_service.generate_receipt(session, payment_id)
    return success_response(data)


@finance_router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await finance_service.generate_invoice(session, invoice_id)
    return success_response(data)


# Dashboards
@finance_router.get("/dashboard/admin")
async def get_admin_dashboard(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin(current_user)
    data = await finance_service.get_admin_dashboard(session)
    return success_response(data)


@finance_router.get("/dashboard/student/{student_id}")
async def get_student_finance_dashboard(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name not in ("ADMIN", "STUDENT"):
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Only admin or student users can access this dashboard",
        )
    if current_user.role.role_name == "STUDENT":
        student = await session.execute(
            select(Student).where(Student.user_id == current_user.id)
        )
        student_obj = student.scalar_one_or_none()
        if student_obj is None or student_obj.id != student_id:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You can only access your own dashboard",
            )
    data = await finance_service.get_student_dashboard(session, student_id)
    return success_response(data)


@finance_router.get("/dashboard/parent/{parent_id}")
async def get_parent_finance_dashboard(
    parent_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.role_name not in ("ADMIN", "PARENT"):
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Only admin or parent users can access this dashboard",
        )
    if current_user.role.role_name == "PARENT":
        if current_user.id != parent_id:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You can only access your own dashboard",
            )
    data = await finance_service.get_parent_dashboard(session, parent_id)
    return success_response(data)


# Payments
@finance_router.get("/payments/{item_id}")
async def get_payment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await payment_service.get(session, item_id)
    return success_response(item)


@finance_router.put("/payments/{item_id}")
async def update_payment(
    item_id: UUID,
    payload: PaymentUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    item = await payment_service.update(session, item_id, payload.model_dump(exclude_unset=True))
    return success_response(item, message="Payment updated successfully")


@finance_router.delete("/payments/{item_id}")
async def delete_payment(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_admin_or_accountant(current_user)
    await payment_service.delete(session, item_id)
    return success_response(message="Payment deleted successfully")

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.api.v1.router_factory import require_roles
from app.api.v1.router_factory import build_crud_router
from app.core.database import get_db
from app.models.exam_result_model import ExamResult
from app.models.parent_model import Parent
from app.models.parent_student_model import ParentStudent
from app.models.student_model import Student
from app.models.timetable_model import Timetable
from app.models.user import User
from app.schemas.student_schema import StudentCreate, StudentResponse, StudentUpdate
from app.schemas.exam_schema import (
    ExamResultResponse,
    ReportCardResponse,
    StudentPerformanceSummary,
)
from app.services.report_card_service import report_card_service
from app.services.student_service import student_service

router = build_crud_router(
    student_service,
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    read_roles=("ADMIN", "TEACHER", "ACCOUNTANT", "LIBRARIAN", "WARDEN"),
)

async def get_current_student(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Student:
    result = await session.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )
    return student


@router.get("/me", response_model=StudentResponse)
async def get_current_student_profile(
    student: Student = Depends(get_current_student),
):
    return student


@router.get("/me/subjects", response_model=list[dict])
async def get_current_student_subjects(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.class_subject_model import ClassSubject
    from app.models.subject_model import Subject

    if student.class_id is None:
        return []

    result = await session.execute(
        select(Subject)
        .join(ClassSubject, ClassSubject.subject_id == Subject.id)
        .where(ClassSubject.class_id == student.class_id)
    )
    subjects = result.scalars().all()
    return [
        {
            "id": str(sub.id),
            "subject_name": sub.subject_name,
            "subject_code": sub.subject_code,
            "class_name": student.class_.class_name if student.class_ else student.class_name,
            "section": student.class_.section if student.class_ else None,
            "academic_year": student.class_.academic_year if student.class_ else None,
        }
        for sub in subjects
    ]



@router.get("/me/timetable", response_model=list[dict])
async def get_current_student_timetable(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    if student.class_id is None:
        return []

    result = await session.execute(
        select(Timetable).where(Timetable.class_id == student.class_id)
    )
    entries = result.scalars().all()
    return [
        {
            "id": str(entry.id),
            "class_id": str(entry.class_id),
            "subject_id": str(entry.subject_id),
            "subject_name": entry.subject.subject_name if entry.subject else None,
            "teacher_id": str(entry.teacher_id),
            "teacher_name": entry.teacher.user.username if entry.teacher and entry.teacher.user else None,
            "day_of_week": entry.day_of_week,
            "start_time": str(entry.start_time),
            "end_time": str(entry.end_time),
            "room_no": entry.room_no,
            "period_no": entry.period_no,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }
        for entry in entries
    ]


@router.get("/me/assignments", response_model=list[dict])
async def get_current_student_assignments(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.assignment_model import Assignment, AssignmentSubmission

    if student.class_id is None:
        return []

    assignments_result = await session.execute(
        select(Assignment).where(Assignment.class_id == student.class_id)
    )
    assignments = assignments_result.scalars().all()
    submissions_result = await session.execute(
        select(AssignmentSubmission).where(AssignmentSubmission.student_id == student.id)
    )
    submissions_by_assignment = {
        submission.assignment_id: submission
        for submission in submissions_result.scalars().all()
    }

    return [
        {
            "id": str(assignment.id),
            "teacher_id": str(assignment.teacher_id),
            "teacher_name": assignment.teacher.user.username if assignment.teacher and assignment.teacher.user else None,
            "class_id": str(assignment.class_id),
            "subject_id": str(assignment.subject_id),
            "subject_name": assignment.subject.subject_name if assignment.subject else None,
            "title": assignment.title,
            "description": assignment.description,
            "due_date": assignment.due_date,
            "attachment": assignment.attachment,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at,
            "submission": (
                {
                    "id": str(submissions_by_assignment[assignment.id].id),
                    "assignment_id": str(submissions_by_assignment[assignment.id].assignment_id),
                    "student_id": str(submissions_by_assignment[assignment.id].student_id),
                    "submitted_on": submissions_by_assignment[assignment.id].submitted_on,
                    "file_path": submissions_by_assignment[assignment.id].file_path,
                    "marks": submissions_by_assignment[assignment.id].marks,
                    "remarks": submissions_by_assignment[assignment.id].remarks,
                    "created_at": submissions_by_assignment[assignment.id].created_at,
                    "updated_at": submissions_by_assignment[assignment.id].updated_at,
                }
                if assignment.id in submissions_by_assignment
                else None
            ),
        }
        for assignment in assignments
    ]


@router.get("/me/submissions", response_model=list[dict])
async def get_current_student_submissions(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.assignment_model import AssignmentSubmission

    result = await session.execute(
        select(AssignmentSubmission).where(AssignmentSubmission.student_id == student.id)
    )
    return [
        {
            "id": str(submission.id),
            "assignment_id": str(submission.assignment_id),
            "student_id": str(submission.student_id),
            "submitted_on": submission.submitted_on,
            "file_path": submission.file_path,
            "marks": submission.marks,
            "remarks": submission.remarks,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
        }
        for submission in result.scalars().all()
    ]


@router.get("/me/exam-results", response_model=list[ExamResultResponse])
async def get_current_student_exam_results(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(ExamResult).where(ExamResult.student_id == student.id)
    )
    return result.scalars().all()


@router.get("/me/hostel", response_model=dict)
async def get_current_student_hostel(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.hostel_model import HostelAllocation, HostelAllocationStatus
    result = await session.execute(
        select(HostelAllocation)
        .where(HostelAllocation.student_id == student.id)
        .where(HostelAllocation.status == HostelAllocationStatus.ACTIVE)
        .limit(1)
    )
    allocation = result.scalar_one_or_none()
    if allocation is None:
        return {"allocated": False, "block_name": None, "room_no": None, "bed_no": None, "status": "NOT_ALLOCATED"}
    bed = allocation.bed
    room = bed.room if bed else None
    block = room.block if room else None
    return {
        "allocated": True,
        "block_name": block.block_name if block else None,
        "block_type": block.block_type if block else None,
        "room_no": room.room_no if room else None,
        "bed_no": bed.bed_no if bed else None,
        "floor_no": room.floor_no if room else None,
        "check_in_date": str(allocation.check_in_date),
        "status": allocation.status.value,
    }


@router.get("/me/hostel-fees", response_model=dict)
async def get_current_student_hostel_fees(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.hostel_operations_model import HostelFeeInvoice, HostelInvoiceStatus
    result = await session.execute(
        select(HostelFeeInvoice).where(HostelFeeInvoice.student_id == student.id)
    )
    invoices = result.scalars().all()
    total = sum(float(inv.amount) for inv in invoices)
    paid = sum(float(inv.amount) for inv in invoices if inv.status == HostelInvoiceStatus.PAID)
    pending = total - paid
    return {
        "total_fees": total,
        "paid_amount": paid,
        "pending_amount": pending,
        "invoices": [
            {
                "id": str(inv.id),
                "fee_type": inv.fee_structure.fee_type if inv.fee_structure else "Hostel Fee",
                "amount": float(inv.amount),
                "status": inv.status.value,
                "invoice_date": str(inv.invoice_date),
                "due_date": str(inv.due_date),
            }
            for inv in invoices
        ],
    }


@router.get("/me/attendance", response_model=dict)
async def get_current_student_attendance(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.attendance_model import Attendance
    result = await session.execute(
        select(Attendance).where(Attendance.student_id == student.id)
    )
    records = result.scalars().all()
    total = len(records)
    present = sum(1 for r in records if (r.status.value if hasattr(r.status, "value") else str(r.status)) == "PRESENT")
    absent = sum(1 for r in records if (r.status.value if hasattr(r.status, "value") else str(r.status)) == "ABSENT")
    late = sum(1 for r in records if (r.status.value if hasattr(r.status, "value") else str(r.status)) == "LATE")
    percentage = (present / total * 100) if total > 0 else 0
    return {
        "total_classes": total,
        "present": present,
        "absent": absent,
        "late": late,
        "attendance_percentage": round(percentage, 2),
        "records": [
            {
                "id": str(r.id),
                "date": str(r.attendance_date),
                "subject_id": str(r.subject_id),
                "subject_name": r.subject.subject_name if r.subject else "N/A",
                "period_no": r.period_no,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            }
            for r in records
        ],
    }


@router.get("/me/transport", response_model=dict)
async def get_current_student_transport(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.transport_model import StudentTransport
    result = await session.execute(
        select(StudentTransport).where(StudentTransport.student_id == student.id)
    )
    st = result.scalar_one_or_none()
    if st is None:
        return {"assigned": False, "bus_number": None, "route_name": None, "stop_point": None}
    bus = st.bus
    route = st.route
    return {
        "assigned": True,
        "bus_number": bus.bus_number if bus else None,
        "bus_model": bus.model if bus else None,
        "route_name": route.route_name if route else None,
        "start_point": route.start_point if route else None,
        "end_point": route.end_point if route else None,
        "stop_point": st.stop_point,
    }


@router.post("/me/submit-assignment", response_model=dict)
async def submit_assignment_for_me(
    payload: dict,
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.assignment_model import AssignmentSubmission
    from datetime import datetime, timezone

    assignment_id_str = payload.get("assignment_id")
    if not assignment_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="assignment_id is required")
    assignment_id = UUID(assignment_id_str)
    file_path = payload.get("file_path", "")

    res = await session.execute(
        select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.student_id == student.id,
        )
    )
    existing = res.scalar_one_or_none()
    if existing:
        existing.file_path = file_path
        existing.submitted_on = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(existing)
        sub = existing
    else:
        sub = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student.id,
            file_path=file_path,
            submitted_on=datetime.now(timezone.utc),
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

    return {
        "id": str(sub.id),
        "assignment_id": str(sub.assignment_id),
        "student_id": str(sub.student_id),
        "submitted_on": str(sub.submitted_on),
        "file_path": sub.file_path,
        "marks": float(sub.marks) if sub.marks is not None else None,
        "remarks": sub.remarks,
    }



@router.get("/me/fees", response_model=dict)
async def get_current_student_fees(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.services.fee_service import fee_invoice_service, payment_service, _invoice_total_paid

    summary = await fee_invoice_service.get_student_fee_summary(session, student.id)
    invoices = await fee_invoice_service.get_by_student(session, student.id)
    outstanding_invoices = await fee_invoice_service.get_outstanding_by_student(session, student.id)
    payments = await payment_service.get_by_student(session, student.id)

    formatted_invoices = []
    for inv in invoices:
        paid = float(await _invoice_total_paid(session, inv.id))
        net = float(inv.net_amount if inv.net_amount else inv.amount)
        formatted_invoices.append({
            "id": str(inv.id),
            "invoice_number": inv.invoice_number or f"INV-{inv.id}",
            "amount": net,
            "paid_amount": paid,
            "pending_amount": max(0.0, net - paid),
            "status": inv.status,
            "due_date": str(inv.due_date) if inv.due_date else None,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
        })

    return {
        "total_fees": summary.get("total_fees", 0),
        "paid_amount": summary.get("paid", 0),
        "pending_amount": summary.get("pending", 0),
        "outstanding_invoices": len(outstanding_invoices),
        "invoices": formatted_invoices,
        "payment_history": [
            {
                "payment_id": str(p.id),
                "date": str(p.payment_date) if p.payment_date else None,
                "amount": float(p.amount_paid),
                "method": p.payment_method,
                "receipt": p.receipt_number or p.receipt_no or "",
                "status": p.payment_status,
                "remarks": p.remarks or "",
            }
            for p in payments
        ],
    }


@router.get("/{student_id}/fee-invoices", response_model=list)
async def get_student_fee_invoices(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.fee_service import fee_invoice_service, _invoice_total_paid
    invoices = await fee_invoice_service.get_by_student(session, student_id)
    result = []
    for inv in invoices:
        paid = float(await _invoice_total_paid(session, inv.id))
        net = float(inv.net_amount if inv.net_amount else inv.amount)
        result.append({
            "id": str(inv.id),
            "invoiceNo": inv.invoice_number or f"INV-{str(inv.id)[:8]}",
            "invoice_number": inv.invoice_number or f"INV-{str(inv.id)[:8]}",
            "amount": net,
            "paid": paid,
            "paidAmount": paid,
            "paid_amount": paid,
            "balance": max(0.0, net - paid),
            "pendingAmount": max(0.0, net - paid),
            "status": inv.status,
            "dueDate": str(inv.due_date) if inv.due_date else None,
            "due_date": str(inv.due_date) if inv.due_date else None,
            "date": str(inv.invoice_date) if inv.invoice_date else None,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
        })
    return result


@router.get("/{student_id}/payments", response_model=list)
async def get_student_payments(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.fee_service import payment_service
    payments = await payment_service.get_by_student(session, student_id)
    return [
        {
            "id": str(p.id),
            "payment_id": str(p.id),
            "date": str(p.payment_date) if p.payment_date else None,
            "payment_date": str(p.payment_date) if p.payment_date else None,
            "amount": float(p.amount_paid),
            "amount_paid": float(p.amount_paid),
            "method": p.payment_method,
            "payment_method": p.payment_method,
            "receipt": p.receipt_number or p.receipt_no or "",
            "receipt_number": p.receipt_number or p.receipt_no or "",
            "status": p.payment_status,
            "payment_status": p.payment_status,
            "remarks": p.remarks or "",
        }
        for p in payments
    ]


@router.get("/{student_id}/fee-summary", response_model=dict)
async def get_student_fee_summary_endpoint(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.fee_service import fee_invoice_service
    summary = await fee_invoice_service.get_student_fee_summary(session, student_id)
    return {
        "totalFees": summary.get("total_fees", 0),
        "total_fees": summary.get("total_fees", 0),
        "paidAmount": summary.get("paid", 0),
        "paid_amount": summary.get("paid", 0),
        "pendingAmount": summary.get("pending", 0),
        "pending_amount": summary.get("pending", 0),
    }


@router.get("/me/library", response_model=dict)
async def get_current_student_library(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db),
):
    from app.models.library_model import BookIssue, BookReservation, FinePayment, BookIssueStatus, ReservationStatus, FinePaymentStatus
    issues_result = await session.execute(
        select(BookIssue).where(BookIssue.student_id == student.id)
    )
    issues = issues_result.scalars().all()
    reservations_result = await session.execute(
        select(BookReservation).where(BookReservation.student_id == student.id)
    )
    reservations = reservations_result.scalars().all()
    fines_result = await session.execute(
        select(FinePayment).join(BookIssue).where(BookIssue.student_id == student.id)
    )
    fines = fines_result.scalars().all()
    active_issues = [i for i in issues if i.status == BookIssueStatus.ISSUED.value]
    overdue_issues = [i for i in issues if i.status == BookIssueStatus.OVERDUE.value]
    returned_issues = [i for i in issues if i.status == BookIssueStatus.RETURNED.value]
    return {
        "active_books": len(active_issues),
        "overdue_books": len(overdue_issues),
        "returned_books": len(returned_issues),
        "total_fine": sum(float(f.amount) for f in fines if f.status == FinePaymentStatus.PAID.value),
        "outstanding_fine": sum(float(f.amount) for f in fines if f.status != FinePaymentStatus.PAID.value),
        "active_issues": [
            {
                "id": str(i.id),
                "book_title": i.book_title,
                "book_author": i.book_author,
                "issue_date": str(i.issue_date),
                "due_date": str(i.due_date),
                "status": i.status,
                "fine_amount": float(i.fine_amount),
            }
            for i in active_issues
        ],
        "overdue_issues": [
            {
                "id": str(i.id),
                "book_title": i.book_title,
                "book_author": i.book_author,
                "issue_date": str(i.issue_date),
                "due_date": str(i.due_date),
                "status": i.status,
                "fine_amount": float(i.fine_amount),
            }
            for i in overdue_issues
        ],
        "reservations": [
            {
                "id": str(r.id),
                "book_title": r.book_title,
                "reservation_date": str(r.reservation_date),
                "status": r.status,
            }
            for r in reservations
        ],
    }


@router.get("/{student_id}/exam-results", response_model=list[ExamResultResponse])
async def get_student_exam_results(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_student_access(session, current_user, student_id)
    result = await session.execute(
        select(ExamResult).where(ExamResult.student_id == student_id)
    )
    return result.scalars().all()


@router.get("/{student_id}/report-cards", response_model=list[ReportCardResponse])
async def get_student_report_cards(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_student_access(session, current_user, student_id)
    return await report_card_service.get_student_report_cards(session, student_id)


@router.get("/{student_id}/performance", response_model=StudentPerformanceSummary)
async def get_student_performance(
    student_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_student_access(session, current_user, student_id)
    return await report_card_service.get_performance_summary(session, student_id)


async def ensure_student_access(
    session: AsyncSession,
    current_user: User,
    student_id: UUID,
) -> None:
    role_name = current_user.role.role_name.upper() if current_user.role else ""
    if role_name == "ADMIN":
        await student_service.get(session, student_id)
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
        detail="You do not have permission to access this student's records",
    )

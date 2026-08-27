from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.dashboard_router import router as dashboard_router
from app.api.v1.admin_router import router as admin_router
from app.api.v1.admission_router import (
    application_router as admission_application_router,
    document_router as admission_document_router,
)
from app.api.v1.attendance_router import router as attendance_router
from app.api.v1.class_router import router as class_router
from app.api.v1.class_subject_router import router as class_subject_router
from app.api.v1.department_router import router as department_router
from app.api.v1.exam_result_router import router as exam_result_router
from app.api.v1.exam_router import router as exam_router
from app.api.v1.parent_router import router as parent_router
from app.api.v1.parent_student_router import router as parent_student_router
from app.api.v1.student_router import router as student_router
from app.api.v1.subject_router import router as subject_router
from app.api.v1.teacher_router import router as teacher_router
from app.api.v1.teacher_subject_router import router as teacher_subject_router
from app.api.v1.timetable_router import router as timetable_router
from app.api.v1.report_card_router import router as report_card_router
from app.api.v1.users.routes import router as user_router
from app.api.v1.assignment_router import router as assignment_router, submission_router, teacher_assignment_router, class_assignment_router, student_assignment_router
from app.api.v1.communication_router import announcement_router, notification_router, message_router, user_communication_router, teacher_communication_router, communication_router
from app.api.v1.fee_router import fee_structure_router, fee_invoice_router, payment_router, student_fee_router, accountant_fee_router
from app.api.v1.leave_router import leave_request_router, leave_type_router, user_leave_router
from app.api.v1.event_router import academic_calendar_router, event_router
from app.api.v1.library_router import (
    author_router,
    book_category_router,
    book_issue_router,
    book_router,
    fine_payment_router,
    library_report_router,
    library_router,
    library_settings_router,
    publisher_router,
    reservation_router,
    student_library_router,
)
from app.api.v1.transport_router import bus_router, route_router, student_transport_detail_router, student_transport_router, transport_router
from app.api.v1.auth.routes import router as auth_router
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import RateLimitMiddleware
from app.services.auth_service import AuthService
from app.services.audit_service import audit_log_service
from app.api.v1.finance_router import finance_router
from app.api.v1.audit_router import audit_log_router, audit_router, login_history_router, user_audit_router
from app.api.v1.ai_analytics_router import ai_analytics_router, ai_chat_history_router, user_chat_history_router
from app.api.v1.hostel_router import allocation_router, bed_router, block_router, hostel_router, room_router, student_hostel_router
from app.api.v1.hostel_operations_router import visitor_router, fee_structure_router as hostel_fee_structure_router, fee_invoice_router as hostel_fee_invoice_router, hostel_payment_router, mess_menu_router, mess_expense_router, mess_collection_router, mess_attendance_router, maintenance_router, work_order_router, student_hostel_extra_router, hostel_extra_router
from app.api.v1.hostel_complaint_router import hostel_complaint_router
from app.api.v1.hostel_notice_router import hostel_notice_router
from app.api.v1.hostel_setting_router import hostel_setting_router
from app.api.v1.hostel_leave_router import hostel_leave_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Auth Service API",
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(admin_router, prefix="/admins", tags=["Admins"])
app.include_router(department_router, prefix="/departments", tags=["Departments"])
app.include_router(teacher_router, prefix="/teachers", tags=["Teachers"])
app.include_router(parent_router, prefix="/parents", tags=["Parents"])
app.include_router(student_router, prefix="/students", tags=["Students"])
app.include_router(parent_student_router, prefix="/parent-students", tags=["Parent Students"])
app.include_router(class_router, prefix="/classes", tags=["Classes"])
app.include_router(subject_router, prefix="/subjects", tags=["Subjects"])
app.include_router(class_subject_router, prefix="/class-subjects", tags=["Class Subjects"])
app.include_router(teacher_subject_router, prefix="/teacher-subjects", tags=["Teacher Subjects"])
app.include_router(timetable_router, prefix="/timetables", tags=["Timetables"])
app.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])
app.include_router(exam_router, prefix="/exams", tags=["Exams"])
app.include_router(exam_result_router, prefix="/exam-results", tags=["Exam Results"])
app.include_router(report_card_router, prefix="/report-cards", tags=["Report Cards"])
app.include_router(assignment_router, prefix="/assignments", tags=["Assignments"])
app.include_router(submission_router, prefix="/assignment-submissions", tags=["Assignment Submissions"])
app.include_router(teacher_assignment_router, prefix="/teachers", tags=["Teacher Assignments"])
app.include_router(class_assignment_router, prefix="/classes", tags=["Class Assignments"])
app.include_router(student_assignment_router, prefix="/students", tags=["Student Assignments"])
app.include_router(announcement_router, prefix="/announcements", tags=["Announcements"])
app.include_router(notification_router, prefix="/notifications", tags=["Notifications"])
app.include_router(message_router, prefix="/messages", tags=["Messages"])
app.include_router(communication_router, prefix="/communication", tags=["Communication"])
app.include_router(user_communication_router, prefix="/users", tags=["User Communication"])
app.include_router(teacher_communication_router, prefix="/teachers", tags=["Teacher Communication"])
app.include_router(fee_structure_router, prefix="/fee-structures", tags=["Fee Structures"])
app.include_router(fee_invoice_router, prefix="/fee-invoices", tags=["Fee Invoices"])
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
app.include_router(student_fee_router, prefix="/students", tags=["Student Fees"])
app.include_router(accountant_fee_router, prefix="/fees", tags=["Accountant Fees"])
app.include_router(
    admission_application_router,
    prefix="/admission-applications",
    tags=["Admission Applications"],
)


@app.middleware("http")
async def audit_business_actions(request, call_next):
    response = await call_next(request)
    if response.status_code >= 400 or request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return response
    if request.url.path.startswith(("/login", "/logout", "/audit", "/login-history", "/audit-logs")):
        return response
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return response
    payload = AuthService.verify_token(authorization.split(" ", 1)[1])
    try:
        user_id = UUID(payload["sub"]) if payload else None
    except (KeyError, ValueError, TypeError):
        user_id = None
    if user_id is None:
        return response
    activity = {"POST": "Create Record", "PUT": "Update Record", "PATCH": "Update Record", "DELETE": "Delete Record"}[request.method]
    path = request.url.path.lower()
    if "approve" in path and "leave" in path: activity = "Approve Leave"
    elif "reject" in path and "leave" in path: activity = "Reject Leave"
    elif path.startswith("/payments") and request.method == "POST": activity = "Fee Payment"
    elif "issue" in path and "book" in path and request.method == "POST": activity = "Book Issue"
    elif "return" in path and "book" in path: activity = "Book Return"
    elif "reservation" in path and "library" in path and request.method == "POST": activity = "Reservation Created"
    elif "approve" in path and "reservation" in path: activity = "Reservation Approved"
    elif "reject" in path and "reservation" in path: activity = "Reservation Rejected"
    elif "pay-fine" in path: activity = "Fine Payment"
    elif "approve" in path and "admission" in path: activity = "Admission Approval"
    try:
        async with AsyncSessionLocal() as audit_session:
            await audit_log_service.create_log(audit_session, {
                "user_id": user_id, "activity": activity,
                "details": f"{request.method} {request.url.path}",
            })
    except Exception:
        # Auditing must never turn a completed business action into a failed response.
        pass
    return response
app.include_router(
    admission_document_router,
    prefix="/admission-documents",
    tags=["Admission Documents"],
)
app.include_router(leave_type_router, prefix="/leave-types", tags=["Leave Types"])
app.include_router(leave_request_router, prefix="/leave-requests", tags=["Leave Requests"])
app.include_router(user_leave_router, prefix="/users", tags=["User Leave Requests"])
app.include_router(event_router, prefix="/events", tags=["Events"])
app.include_router(academic_calendar_router, prefix="/academic-calendar", tags=["Academic Calendar"])
app.include_router(book_category_router, prefix="/book-categories", tags=["Book Categories"])
app.include_router(book_router, prefix="/books", tags=["Books"])
app.include_router(book_issue_router, prefix="/book-issues", tags=["Book Issues"])
app.include_router(student_library_router, prefix="/students", tags=["Student Library"])
app.include_router(library_router, prefix="/library", tags=["Library"])
app.include_router(author_router, prefix="/library/authors", tags=["Library Authors"])
app.include_router(publisher_router, prefix="/library/publishers", tags=["Library Publishers"])
app.include_router(reservation_router, prefix="/library/reservations", tags=["Library Reservations"])
app.include_router(fine_payment_router, prefix="/library/fine-payments", tags=["Library Fine Payments"])
app.include_router(library_settings_router, prefix="/library/settings", tags=["Library Settings"])
app.include_router(library_report_router, prefix="/library/reports", tags=["Library Reports"])
app.include_router(bus_router, prefix="/buses", tags=["Buses"])
app.include_router(route_router, prefix="/routes", tags=["Routes"])
app.include_router(student_transport_router, prefix="/student-transport", tags=["Student Transport"])
app.include_router(student_transport_detail_router, prefix="/students", tags=["Student Transport"])
app.include_router(transport_router, prefix="/transport", tags=["Transport"])
app.include_router(finance_router, prefix="/finance", tags=["Finance"])
app.include_router(user_router, tags=["Users"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(login_history_router, prefix="/login-history", tags=["Login History"])
app.include_router(audit_log_router, prefix="/audit-logs", tags=["Audit Logs"])
app.include_router(audit_router, prefix="/audit", tags=["Audit & Security"])
app.include_router(user_audit_router, prefix="/users", tags=["User Activity"])
app.include_router(ai_analytics_router, prefix="/ai-analytics", tags=["AI Analytics"])
app.include_router(ai_chat_history_router, prefix="/ai-chat-history", tags=["AI Chat History"])
app.include_router(user_chat_history_router, prefix="/users", tags=["User Chat History"])
app.include_router(block_router, prefix="/hostel-blocks", tags=["Hostel Blocks"])
app.include_router(room_router, prefix="/hostel-rooms", tags=["Hostel Rooms"])
app.include_router(bed_router, prefix="/hostel-beds", tags=["Hostel Beds"])
app.include_router(allocation_router, prefix="/hostel-allocations", tags=["Hostel Allocations"])
app.include_router(student_hostel_router, prefix="/students", tags=["Student Hostel"])
app.include_router(hostel_router, prefix="/hostel", tags=["Hostel"])
app.include_router(visitor_router, prefix="/hostel-visitors", tags=["Hostel Visitors"])
app.include_router(hostel_fee_structure_router, prefix="/hostel-fee-structures", tags=["Hostel Fee Structures"])
app.include_router(hostel_fee_invoice_router, prefix="/hostel-fee-invoices", tags=["Hostel Fee Invoices"])
app.include_router(hostel_payment_router, prefix="/hostel-payments", tags=["Hostel Payments"])
app.include_router(mess_menu_router, prefix="/mess-menu", tags=["Mess Menu"])
app.include_router(mess_expense_router, prefix="/mess-expenses", tags=["Mess Expenses"])
app.include_router(mess_collection_router, prefix="/mess-collections", tags=["Mess Collections"])
app.include_router(mess_attendance_router, prefix="/mess-attendance", tags=["Mess Attendance"])
app.include_router(maintenance_router, prefix="/maintenance-requests", tags=["Maintenance Requests"])
app.include_router(work_order_router, prefix="/work-orders", tags=["Work Orders"])
app.include_router(student_hostel_extra_router, prefix="/students", tags=["Student Hostel"])
app.include_router(hostel_extra_router, prefix="/hostel", tags=["Hostel"])
app.include_router(hostel_complaint_router, prefix="/hostel-complaints", tags=["Hostel Complaints"])
app.include_router(hostel_notice_router, prefix="/hostel-notices", tags=["Hostel Notices"])
app.include_router(hostel_setting_router, prefix="/hostel-settings", tags=["Hostel Settings"])
from app.api.v1.academic_content_router import router as academic_content_router

app.include_router(academic_content_router, prefix="", tags=["Academic Content"])


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


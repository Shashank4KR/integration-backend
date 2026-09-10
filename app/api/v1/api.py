from fastapi import APIRouter

from app.api.v1.academics import (
    academic_content_router,
    class_router,
    class_subject_router,
    department_router,
    subject_router,
    timetable_router,
)
from app.api.v1.admissions import (
    application_router as admission_application_router,
    document_router as admission_document_router,
)
from app.api.v1.ai_analytics import (
    ai_analytics_router,
    ai_chat_history_router,
    user_chat_history_router,
)
from app.api.v1.assignments import (
    class_assignment_router,
    router as assignment_router,
    student_assignment_router,
    submission_router,
    teacher_assignment_router,
)
from app.api.v1.attendance import router as attendance_router
from app.api.v1.audit import (
    audit_log_router,
    audit_router,
    login_history_router,
    user_audit_router,
)
from app.api.v1.auth import router as auth_router
from app.api.v1.communication import (
    announcement_router,
    communication_router,
    message_router,
    notification_router,
    teacher_communication_router,
    user_communication_router,
)
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.events import academic_calendar_router, event_router
from app.api.v1.exams import (
    exam_result_router,
    exam_router,
    exam_sub_router,
    report_card_router,
)
from app.api.v1.finance import (
    accountant_fee_router,
    fee_invoice_router,
    fee_structure_router,
    finance_router,
    payment_router,
    student_fee_router,
)
from app.api.v1.hostel import (
    allocation_router,
    bed_router,
    block_router,
    hostel_complaint_router,
    hostel_extra_router,
    hostel_fee_invoice_router,
    hostel_fee_structure_router,
    hostel_leave_router,
    hostel_notice_router,
    hostel_payment_router,
    hostel_router,
    hostel_setting_router,
    maintenance_router,
    mess_attendance_router,
    mess_collection_router,
    mess_expense_router,
    mess_menu_router,
    room_router,
    student_hostel_extra_router,
    student_hostel_router,
    visitor_router,
    work_order_router,
)
from app.api.v1.leaves import (
    leave_request_router,
    leave_type_router,
    user_leave_router,
)
from app.api.v1.library import (
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
from app.api.v1.parents import (
    parent_router,
    parent_student_router,
)
from app.api.v1.settings import settings_router
from app.api.v1.students import router as student_router
from app.api.v1.teachers import (
    teacher_router,
    teacher_subject_router,
)
from app.api.v1.transport import (
    bus_router,
    route_router,
    student_transport_detail_router,
    student_transport_router,
    transport_router,
)
from app.api.v1.users import (
    admin_router,
    user_router,
)

api_router = APIRouter()

# Dashboard
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

# Users & Admins
api_router.include_router(admin_router, prefix="/admins", tags=["Admins"])
api_router.include_router(user_router, tags=["Users"])

# Academics
api_router.include_router(department_router, prefix="/departments", tags=["Departments"])
api_router.include_router(class_router, prefix="/classes", tags=["Classes"])
api_router.include_router(subject_router, prefix="/subjects", tags=["Subjects"])
api_router.include_router(class_subject_router, prefix="/class-subjects", tags=["Class Subjects"])
api_router.include_router(teacher_subject_router, prefix="/teacher-subjects", tags=["Teacher Subjects"])
api_router.include_router(timetable_router, prefix="/timetables", tags=["Timetables"])
api_router.include_router(academic_content_router, prefix="", tags=["Academic Content"])

# People
api_router.include_router(teacher_router, prefix="/teachers", tags=["Teachers"])
api_router.include_router(parent_router, prefix="/parents", tags=["Parents"])
api_router.include_router(student_router, prefix="/students", tags=["Students"])
api_router.include_router(parent_student_router, prefix="/parent-students", tags=["Parent Students"])

# Attendance
api_router.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])

# Examinations
api_router.include_router(exam_router, prefix="/exams", tags=["Exams"])
api_router.include_router(exam_sub_router, prefix="/exams", tags=["Exams"])
api_router.include_router(exam_result_router, prefix="/exam-results", tags=["Exam Results"])
api_router.include_router(report_card_router, prefix="/report-cards", tags=["Report Cards"])

# Assignments
api_router.include_router(assignment_router, prefix="/assignments", tags=["Assignments"])
api_router.include_router(submission_router, prefix="/assignment-submissions", tags=["Assignment Submissions"])
api_router.include_router(teacher_assignment_router, prefix="/teachers", tags=["Teacher Assignments"])
api_router.include_router(class_assignment_router, prefix="/classes", tags=["Class Assignments"])
api_router.include_router(student_assignment_router, prefix="/students", tags=["Student Assignments"])

# Communication
api_router.include_router(announcement_router, prefix="/announcements", tags=["Announcements"])
api_router.include_router(notification_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(message_router, prefix="/messages", tags=["Messages"])
api_router.include_router(communication_router, prefix="/communication", tags=["Communication"])
api_router.include_router(user_communication_router, prefix="/users", tags=["User Communication"])
api_router.include_router(teacher_communication_router, prefix="/teachers", tags=["Teacher Communication"])

# Finance & Fees
api_router.include_router(fee_structure_router, prefix="/fee-structures", tags=["Fee Structures"])
api_router.include_router(fee_invoice_router, prefix="/fee-invoices", tags=["Fee Invoices"])
api_router.include_router(payment_router, prefix="/payments", tags=["Payments"])
api_router.include_router(student_fee_router, prefix="/students", tags=["Student Fees"])
api_router.include_router(accountant_fee_router, prefix="/fees", tags=["Accountant Fees"])
api_router.include_router(finance_router, prefix="/finance", tags=["Finance"])

# Admissions
api_router.include_router(admission_application_router, prefix="/admission-applications", tags=["Admission Applications"])
api_router.include_router(admission_document_router, prefix="/admission-documents", tags=["Admission Documents"])

# Leaves
api_router.include_router(leave_type_router, prefix="/leave-types", tags=["Leave Types"])
api_router.include_router(leave_request_router, prefix="/leave-requests", tags=["Leave Requests"])
api_router.include_router(user_leave_router, prefix="/users", tags=["User Leave Requests"])

# Events
api_router.include_router(event_router, prefix="/events", tags=["Events"])
api_router.include_router(academic_calendar_router, prefix="/academic-calendar", tags=["Academic Calendar"])

# Library
api_router.include_router(book_category_router, prefix="/book-categories", tags=["Book Categories"])
api_router.include_router(book_router, prefix="/books", tags=["Books"])
api_router.include_router(book_issue_router, prefix="/book-issues", tags=["Book Issues"])
api_router.include_router(student_library_router, prefix="/students", tags=["Student Library"])
api_router.include_router(library_router, prefix="/library", tags=["Library"])
api_router.include_router(author_router, prefix="/library/authors", tags=["Library Authors"])
api_router.include_router(publisher_router, prefix="/library/publishers", tags=["Library Publishers"])
api_router.include_router(reservation_router, prefix="/library/reservations", tags=["Library Reservations"])
api_router.include_router(fine_payment_router, prefix="/library/fine-payments", tags=["Library Fine Payments"])
api_router.include_router(library_settings_router, prefix="/library/settings", tags=["Library Settings"])
api_router.include_router(library_report_router, prefix="/library/reports", tags=["Library Reports"])

# Transport
api_router.include_router(bus_router, prefix="/buses", tags=["Buses"])
api_router.include_router(route_router, prefix="/routes", tags=["Routes"])
api_router.include_router(student_transport_router, prefix="/student-transport", tags=["Student Transport"])
api_router.include_router(student_transport_detail_router, prefix="/students", tags=["Student Transport"])
api_router.include_router(transport_router, prefix="/transport", tags=["Transport"])

# Auth
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(auth_router, tags=["auth"])  # Expose auth routes at root for compatibility

# Audit & Security
api_router.include_router(login_history_router, prefix="/login-history", tags=["Login History"])
api_router.include_router(audit_log_router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(audit_router, prefix="/audit", tags=["Audit & Security"])
api_router.include_router(user_audit_router, prefix="/users", tags=["User Activity"])

# AI & Analytics
api_router.include_router(ai_analytics_router, prefix="/ai-analytics", tags=["AI Analytics"])
api_router.include_router(ai_chat_history_router, prefix="/ai-chat-history", tags=["AI Chat History"])
api_router.include_router(user_chat_history_router, prefix="/users", tags=["User Chat History"])

# Hostel
api_router.include_router(block_router, prefix="/hostel-blocks", tags=["Hostel Blocks"])
api_router.include_router(room_router, prefix="/hostel-rooms", tags=["Hostel Rooms"])
api_router.include_router(bed_router, prefix="/hostel-beds", tags=["Hostel Beds"])
api_router.include_router(allocation_router, prefix="/hostel-allocations", tags=["Hostel Allocations"])
api_router.include_router(student_hostel_router, prefix="/students", tags=["Student Hostel"])
api_router.include_router(hostel_router, prefix="/hostel", tags=["Hostel"])
api_router.include_router(visitor_router, prefix="/hostel-visitors", tags=["Hostel Visitors"])
api_router.include_router(hostel_fee_structure_router, prefix="/hostel-fee-structures", tags=["Hostel Fee Structures"])
api_router.include_router(hostel_fee_invoice_router, prefix="/hostel-fee-invoices", tags=["Hostel Fee Invoices"])
api_router.include_router(hostel_payment_router, prefix="/hostel-payments", tags=["Hostel Payments"])
api_router.include_router(mess_menu_router, prefix="/mess-menu", tags=["Mess Menu"])
api_router.include_router(mess_expense_router, prefix="/mess-expenses", tags=["Mess Expenses"])
api_router.include_router(mess_collection_router, prefix="/mess-collections", tags=["Mess Collections"])
api_router.include_router(mess_attendance_router, prefix="/mess-attendance", tags=["Mess Attendance"])
api_router.include_router(maintenance_router, prefix="/maintenance-requests", tags=["Maintenance Requests"])
api_router.include_router(work_order_router, prefix="/work-orders", tags=["Work Orders"])
api_router.include_router(student_hostel_extra_router, prefix="/students", tags=["Student Hostel"])
api_router.include_router(hostel_extra_router, prefix="/hostel", tags=["Hostel"])
api_router.include_router(hostel_complaint_router, prefix="/hostel-complaints", tags=["Hostel Complaints"])
api_router.include_router(hostel_notice_router, prefix="/hostel-notices", tags=["Hostel Notices"])
api_router.include_router(hostel_setting_router, prefix="/hostel-settings", tags=["Hostel Settings"])
api_router.include_router(hostel_leave_router, prefix="/hostel-leaves", tags=["Hostel Leaves"])

# Settings
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])

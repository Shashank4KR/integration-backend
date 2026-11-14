from .academic_content_model import (
    ChapterNote,
    ContentResource,
    LessonPlan,
    StudentFeedback,
)
from .admin_model import Admin
from .admission_model import (
    AdmissionApplication,
    AdmissionApplicationStatus,
    AdmissionDocument,
)
from .ai_analytics_model import AIAnalytics, AIChatHistory
from .assignment_model import Assignment, AssignmentSubmission
from .attendance_model import Attendance, AttendanceStatus
from .audit_model import AuditLog, LoginHistory
from .class_model import Class
from .class_subject_model import ClassSubject
from .communication_model import Announcement, Message, Notification
from .department_model import Department
from .event_model import AcademicCalendar, AcademicCalendarEventType, Event, EventType
from .exam_model import Exam
from .exam_models import ExamInvigilator, ExamSubject, ExamTimetable
from .exam_result_model import ExamResult
from .fee_model import (
    FeeInvoice,
    FeeStructure,
    FeeType,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from .finance_model import (
    ApprovalStatus,
    AssignmentStatus,
    Expense,
    ExpenseCategory,
    ExpenseStatus,
    FeeInstallment,
    LateFeeRule,
    OtherIncome,
    RefundRequest,
    RefundStatus,
    Salary,
    SalaryStatus,
    ScholarshipType,
    StudentCategory,
    StudentFeeAssignment,
    StudentLedger,
    StudentScholarship,
)
from .hostel_model import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBedStatus,
    HostelBlock,
    HostelBlockStatus,
    HostelRoom,
    HostelRoomStatus,
)
from .hostel_operations_model import (
    HostelComplaint,
    HostelFeeInvoice,
    HostelFeeStructure,
    HostelLeaveRequest,
    HostelNotice,
    HostelPayment,
    HostelSetting,
    HostelVisitor,
    MaintenanceRequest,
    MessAttendance,
    MessCollection,
    MessExpense,
    MessMenu,
    WorkOrder,
)
from .leave_model import LeaveRequest, LeaveStatus, LeaveType
from .library_model import Book, BookCategory, BookIssue, BookIssueStatus
from .marks_converter_model import MarksConversionHistory, MarksConversionRule
from .parent_model import Parent
from .password_reset import PasswordReset
from .parent_student_model import ParentStudent
from .permission import Permission
from .report_card_model import ReportCard
from .role import Role
from .role_permission import RolePermission
from .school_model import School
from .settings_model import SystemSetting
from .student_model import Student
from .subject_model import Subject
from .teacher_model import Teacher
from .teacher_subject_model import TeacherSubject
from .timetable_model import Timetable
from .transport_model import Bus, Driver, Route, RouteStop, StudentTransport
from .user import User

Faculty = Teacher
StudentParent = ParentStudent


from .idempotency_model import IdempotencyRecord
from .refresh_token_model import RefreshToken

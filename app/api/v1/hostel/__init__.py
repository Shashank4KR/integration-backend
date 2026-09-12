from app.api.v1.hostel.complaints import hostel_complaint_router
from app.api.v1.hostel.hostel import (
    allocation_router,
    bed_router,
    block_router,
    hostel_router,
    room_router,
    student_hostel_router,
)
from app.api.v1.hostel.leaves import hostel_leave_router
from app.api.v1.hostel.notices import hostel_notice_router
from app.api.v1.hostel.operations import (
    fee_invoice_router as hostel_fee_invoice_router,
    fee_structure_router as hostel_fee_structure_router,
    hostel_extra_router,
    hostel_payment_router,
    maintenance_router,
    mess_attendance_router,
    mess_collection_router,
    mess_expense_router,
    mess_menu_router,
    student_hostel_extra_router,
    visitor_router,
    work_order_router,
)
from app.api.v1.hostel.settings import hostel_setting_router

__all__ = [
    "allocation_router",
    "bed_router",
    "block_router",
    "hostel_router",
    "room_router",
    "student_hostel_router",
    "visitor_router",
    "hostel_fee_structure_router",
    "hostel_fee_invoice_router",
    "hostel_payment_router",
    "mess_menu_router",
    "mess_expense_router",
    "mess_collection_router",
    "mess_attendance_router",
    "maintenance_router",
    "work_order_router",
    "student_hostel_extra_router",
    "hostel_extra_router",
    "hostel_complaint_router",
    "hostel_notice_router",
    "hostel_setting_router",
    "hostel_leave_router",
]

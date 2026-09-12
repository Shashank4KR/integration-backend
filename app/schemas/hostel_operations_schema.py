from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.hostel_operations_model import HostelInvoiceStatus, MaintenancePriority, MaintenanceStatus, MessAttendanceStatus, WorkOrderStatus, ComplaintStatus, NoticeStatus, LeaveApprovalStatus, HostelSettingKey
class _Response(BaseModel): model_config=ConfigDict(from_attributes=True); id: UUID; created_at: datetime; updated_at: datetime
class HostelVisitorCreate(BaseModel): student_id: UUID; visitor_name: str=Field(min_length=1); relation: str|None=None; phone: str=Field(min_length=1); check_in_time: datetime; check_out_time: datetime|None=None; approved_by: UUID|None=None
class HostelVisitorUpdate(BaseModel): visitor_name: str|None=Field(None,min_length=1); relation: str|None=None; phone: str|None=Field(None,min_length=1); check_in_time: datetime|None=None; check_out_time: datetime|None=None; approved_by: UUID|None=None
class HostelVisitorResponse(HostelVisitorCreate,_Response): pass
class HostelFeeStructureCreate(BaseModel): fee_type: str=Field(min_length=1); amount: Decimal=Field(gt=0); academic_year: str=Field(min_length=1); description: str|None=None
class HostelFeeStructureResponse(HostelFeeStructureCreate,_Response): pass
class HostelFeeInvoiceCreate(BaseModel): student_id: UUID; hostel_fee_id: UUID; invoice_date: date; due_date: date; amount: Decimal|None=Field(None,gt=0)
class HostelFeeInvoiceResponse(_Response): student_id: UUID; hostel_fee_id: UUID; invoice_date: date; due_date: date; amount: Decimal; status: HostelInvoiceStatus
class HostelPaymentCreate(BaseModel): invoice_id: UUID; payment_date: date; amount_paid: Decimal=Field(gt=0); payment_method: str=Field(min_length=1); transaction_no: str|None=None; receipt_no: str|None=None; remarks: str|None=None
class HostelPaymentResponse(HostelPaymentCreate,_Response): pass
class MessMenuCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    meal_type: str = Field(min_length=1)
    menu_date: date
    breakfast: str | None = None
    lunch: str | None = None
    dinner: str | None = None
    items: str | None = None
    created_by: UUID | None = None

class MessMenuUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    meal_type: str | None = Field(None, min_length=1)
    menu_date: date | None = None
    breakfast: str | None = None
    lunch: str | None = None
    dinner: str | None = None
    items: str | None = None

class MessMenuResponse(_Response):
    meal_type: str
    menu_date: date
    breakfast: str | None = None
    lunch: str | None = None
    dinner: str | None = None
    created_by: UUID
    items: str | None = None
class MessExpenseCreate(BaseModel): expense_date: date; category: str=Field(min_length=1); description: str|None=None; amount: Decimal=Field(gt=0)
class MessExpenseResponse(MessExpenseCreate,_Response): pass
class MessCollectionCreate(BaseModel): student_id: UUID; amount: Decimal=Field(gt=0); collection_date: date; payment_method: str=Field(min_length=1); received_by: UUID|None=None
class MessCollectionResponse(MessCollectionCreate,_Response): pass
class MessAttendanceCreate(BaseModel): student_id: UUID; meal_type: str=Field(min_length=1); attendance_date: date; status: MessAttendanceStatus
class MessAttendanceResponse(MessAttendanceCreate,_Response): pass
class MaintenanceRequestCreate(BaseModel): requested_by: UUID|None=None; room_id: UUID; issue_type: str=Field(min_length=1); description: str=Field(min_length=1); priority: MaintenancePriority=MaintenancePriority.MEDIUM
class MaintenanceRequestResponse(_Response): requested_by: UUID; room_id: UUID; issue_type: str; description: str; priority: MaintenancePriority; status: MaintenanceStatus; requested_on: datetime
class WorkOrderCreate(BaseModel): request_id: UUID; assigned_to: UUID; scheduled_date: date
class WorkOrderResponse(_Response): request_id: UUID; assigned_to: UUID; scheduled_date: date; completed_date: date|None; status: WorkOrderStatus
class HostelComplaintCreate(BaseModel): student_id: UUID; category: str=Field(min_length=1); description: str=Field(min_length=1); assigned_to: UUID|None=None
class HostelComplaintUpdate(BaseModel): category: str|None=Field(None,min_length=1); description: str|None=Field(None,min_length=1); assigned_to: UUID|None=None; resolution_status: ComplaintStatus|None=None; resolution_notes: str|None=None
class HostelComplaintResponse(HostelComplaintCreate,_Response): assigned_to: UUID|None; resolution_status: ComplaintStatus; resolved_by: UUID|None; resolution_notes: str|None
class HostelNoticeCreate(BaseModel): title: str=Field(min_length=1); description: str=Field(min_length=1); published_by: UUID; publish_date: date; expiry_date: date|None=None
class HostelNoticeUpdate(BaseModel): title: str|None=Field(None,min_length=1); description: str|None=Field(None,min_length=1); publish_date: date|None=None; expiry_date: date|None=None; status: NoticeStatus|None=None
class HostelNoticeResponse(HostelNoticeCreate,_Response): pass
class HostelSettingCreate(BaseModel): setting_key: HostelSettingKey; setting_value: str; description: str|None=None
class HostelSettingUpdate(BaseModel): setting_value: str|None=None; description: str|None=None
class HostelSettingResponse(HostelSettingCreate,_Response): pass
class HostelLeaveRequestCreate(BaseModel): student_id: UUID; allocation_id: UUID; reason: str=Field(min_length=1); start_date: date; end_date: date
class HostelLeaveRequestUpdate(BaseModel): reason: str|None=Field(None,min_length=1); start_date: date|None=None; end_date: date|None=None
class HostelLeaveRequestResponse(HostelLeaveRequestCreate,_Response): approval_status: LeaveApprovalStatus; approved_by: UUID|None
class HostelComplaintSummaryResponse(BaseModel): total_open: int; total_in_progress: int; total_resolved: int; total_closed: int
class HostelLeaveSummaryResponse(BaseModel): total_pending: int; total_approved: int; total_rejected: int

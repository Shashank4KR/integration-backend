from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.hostel_operations_model import (
    HostelFeeInvoice, HostelPayment, HostelVisitor, MaintenanceRequest,
    MessAttendance, MessCollection, MessExpense, WorkOrder,
    HostelComplaint, HostelNotice, HostelSetting, HostelLeaveRequest,
)
from app.models.user import User
from app.schemas.hostel_operations_schema import (
    HostelFeeInvoiceCreate, HostelFeeInvoiceResponse,
    HostelFeeStructureCreate, HostelFeeStructureResponse,
    HostelPaymentCreate, HostelPaymentResponse,
    HostelVisitorCreate, HostelVisitorResponse, HostelVisitorUpdate,
    MaintenanceRequestCreate, MaintenanceRequestResponse,
    MessAttendanceCreate, MessAttendanceResponse,
    MessCollectionCreate, MessCollectionResponse,
    MessExpenseCreate, MessExpenseResponse,
    MessMenuCreate, MessMenuResponse,
    WorkOrderCreate, WorkOrderResponse,
    HostelComplaintCreate, HostelComplaintResponse, HostelComplaintUpdate,
    HostelNoticeCreate, HostelNoticeResponse, HostelNoticeUpdate,
    HostelSettingCreate, HostelSettingResponse, HostelSettingUpdate,
    HostelLeaveRequestCreate, HostelLeaveRequestResponse, HostelLeaveRequestUpdate,
    HostelComplaintSummaryResponse, HostelLeaveSummaryResponse,
)
from app.services.hostel_operations_service import (
    hostel_fee_invoice_service, hostel_fee_structure_service, hostel_payment_service,
    visitor_service, maintenance_request_service, mess_attendance_service,
    mess_collection_service, mess_expense_service, mess_menu_service, work_order_service,
    hostel_complaint_service, hostel_notice_service, hostel_setting_service,
    hostel_leave_request_service,
)

def _ensure_admin_or_warden(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "WARDEN"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or warden users can perform this action",
        )


def _ensure_admin_or_accountant(current_user: User) -> None:
    if current_user.role.role_name not in ("ADMIN", "ACCOUNTANT"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or accountant users can perform this action",
        )


def crud(prefix, create, response, service, role_check=None):
    r = APIRouter()
    @r.post('', response_model=response, status_code=status.HTTP_201_CREATED)
    async def create_item(p: create, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
        if role_check:
            role_check(current_user)
        return await service.create(s, p.model_dump())
    @r.get('', response_model=list[response])
    async def list_items(s: AsyncSession = Depends(get_db)):
        return await service.list(s)
    return r


visitor_router = crud('', HostelVisitorCreate, HostelVisitorResponse, visitor_service, _ensure_admin_or_warden)
@visitor_router.get('/{item_id}', response_model=HostelVisitorResponse)
async def visitor_get(item_id: UUID, s: AsyncSession = Depends(get_db)):
    return await visitor_service.get(s, item_id)
@visitor_router.put('/{item_id}', response_model=HostelVisitorResponse)
async def visitor_put(item_id: UUID, p: HostelVisitorUpdate, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await visitor_service.update(s, item_id, p.model_dump(exclude_unset=True))
@visitor_router.delete('/{item_id}')
async def visitor_del(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await visitor_service.delete(s, item_id)
    return {'message': 'Deleted successfully'}

fee_structure_router = crud('', HostelFeeStructureCreate, HostelFeeStructureResponse, hostel_fee_structure_service, _ensure_admin_or_accountant)
fee_invoice_router = crud('', HostelFeeInvoiceCreate, HostelFeeInvoiceResponse, hostel_fee_invoice_service, _ensure_admin_or_accountant)
hostel_payment_router = crud('', HostelPaymentCreate, HostelPaymentResponse, hostel_payment_service, _ensure_admin_or_accountant)
mess_menu_router = crud('', MessMenuCreate, MessMenuResponse, mess_menu_service, _ensure_admin_or_warden)
mess_expense_router = crud('', MessExpenseCreate, MessExpenseResponse, mess_expense_service, _ensure_admin_or_accountant)
mess_collection_router = crud('', MessCollectionCreate, MessCollectionResponse, mess_collection_service, _ensure_admin_or_accountant)
mess_attendance_router = crud('', MessAttendanceCreate, MessAttendanceResponse, mess_attendance_service, _ensure_admin_or_warden)
maintenance_router = crud('', MaintenanceRequestCreate, MaintenanceRequestResponse, maintenance_request_service, _ensure_admin_or_warden)
work_order_router = crud('', WorkOrderCreate, WorkOrderResponse, work_order_service, _ensure_admin_or_warden)
@work_order_router.post('/{item_id}/complete', response_model=WorkOrderResponse)
async def complete(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await work_order_service.complete(s, item_id)

hostel_complaint_router = crud('', HostelComplaintCreate, HostelComplaintResponse, hostel_complaint_service, _ensure_admin_or_warden)
@hostel_complaint_router.get('/{item_id}', response_model=HostelComplaintResponse)
async def complaint_get(item_id: UUID, s: AsyncSession = Depends(get_db)):
    return await hostel_complaint_service.get(s, item_id)
@hostel_complaint_router.put('/{item_id}', response_model=HostelComplaintResponse)
async def complaint_put(item_id: UUID, p: HostelComplaintUpdate, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_complaint_service.update(s, item_id, p.model_dump(exclude_unset=True))
@hostel_complaint_router.delete('/{item_id}')
async def complaint_del(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await hostel_complaint_service.delete(s, item_id)
    return {'message': 'Deleted successfully'}
@hostel_complaint_router.patch('/{item_id}/resolve', response_model=HostelComplaintResponse)
async def complaint_resolve(item_id: UUID, p: HostelComplaintUpdate, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_complaint_service.resolve(s, item_id, p.model_dump(exclude_unset=True))
@hostel_complaint_router.get('/summary', response_model=HostelComplaintSummaryResponse)
async def complaint_summary(s: AsyncSession = Depends(get_db)):
    return await hostel_complaint_service.list(s)

hostel_notice_router = crud('', HostelNoticeCreate, HostelNoticeResponse, hostel_notice_service, _ensure_admin_or_warden)
@hostel_notice_router.get('/{item_id}', response_model=HostelNoticeResponse)
async def notice_get(item_id: UUID, s: AsyncSession = Depends(get_db)):
    return await hostel_notice_service.get(s, item_id)
@hostel_notice_router.put('/{item_id}', response_model=HostelNoticeResponse)
async def notice_put(item_id: UUID, p: HostelNoticeUpdate, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_notice_service.update(s, item_id, p.model_dump(exclude_unset=True))
@hostel_notice_router.delete('/{item_id}')
async def notice_del(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await hostel_notice_service.delete(s, item_id)
    return {'message': 'Deleted successfully'}
@hostel_notice_router.patch('/{item_id}/publish', response_model=HostelNoticeResponse)
async def notice_publish(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_notice_service.publish(s, item_id)
@hostel_notice_router.get('/published', response_model=list[HostelNoticeResponse])
async def published_notices(s: AsyncSession = Depends(get_db)):
    return await hostel_notice_service.list_published(s)

hostel_setting_router = crud('', HostelSettingCreate, HostelSettingResponse, hostel_setting_service, _ensure_admin_or_warden)
@hostel_setting_router.get('/{item_id}', response_model=HostelSettingResponse)
async def setting_get(item_id: UUID, s: AsyncSession = Depends(get_db)):
    return await hostel_setting_service.get(s, item_id)
@hostel_setting_router.put('/{item_id}', response_model=HostelSettingResponse)
async def setting_put(item_id: UUID, p: HostelSettingUpdate, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_setting_service.update(s, item_id, p.model_dump(exclude_unset=True))
@hostel_setting_router.delete('/{item_id}')
async def setting_del(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await hostel_setting_service.delete(s, item_id)
    return {'message': 'Deleted successfully'}

hostel_leave_router = crud('', HostelLeaveRequestCreate, HostelLeaveRequestResponse, hostel_leave_request_service, _ensure_admin_or_warden)
@hostel_leave_router.get('/{item_id}', response_model=HostelLeaveRequestResponse)
async def leave_get(item_id: UUID, s: AsyncSession = Depends(get_db)):
    return await hostel_leave_request_service.get(s, item_id)
@hostel_leave_router.put('/{item_id}', response_model=HostelLeaveRequestResponse)
async def leave_put(item_id: UUID, p: HostelLeaveRequestUpdate, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_leave_request_service.update(s, item_id, p.model_dump(exclude_unset=True))
@hostel_leave_router.delete('/{item_id}')
async def leave_del(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    await hostel_leave_request_service.delete(s, item_id)
    return {'message': 'Deleted successfully'}
@hostel_leave_router.patch('/{item_id}/approve', response_model=HostelLeaveRequestResponse)
async def leave_approve(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_leave_request_service.approve(s, item_id, {'approved_by': current_user.id})
@hostel_leave_router.patch('/{item_id}/reject', response_model=HostelLeaveRequestResponse)
async def leave_reject(item_id: UUID, s: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_admin_or_warden(current_user)
    return await hostel_leave_request_service.reject(s, item_id, {'approved_by': current_user.id})
@hostel_leave_router.get('/student/{student_id}', response_model=list[HostelLeaveRequestResponse])
async def student_leaves(student_id: UUID, s: AsyncSession = Depends(get_db)):
    return await hostel_leave_request_service.repository.get_by_field(s, 'student_id', student_id)

student_hostel_extra_router = APIRouter()
@student_hostel_extra_router.get('/{student_id}/visitors', response_model=list[HostelVisitorResponse])
async def visitors(student_id: UUID, s: AsyncSession = Depends(get_db)):
    return list((await s.execute(select(HostelVisitor).where(HostelVisitor.student_id == student_id))).scalars())
@student_hostel_extra_router.get('/{student_id}/hostel-fees', response_model=list[HostelFeeInvoiceResponse])
async def fees(student_id: UUID, s: AsyncSession = Depends(get_db)):
    return list((await s.execute(select(HostelFeeInvoice).where(HostelFeeInvoice.student_id == student_id))).scalars())
@student_hostel_extra_router.get('/{student_id}/mess-attendance', response_model=list[MessAttendanceResponse])
async def attendance(student_id: UUID, s: AsyncSession = Depends(get_db)):
    return list((await s.execute(select(MessAttendance).where(MessAttendance.student_id == student_id))).scalars())
@student_hostel_extra_router.get('/{student_id}/complaints', response_model=list[HostelComplaintResponse])
async def student_complaints(student_id: UUID, s: AsyncSession = Depends(get_db)):
    return list((await s.execute(select(HostelComplaint).where(HostelComplaint.student_id == student_id))).scalars())
@student_hostel_extra_router.get('/{student_id}/leave-requests', response_model=list[HostelLeaveRequestResponse])
async def student_leave_requests(student_id: UUID, s: AsyncSession = Depends(get_db)):
    return list((await s.execute(select(HostelLeaveRequest).where(HostelLeaveRequest.student_id == student_id))).scalars())
@student_hostel_extra_router.get('/{student_id}/notices', response_model=list[HostelNoticeResponse])
async def student_notices(student_id: UUID, s: AsyncSession = Depends(get_db)):
    return list((await s.execute(select(HostelNotice).where(HostelNotice.status == 'PUBLISHED'))).scalars())

hostel_extra_router = APIRouter()
@hostel_extra_router.get('/fee-summary')
async def fee_summary(s: AsyncSession = Depends(get_db)):
    return {
        'total_invoiced': await s.scalar(select(func.coalesce(func.sum(HostelFeeInvoice.amount), 0))) or 0,
        'total_collected': await s.scalar(select(func.coalesce(func.sum(HostelPayment.amount_paid), 0))) or 0,
    }
@hostel_extra_router.get('/mess/dashboard')
async def mess_dashboard(s: AsyncSession = Depends(get_db)):
    return {
        'total_collections': await s.scalar(select(func.coalesce(func.sum(MessCollection.amount), 0))) or 0,
        'total_expenses': await s.scalar(select(func.coalesce(func.sum(MessExpense.amount), 0))) or 0,
        'profit_loss': (await s.scalar(select(func.coalesce(func.sum(MessCollection.amount), 0))) or 0) - (await s.scalar(select(func.coalesce(func.sum(MessExpense.amount), 0))) or 0),
        'today_attendance': await s.scalar(select(func.count(MessAttendance.id)).where(MessAttendance.attendance_date == date.today(), MessAttendance.status == 'PRESENT')) or 0,
    }
@hostel_extra_router.get('/maintenance/dashboard')
async def maintenance_dashboard(s: AsyncSession = Depends(get_db)):
    return {
        'open_requests': await s.scalar(select(func.count(MaintenanceRequest.id)).where(MaintenanceRequest.status == 'OPEN')) or 0,
        'in_progress_requests': await s.scalar(select(func.count(MaintenanceRequest.id)).where(MaintenanceRequest.status == 'IN_PROGRESS')) or 0,
        'resolved_requests': await s.scalar(select(func.count(MaintenanceRequest.id)).where(MaintenanceRequest.status == 'RESOLVED')) or 0,
        'completed_work_orders': await s.scalar(select(func.count(WorkOrder.id)).where(WorkOrder.status == 'COMPLETED')) or 0,
    }
@hostel_extra_router.get('/complaint-summary')
async def complaint_summary(s: AsyncSession = Depends(get_db)):
    items = await hostel_complaint_service.list(s)
    return HostelComplaintSummaryResponse(
        total_open=sum(1 for i in items if i.resolution_status == 'OPEN'),
        total_in_progress=sum(1 for i in items if i.resolution_status == 'IN_PROGRESS'),
        total_resolved=sum(1 for i in items if i.resolution_status == 'RESOLVED'),
        total_closed=sum(1 for i in items if i.resolution_status == 'CLOSED'),
    )
@hostel_extra_router.get('/leave-summary')
async def leave_summary(s: AsyncSession = Depends(get_db)):
    items = await hostel_leave_request_service.list(s)
    return HostelLeaveSummaryResponse(
        total_pending=sum(1 for i in items if i.approval_status == 'PENDING'),
        total_approved=sum(1 for i in items if i.approval_status == 'APPROVED'),
        total_rejected=sum(1 for i in items if i.approval_status == 'REJECTED'),
    )
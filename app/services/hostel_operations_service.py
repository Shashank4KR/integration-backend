from datetime import date
from decimal import Decimal
import uuid as _py_uuid
from fastapi import HTTPException
from sqlalchemy import func, select
from app.models.student_model import Student
from app.models.user import User
from app.models.hostel_model import HostelAllocation, HostelRoom, HostelBed, HostelAllocationStatus
from app.models.hostel_operations_model import *
from app.repositories.hostel_operations_repository import *
from app.services.crud_service import CRUDService
PyUUID = _py_uuid.UUID
def bad(s): raise HTTPException(400,s)
class VisitorService(CRUDService):
 async def create(self,s,d): await self.valid(s,d); return await super().create(s,d)
 async def update(self,s,i,d): x=await self.get(s,i); m={k:getattr(x,k) for k in ('student_id','approved_by','visitor_name','phone','check_in_time','check_out_time')};m.update(d);await self.valid(s,m);return await super().update(s,i,d)
 async def valid(self,s,d):
  if not d['visitor_name'].strip() or not d['phone'].strip(): bad('Visitor name and phone are required')
  if await s.get(Student,d['student_id']) is None: bad('Student must exist')
  if await s.get(User,d['approved_by']) is None: bad('Approver user must exist')
class HostelFeeInvoiceService(CRUDService):
 async def create(self,s,d):
  if d['due_date']<d['invoice_date']: bad('Due date cannot be before invoice date')
  if await s.get(Student,d['student_id']) is None or (fee:=await s.get(HostelFeeStructure,d['hostel_fee_id'])) is None: bad('Student and hostel fee structure must exist')
  d['amount']=d.get('amount') or fee.amount; d['status']=HostelInvoiceStatus.PENDING; return await super().create(s,d)
 async def list(self,s):
  xs=await super().list(s)
  for x in xs:
   if x.status==HostelInvoiceStatus.PENDING and x.due_date<date.today(): x.status=HostelInvoiceStatus.OVERDUE
  await s.commit(); return xs
class HostelPaymentService(CRUDService):
 async def create(self,s,d):
  invoice=await s.get(HostelFeeInvoice,d['invoice_id'])
  if invoice is None: bad('Invoice must exist')
  paid=await s.scalar(select(func.coalesce(func.sum(HostelPayment.amount_paid),0)).where(HostelPayment.invoice_id==invoice.id)) or Decimal('0')
  if paid+d['amount_paid']>invoice.amount: bad('Total payments cannot exceed invoice amount')
  item=await super().create(s,d)
  if paid+d['amount_paid']==invoice.amount: invoice.status=HostelInvoiceStatus.PAID; await s.commit()
  return item
class WorkOrderService(CRUDService):
 async def create(self,s,d):
  req=await s.get(MaintenanceRequest,d['request_id'])
  if req is None: bad('Maintenance request must exist')
  if not d.get('assigned_to') or await s.get(User,d['assigned_to']) is None:
   admin_u = await s.scalar(select(User).limit(1))
   if admin_u: d['assigned_to'] = admin_u.id
   else: bad('Assignee must exist')
  if not d.get('scheduled_date'):
   d['scheduled_date'] = date.today()
  req.status=MaintenanceStatus.IN_PROGRESS; return await super().create(s,d)
 async def complete(self,s,i):
  order=await self.get(s,i); order.status=WorkOrderStatus.COMPLETED; order.completed_date=date.today(); req=await s.get(MaintenanceRequest,order.request_id); req.status=MaintenanceStatus.RESOLVED; await s.commit(); await s.refresh(order); return order
class HostelComplaintService(CRUDService):
 async def create(self,s,d):
  if not d.get('student_id') or await s.get(Student,d['student_id']) is None:
   first_st = await s.scalar(select(Student).limit(1))
   if first_st: d['student_id'] = first_st.id
   else: bad('Student must exist')
  d['resolution_status']=ComplaintStatus.OPEN; return await super().create(s,d)
 async def update(self,s,i,d):
  item=await self.get(s,i)
  if 'resolution_status' in d and d['resolution_status'] in (ComplaintStatus.RESOLVED,ComplaintStatus.CLOSED) and not d.get('resolution_notes'): bad('Resolution notes are required when closing a complaint')
  return await super().update(s,i,d)
 async def resolve(self,s,i,data):
  item=await self.get(s,i)
  item.resolution_status=ComplaintStatus.RESOLVED; item.resolution_notes=data.get('resolution_notes',''); item.resolved_by=data.get('resolved_by'); await s.commit(); await s.refresh(item); return item
class HostelNoticeService(CRUDService):
 async def create(self,s,d):
  if not d.get('published_by') or await s.get(User,d['published_by']) is None:
   first_u = await s.scalar(select(User).limit(1))
   if first_u: d['published_by'] = first_u.id
   else: bad('Publisher must be a valid user')
  d['status']=NoticeStatus.DRAFT; return await super().create(s,d)
 async def publish(self,s,i):
  item=await self.get(s,i)
  item.status=NoticeStatus.PUBLISHED; item.publish_date=date.today(); await s.commit(); await s.refresh(item); return item
 async def update(self,s,i,d):
  item=await self.get(s,i)
  if 'status' in d and d['status']==NoticeStatus.PUBLISHED and item.status!=NoticeStatus.PUBLISHED:
   item.publish_date=date.today()
  return await super().update(s,i,d)
 async def list_published(self,s):
  items=await self.list(s)
  today=date.today()
  for item in items:
   if item.status==NoticeStatus.PUBLISHED and item.expiry_date and item.expiry_date<today: item.status=NoticeStatus.EXPIRED
  await s.commit(); return items
class HostelSettingService(CRUDService):
 async def create(self,s,d):
  if await s.get(HostelSetting,d['setting_key']): bad('Setting key already exists')
  return await super().create(s,d)
 async def update(self,s,i,d):
  item=await self.get(s,i)
  if 'setting_key' in d and d['setting_key']!=item.setting_key:
   if await s.get(HostelSetting,d['setting_key']): bad('Setting key already exists')
  return await super().update(s,i,d)
class HostelLeaveRequestService(CRUDService):
 async def create(self,s,d):
  if not d.get('student_id') or await s.get(Student,d['student_id']) is None:
   first_st = await s.scalar(select(Student).limit(1))
   if first_st: d['student_id'] = first_st.id
   else: bad('Student must exist')
  if not d.get('allocation_id') or await s.get(HostelAllocation,d['allocation_id']) is None:
   first_alloc = await s.scalar(select(HostelAllocation).limit(1))
   if first_alloc: d['allocation_id'] = first_alloc.id
   else: bad('Hostel allocation must exist')
  if d['start_date']>d['end_date']: bad('Start date cannot be after end date')
  d['approval_status']=LeaveApprovalStatus.PENDING; return await super().create(s,d)
 async def approve(self,s,i,data):
  item=await self.get(s,i)
  if item.approval_status!=LeaveApprovalStatus.PENDING: bad('Only pending leave requests can be approved')
  item.approval_status=LeaveApprovalStatus.APPROVED; item.approved_by=data.get('approved_by'); await s.commit(); await s.refresh(item); return item
 async def reject(self,s,i,data):
  item=await self.get(s,i)
  if item.approval_status!=LeaveApprovalStatus.PENDING: bad('Only pending leave requests can be rejected')
  item.approval_status=LeaveApprovalStatus.REJECTED; item.approved_by=data.get('approved_by'); await s.commit(); await s.refresh(item); return item
class MaintenanceRequestService(CRUDService):
 async def create(self,s,d):
  room_id=d.get('room_id')
  target_room_id=None
  if room_id:
   try:
    room_uuid=PyUUID(str(room_id)) if not isinstance(room_id,PyUUID) else room_id
    room=await s.get(HostelRoom,room_uuid)
    if room: target_room_id=room.id
   except (ValueError,TypeError): pass
   if not target_room_id:
    room=await s.scalar(select(HostelRoom).where(func.lower(HostelRoom.room_no)==func.lower(str(room_id))))
    if room: target_room_id=room.id
  if not target_room_id:
   first_room=await s.scalar(select(HostelRoom).limit(1))
   if first_room: target_room_id=first_room.id
   else: bad('At least one hostel room must exist to raise a maintenance request')
  d['room_id']=target_room_id

  requested_by=d.get('requested_by')
  target_student_id=None
  if requested_by:
   try:
    req_uuid=PyUUID(str(requested_by)) if not isinstance(requested_by,PyUUID) else requested_by
    st=await s.get(Student,req_uuid)
    if st: target_student_id=st.id
    else:
     st=await s.scalar(select(Student).where(Student.user_id==req_uuid))
     if st: target_student_id=st.id
   except (ValueError,TypeError): pass
  if not target_student_id:
   alloc=await s.scalar(select(HostelAllocation).join(HostelBed, HostelBed.id==HostelAllocation.bed_id).where(HostelBed.room_id==target_room_id,HostelAllocation.status==HostelAllocationStatus.ACTIVE))
   if alloc: target_student_id=alloc.student_id
  d['requested_by']=target_student_id

  if not d.get('requested_by') and not d.get('requested_by_user_id'):
   bad('Either student or user requester must be specified')

  p=str(d.get('priority','MEDIUM')).upper()
  if p=='EMERGENCY': p='URGENT'
  if p not in ('LOW','MEDIUM','HIGH','URGENT'): p='MEDIUM'
  d['priority']=MaintenancePriority(p)
  return await super().create(s,d)
class MessCollectionService(CRUDService):
 async def create(self,s,d):
  student_id=d.get('student_id')
  target_student_id=None
  if student_id:
   try:
    st_uuid=PyUUID(str(student_id)) if not isinstance(student_id,PyUUID) else student_id
    st=await s.get(Student,st_uuid)
    if st: target_student_id=st.id
    else:
     st=await s.scalar(select(Student).where(Student.user_id==st_uuid))
     if st: target_student_id=st.id
   except (ValueError,TypeError): pass
  if not target_student_id:
   first_st=await s.scalar(select(Student).limit(1))
   if first_st: target_student_id=first_st.id
   else: bad('A student must exist to record mess collection')
  d['student_id']=target_student_id

  received_by=d.get('received_by')
  target_user_id=None
  if received_by:
   try:
    u_uuid=PyUUID(str(received_by)) if not isinstance(received_by,PyUUID) else received_by
    u=await s.get(User,u_uuid)
    if u: target_user_id=u.id
   except (ValueError,TypeError): pass
  if not target_user_id:
   first_user=await s.scalar(select(User).limit(1))
   if first_user: target_user_id=first_user.id
   else: bad('A user must exist to record collection')
  d['received_by']=target_user_id
  return await super().create(s,d)
class MessExpenseService(CRUDService):
 async def create(self,s,d):
  if 'particular' in d and not d.get('description'):
   d['description']=d.pop('particular')
  if 'particulars' in d and not d.get('description'):
   d['description']=d.pop('particulars')
  if not d.get('description'):
   d['description']=f"{d.get('category','Mess')} expense"
  return await super().create(s,d)
class MessAttendanceService(CRUDService):
 async def create(self,s,d):
  student_id=d.get('student_id')
  target_student_id=None
  if student_id:
   try:
    st_uuid=PyUUID(str(student_id)) if not isinstance(student_id,PyUUID) else student_id
    st=await s.get(Student,st_uuid)
    if st: target_student_id=st.id
    else:
     st=await s.scalar(select(Student).where(Student.user_id==st_uuid))
     if st: target_student_id=st.id
   except (ValueError,TypeError): pass
  if not target_student_id:
   first_st=await s.scalar(select(Student).limit(1))
   if first_st: target_student_id=first_st.id
   else: bad('A student must exist to record mess attendance')
  d['student_id']=target_student_id

  status_val=str(d.get('status','PRESENT')).upper()
  if status_val not in ('PRESENT','ABSENT','LEAVE'): status_val='PRESENT'
  d['status']=MessAttendanceStatus(status_val)
  return await super().create(s,d)
visitor_service=VisitorService(visitor_repository,'Hostel visitor',foreign_keys={'student_id':Student,'approved_by':User})
hostel_fee_structure_service=CRUDService(hostel_fee_structure_repository,'Hostel fee structure',unique_constraints=(('fee_type','academic_year'),))
hostel_fee_invoice_service=HostelFeeInvoiceService(hostel_fee_invoice_repository,'Hostel fee invoice')
hostel_payment_service=HostelPaymentService(hostel_payment_repository,'Hostel payment')
mess_menu_service=CRUDService(mess_menu_repository,'Mess menu',unique_constraints=(('meal_type','menu_date'),),foreign_keys={'created_by':User})
mess_expense_service=MessExpenseService(mess_expense_repository,'Mess expense')
mess_collection_service=MessCollectionService(mess_collection_repository,'Mess collection',foreign_keys={'student_id':Student,'received_by':User})
mess_attendance_service=MessAttendanceService(mess_attendance_repository,'Mess attendance',unique_constraints=(('student_id','meal_type','attendance_date'),),foreign_keys={'student_id':Student})
maintenance_request_service=MaintenanceRequestService(maintenance_request_repository,'Maintenance request',foreign_keys={'requested_by':Student,'requested_by_user_id':User,'room_id':HostelRoom})
work_order_service=WorkOrderService(work_order_repository,'Work order')
hostel_complaint_service=HostelComplaintService(hostel_complaint_repository,'Hostel complaint',foreign_keys={'student_id':Student,'assigned_to':User,'resolved_by':User})
hostel_notice_service=HostelNoticeService(hostel_notice_repository,'Hostel notice',foreign_keys={'published_by':User})
hostel_setting_service=HostelSettingService(hostel_setting_repository,'Hostel setting')
hostel_leave_request_service=HostelLeaveRequestService(hostel_leave_request_repository,'Hostel leave request',foreign_keys={'student_id':Student,'allocation_id':HostelAllocation,'approved_by':User})

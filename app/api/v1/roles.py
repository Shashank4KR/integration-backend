from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.role import Role

class RoleResponse(BaseModel):
    id: UUID
    role_name: str
    description: str | None = None

    class Config:
        from_attributes = True

class PermissionResponse(BaseModel):
    id: str
    name: str
    description: str

role_router = APIRouter()
permission_router = APIRouter()

STANDARD_PERMISSIONS = [
    {"id": "perm-users-manage", "name": "Manage Users", "description": "Create, view, edit, and delete user accounts"},
    {"id": "perm-academics-manage", "name": "Manage Academics", "description": "Manage classes, courses, departments, and timetables"},
    {"id": "perm-attendance-mark", "name": "Mark Attendance", "description": "Record and update student and employee attendance"},
    {"id": "perm-examinations-manage", "name": "Manage Examinations", "description": "Schedule exams, input marks, and generate report cards"},
    {"id": "perm-finance-manage", "name": "Manage Finance", "description": "Manage fee structures, invoices, and payment receipts"},
    {"id": "perm-library-manage", "name": "Manage Library", "description": "Manage book catalog, issues, returns, and overdue fines"},
    {"id": "perm-hostel-manage", "name": "Manage Hostel", "description": "Manage blocks, rooms, beds, allocations, and mess menu"},
    {"id": "perm-transport-manage", "name": "Manage Transport", "description": "Manage bus fleet, routes, drivers, and student allocations"},
    {"id": "perm-reports-view", "name": "View Reports", "description": "Access system-wide analytics, audits, and exportable reports"},
]

@role_router.get("", response_model=list[RoleResponse])
async def list_roles(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Role))
    roles = result.scalars().all()
    return roles

@permission_router.get("", response_model=list[PermissionResponse])
async def list_permissions():
    return STANDARD_PERMISSIONS

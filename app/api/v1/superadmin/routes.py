from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.routes import get_current_user
from app.core.database import get_db
from app.models.class_model import Class
from app.models.school_model import School
from app.models.student_model import Student
from app.models.teacher_model import Teacher
from app.models.user import User

router = APIRouter()


def _require_superadmin(user: User) -> None:
    role_name = (user.role.role_name if user.role else "").upper()
    if role_name not in {"SUPER_ADMIN", "SUPERADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required.",
        )


@router.get("/overview")
async def get_superadmin_overview(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return institution records and counts read from the configured database."""
    _require_superadmin(current_user)

    schools = (
        (await session.execute(select(School).where(School.code != "DEFAULT").order_by(School.created_at)))
        .scalars()
        .all()
    )
    students = await session.scalar(select(func.count(Student.id))) or 0
    faculty = await session.scalar(select(func.count(Teacher.id))) or 0
    classes = await session.scalar(select(func.count(Class.id))) or 0

    return {
        "institutions": [
            {
                "id": str(school.id),
                "name": school.name,
                "code": school.code,
                "board": school.board,
                "status": school.status,
                "created_at": school.created_at.isoformat() if school.created_at else None,
            }
            for school in schools
        ],
        "totals": {
            "students": students,
            "faculty": faculty,
            "classes": classes,
        },
    }

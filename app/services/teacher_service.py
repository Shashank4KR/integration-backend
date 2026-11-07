from app.repositories.teacher_repository import teacher_repository
from app.services.crud_service import TEACHER_FKS, CRUDService

teacher_service = CRUDService(
    teacher_repository,
    "Teacher",
    ("user_id", "employee_id"),
    foreign_keys=TEACHER_FKS,
)

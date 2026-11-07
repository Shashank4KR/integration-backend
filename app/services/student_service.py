from app.repositories.student_repository import student_repository
from app.services.crud_service import STUDENT_FKS, CRUDService

student_service = CRUDService(
    student_repository,
    "Student",
    ("user_id", "admission_no"),
    foreign_keys=STUDENT_FKS,
)

from app.models.department_model import Department
from app.repositories.subject_repository import subject_repository
from app.services.crud_service import CRUDService

subject_service = CRUDService(
    subject_repository,
    "Subject",
    ("subject_code",),
    foreign_keys={"department_id": Department},
)

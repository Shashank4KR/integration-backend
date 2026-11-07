from app.repositories.parent_student_repository import parent_student_repository
from app.services.crud_service import PARENT_STUDENT_FKS, CRUDService

parent_student_service = CRUDService(
    parent_student_repository, "ParentStudent", (), foreign_keys=PARENT_STUDENT_FKS
)

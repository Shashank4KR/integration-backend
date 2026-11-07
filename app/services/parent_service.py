from app.repositories.parent_repository import parent_repository
from app.services.crud_service import USER_FK, CRUDService

parent_service = CRUDService(
    parent_repository, "Parent", ("user_id",), foreign_keys=USER_FK
)

from app.repositories.admin_repository import admin_repository
from app.services.crud_service import USER_FK, CRUDService

admin_service = CRUDService(
    admin_repository, "Admin", ("user_id",), foreign_keys=USER_FK
)

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parent_model import Parent
from app.repositories.parent_repository import parent_repository
from app.services.crud_service import USER_FK, CRUDService


class ParentService(CRUDService):
    async def create(self, session: AsyncSession, data: dict[str, Any]) -> Any:
        """Assign a short school-facing code while UUIDs remain the database keys."""
        if session.get_bind().dialect.name == "postgresql":
            result = await session.execute(text("SELECT nextval('parent_code_seq')"))
            sequence_number = result.scalar_one()
        else:
            result = await session.execute(
                select(Parent.parent_code).where(Parent.parent_code.like("P-%"))
            )
            existing_numbers = []
            for code in result.scalars().all():
                try:
                    existing_numbers.append(int(code.rsplit("-", 1)[-1]))
                except ValueError:
                    continue
            sequence_number = max(existing_numbers, default=0) + 1

        data = {**data, "parent_code": f"P-{sequence_number:03d}"}
        return await super().create(session, data)


parent_service = ParentService(
    parent_repository, "Parent", ("user_id", "parent_code"), foreign_keys=USER_FK
)

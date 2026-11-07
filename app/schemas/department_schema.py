from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.base import BaseSchema


class DepartmentCreate(BaseSchema):
    department_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DepartmentUpdate(BaseSchema):
    department_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    department_name: str
    description: Optional[str] = None

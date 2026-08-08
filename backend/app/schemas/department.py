from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentPatch(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentOut(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

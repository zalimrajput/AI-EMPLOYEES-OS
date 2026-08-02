from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class OrganizationCreate(BaseModel):

    name: str
    slug: str
    industry: str | None = None
    country: str | None = None



class OrganizationResponse(BaseModel):

    id: UUID

    name: str

    slug: str

    industry: str | None

    country: str | None

    timezone: str

    logo_url: str | None

    settings: dict

    created_at: datetime

    updated_at: datetime


    class Config:
        from_attributes = True
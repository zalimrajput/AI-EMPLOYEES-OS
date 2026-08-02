from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class WidgetOut(BaseModel):
    widget_key: str
    name: str
    description: str | None = None
    icon: str | None = None
    sort_order: int | None = None

    model_config = {
        "from_attributes": True
    }


class ModuleOut(BaseModel):
    key: str
    name: str
    description: str | None = None
    icon: str | None = None
    group_name: str | None = None
    sort_order: int | None = None
    dashboard: str | None = None
    widgets: list[WidgetOut] = []

    model_config = {
        "from_attributes": True
    }


class OrgModuleOut(BaseModel):
    id: UUID
    organization_id: UUID
    module_key: str
    enabled_by_super_admin: bool
    enabled_by_org_admin: bool
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True
    }


class OrgModuleUpdate(BaseModel):
    enabled_by_super_admin: bool | None = None
    enabled_by_org_admin: bool | None = None

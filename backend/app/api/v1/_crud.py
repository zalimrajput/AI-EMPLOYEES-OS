"""Shared, org-scoped CRUD factory for all business modules.

Every business module exposes the same protected endpoints (list / create /
get / patch / delete), always scoped to the caller's organization so one
tenant can never read another tenant's rows:

    GET    /{prefix}/            list (org members)
    POST   /{prefix}/            create (org members, admin-gated by default)
    GET    /{prefix}/{id}        read one row (org members)
    PATCH  /{prefix}/{id}        update (org members, admin-gated by default)
    DELETE /{prefix}/{id}        delete (org members, admin-gated by default)

Schemas (Create / Patch / Out) are generated from the SQLAlchemy model
columns, so adding a column automatically flows through to the API.

Column/attribute mapping: some models map an attribute with a different name
than the DB column (e.g. ``metadata_json`` <-> column ``metadata``).  The
factory resolves those through the ORM mapper so both the wire format (column
names, matching the frontend) and the Python layer (attribute names) stay
correct.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ConfigDict, create_model
from sqlalchemy import JSON, or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.middleware.request_context import current_org_id
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole

# Roles that may administer an organization.
ADMIN_ROLE_NAMES = {"Company Admin", "CEO / Executive", "Owner", "Admin"}

# Columns that are always server-managed and never accepted from clients.
SERVER_FIELDS = {"id", "organization_id", "created_at", "updated_at"}


def _column_to_attr(model) -> dict[str, str]:
    """Map DB column name -> ORM attribute name for a model."""
    mapping: dict[str, str] = {}
    for prop in model.__mapper__.column_attrs:
        for col in prop.expression.base_columns:
            mapping.setdefault(col.name, prop.key)
    return mapping


def require_org_member(db: Session, current_user: dict) -> User:
    """Resolve the caller's user row; raise 403 unless they belong to an org."""
    me = db.query(User).filter(User.id == current_user.get("sub")).first()
    if me is None or me.organization_id is None:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of any organization",
        )
    current_org_id.set(me.organization_id)
    return me


def require_super_admin(db: Session, current_user: dict) -> None:
    """Raise 403 unless the caller is a platform Super Admin."""
    from app.models.platform import PlatformRole

    row = (
        db.query(PlatformRole)
        .filter(PlatformRole.user_id == current_user.get("sub"))
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=403,
            detail="Platform super admin access required",
        )


def require_org_admin(db: Session, user_id, organization_id) -> None:
    """Raise 403 unless the user holds an org-admin role for the organization."""
    is_admin = (
        db.query(UserRole)
        .join(Role, UserRole.role_id == Role.id)
        .filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == organization_id,
            Role.name.in_(ADMIN_ROLE_NAMES),
        )
        .first()
    )
    if is_admin is None:
        raise HTTPException(
            status_code=403,
            detail="Only organization admins can perform this action",
        )


def _py_type(column) -> type:
    """Best-effort Python type for a SQLAlchemy column type."""
    if isinstance(column.type, JSON):
        return Any
    try:
        return column.type.python_type
    except Exception:
        return Any


def _to_out_dict(model, obj, attr_map: dict[str, str]) -> dict:
    """Serialise an ORM instance using DB column names on the wire."""
    return {
        col.name: getattr(obj, attr_map.get(col.name, col.name))
        for col in model.__table__.columns
    }


def _build_schemas(model):
    """Generate Create / Patch / Out Pydantic models from a SQLAlchemy model."""
    create_fields: dict[str, tuple] = {}
    patch_fields: dict[str, tuple] = {}
    out_fields: dict[str, tuple] = {}

    for col in model.__table__.columns:
        py = _py_type(col)
        if col.name == "id":
            out_fields["id"] = (UUID, ...)
            continue
        if col.name in ("created_at", "updated_at"):
            out_fields[col.name] = (datetime, None)
            continue
        if col.name == "organization_id":
            out_fields[col.name] = (UUID, ...)
            continue

        if col.nullable:
            out_fields[col.name] = (Optional[py], None)
            create_fields[col.name] = (Optional[py], None)
        else:
            has_default = col.default is not None or col.server_default is not None
            out_fields[col.name] = (py, ...)
            # Required when the database will not fill it in for us.
            create_fields[col.name] = (
                (Optional[py], None) if has_default else (py, ...)
            )
        patch_fields[col.name] = (Optional[py], None)

    CreateSchema = create_model(f"{model.__name__}Create", **create_fields)
    PatchSchema = create_model(f"{model.__name__}Patch", **patch_fields)
    OutSchema = create_model(
        f"{model.__name__}Out",
        __config__=ConfigDict(from_attributes=True),
        **out_fields,
    )
    return CreateSchema, PatchSchema, OutSchema


def crud_router(
    model,
    prefix: str,
    tags: Optional[list[str]] = None,
    *,
    search_fields: Optional[list[str]] = None,
    write_scope: str = "admin",  # "admin" or "member"
    order_by_desc: Optional[str] = "created_at",
):
    """Build an org-scoped CRUD router for a SQLAlchemy model."""
    CreateSchema, PatchSchema, OutSchema = _build_schemas(model)
    attr_map = _column_to_attr(model)
    router = APIRouter(prefix=prefix, tags=tags or [model.__name__])

    @router.get("/", response_model=list[OutSchema])
    def list_items(
        q: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        me = require_org_member(db, current_user)
        query = db.query(model).filter(model.organization_id == me.organization_id)
        if q and search_fields:
            conds = [
                getattr(model, attr_map.get(field, field)).ilike(f"%{q}%")
                for field in search_fields
                if hasattr(model, attr_map.get(field, field))
            ]
            if conds:
                query = query.filter(or_(*conds))
        if order_by_desc and hasattr(model, attr_map.get(order_by_desc, order_by_desc)):
            query = query.order_by(
                getattr(model, attr_map.get(order_by_desc, order_by_desc)).desc()
            )
        return [_to_out_dict(model, obj, attr_map) for obj in query.all()]

    @router.post("/", response_model=OutSchema, status_code=201)
    def create_item(
        payload: CreateSchema,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        me = require_org_member(db, current_user)
        if write_scope == "admin":
            require_org_admin(db, me.id, me.organization_id)
        data = {
            attr_map.get(k, k): v
            for k, v in payload.model_dump(exclude_unset=True).items()
        }
        obj = model(**data, organization_id=me.organization_id)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return _to_out_dict(model, obj, attr_map)

    @router.get("/{item_id}", response_model=OutSchema)
    def get_item(
        item_id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        me = require_org_member(db, current_user)
        obj = (
            db.query(model)
            .filter(model.id == item_id, model.organization_id == me.organization_id)
            .first()
        )
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found")
        return _to_out_dict(model, obj, attr_map)

    @router.patch("/{item_id}", response_model=OutSchema)
    def update_item(
        item_id: UUID,
        payload: PatchSchema,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        me = require_org_member(db, current_user)
        if write_scope == "admin":
            require_org_admin(db, me.id, me.organization_id)
        obj = (
            db.query(model)
            .filter(model.id == item_id, model.organization_id == me.organization_id)
            .first()
        )
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            if key in SERVER_FIELDS:
                continue
            setattr(obj, attr_map.get(key, key), value)
        db.commit()
        db.refresh(obj)
        return _to_out_dict(model, obj, attr_map)

    @router.delete("/{item_id}")
    def delete_item(
        item_id: UUID,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        me = require_org_member(db, current_user)
        if write_scope == "admin":
            require_org_admin(db, me.id, me.organization_id)
        obj = (
            db.query(model)
            .filter(model.id == item_id, model.organization_id == me.organization_id)
            .first()
        )
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(obj)
        db.commit()
        return {"id": str(item_id), "deleted": True}

    return router
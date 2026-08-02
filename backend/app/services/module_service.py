from sqlalchemy.orm import Session

from app.models.module import Module
from app.models.org_module import OrgModule
from app.models.platform import PlatformRole
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.widget import Widget

# Roles that may administer an organization (manage modules/users).
ORG_ADMIN_ROLE_NAMES = {"Company Admin", "CEO / Executive", "Owner", "Admin"}


def is_super_admin(db: Session, user_id) -> bool:
    """True when the user holds a platform Super Admin role."""
    return (
        db.query(PlatformRole)
        .filter(PlatformRole.user_id == user_id)
        .first()
        is not None
    )


def is_org_admin(db: Session, user_id, organization_id) -> bool:
    """True when the user holds an org-admin role for the organization."""
    return (
        db.query(UserRole)
        .join(Role, UserRole.role_id == Role.id)
        .filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == organization_id,
            Role.name.in_(ORG_ADMIN_ROLE_NAMES),
        )
        .first()
        is not None
    )


def get_user_organization_id(db: Session, user_id):
    """The organization the user belongs to, or None."""
    from app.models.user import User

    me = db.query(User).filter(User.id == user_id).first()
    if me is None:
        return None
    return me.organization_id


def list_modules_with_widgets(db: Session):
    """The full module catalog, each with its widgets, ordered."""
    modules = (
        db.query(Module)
        .order_by(Module.sort_order)
        .all()
    )
    widgets = (
        db.query(Widget)
        .order_by(Widget.module_key, Widget.sort_order)
        .all()
    )
    by_module: dict[str, list[Widget]] = {}
    for w in widgets:
        by_module.setdefault(w.module_key, []).append(w)

    return [
        {
            "key": m.key,
            "name": m.name,
            "description": m.description,
            "icon": m.icon,
            "group_name": m.group_name,
            "sort_order": m.sort_order,
            "dashboard": m.dashboard,
            "widgets": [
                {
                    "widget_key": w.widget_key,
                    "name": w.name,
                    "description": w.description,
                    "icon": w.icon,
                    "sort_order": w.sort_order,
                }
                for w in by_module.get(m.key, [])
            ],
        }
        for m in modules
    ]


def list_org_modules(db: Session, organization_id):
    """All module settings rows for an organization."""
    return (
        db.query(OrgModule)
        .filter(OrgModule.organization_id == organization_id)
        .order_by(OrgModule.module_key)
        .all()
    )


def update_super_admin_module(
    db: Session,
    organization_id,
    module_key: str,
    enabled: bool,
) -> OrgModule:
    """Super Admin enables/disables a module for an organization."""
    row = (
        db.query(OrgModule)
        .filter(
            OrgModule.organization_id == organization_id,
            OrgModule.module_key == module_key,
        )
        .first()
    )
    if row is None:
        # Row should exist (seeded on org create + backfilled); create on demand.
        row = OrgModule(
            organization_id=organization_id,
            module_key=module_key,
            enabled_by_super_admin=enabled,
        )
        db.add(row)
    else:
        row.enabled_by_super_admin = enabled
    db.commit()
    db.refresh(row)
    return row


def update_org_admin_module(
    db: Session,
    organization_id,
    module_key: str,
    enabled: bool,
) -> OrgModule:
    """Org Admin enables/disables a module for their own workspace.

    Only modules the Super Admin left enabled can be turned on by the org:
    enabling here while enabled_by_super_admin is false would have no effect
    on visibility, so reject it server-side to keep data consistent.
    """
    row = (
        db.query(OrgModule)
        .filter(
            OrgModule.organization_id == organization_id,
            OrgModule.module_key == module_key,
        )
        .first()
    )
    if row is None:
        row = OrgModule(
            organization_id=organization_id,
            module_key=module_key,
            enabled_by_org_admin=enabled,
        )
        db.add(row)
    else:
        if enabled and row.enabled_by_super_admin is False:
            raise ValueError(
                "This module was disabled by the platform admin and cannot be enabled"
            )
        row.enabled_by_org_admin = enabled
    db.commit()
    db.refresh(row)
    return row

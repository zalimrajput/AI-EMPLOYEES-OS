from uuid import UUID

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole



def create_organization(
        db:Session,
        data,
        created_by: UUID | None = None
):

    if created_by and not isinstance(created_by, UUID):
        created_by = UUID(str(created_by))

    organization = Organization(
        **data.model_dump(),
        created_by=created_by
    )


    db.add(
        organization
    )


    db.flush()


    # The backend inserts via the superuser connection (no JWT context), so the
    # set_org_creator trigger cannot bind the caller. Assign membership and the
    # Owner role here. The trg_seed_default_roles trigger (0059) seeds the
    # default roles for the new org, so the Owner role already exists.
    if created_by:
        user = db.query(
            User
        ).filter(
            User.id == created_by
        ).first()

        if user:
            if user.organization_id is None:
                user.organization_id = organization.id

            creator_role = db.query(
                Role
            ).filter(
                Role.organization_id == organization.id,
                Role.name == "Company Admin",
            ).first()

            # Guard against a duplicate assignment (e.g. if the org was created
            # through a path where trg_seed_default_roles already bound the
            # creator as Company Admin): user_roles has UNIQUE(user_id, role_id).
            already_creator = creator_role and db.query(
                UserRole
            ).filter(
                UserRole.user_id == user.id,
                UserRole.role_id == creator_role.id,
            ).first()

            if creator_role and not already_creator:
                db.add(
                    UserRole(
                        user_id=user.id,
                        role_id=creator_role.id,
                        organization_id=organization.id,
                    )
                )


    db.commit()


    db.refresh(
        organization
    )


    return organization
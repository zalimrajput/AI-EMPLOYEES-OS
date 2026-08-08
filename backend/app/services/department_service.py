from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.department import Department


def create_department(
    db: Session,
    organization_id,
    name: str,
    description: str | None = None,
):
    """Create a department inside an organization."""
    cleaned = (name or "").strip()
    if not cleaned:
        raise ValueError("Department name is required")

    existing = db.query(Department).filter(
        Department.organization_id == organization_id,
        func.lower(Department.name) == cleaned.lower(),
    ).first()
    if existing is not None:
        raise ValueError(f"A department named '{cleaned}' already exists")

    dept = Department(
        organization_id=organization_id,
        name=cleaned,
        description=description or None,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


def list_org_departments(
    db: Session,
    organization_id,
):
    """Return all departments belonging to an organization."""
    return db.query(Department).filter(
        Department.organization_id == organization_id
    ).order_by(Department.name).all()


def get_department(
    db: Session,
    department_id,
    organization_id,
):
    """Return one department, but only if it belongs to the organization."""
    dept = db.query(Department).filter(
        Department.id == department_id
    ).first()
    if dept is None:
        raise ValueError("Department not found")
    if str(dept.organization_id) != str(organization_id):
        raise ValueError("Department does not belong to this organization")
    return dept


def update_department(
    db: Session,
    department_id,
    organization_id,
    name: str | None = None,
    description: str | None = None,
):
    """Update a department inside the same organization."""
    dept = get_department(db, department_id, organization_id)

    if name is not None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Department name is required")
        existing = db.query(Department).filter(
            Department.organization_id == organization_id,
            func.lower(Department.name) == cleaned.lower(),
            Department.id != department_id,
        ).first()
        if existing is not None:
            raise ValueError(f"A department named '{cleaned}' already exists")
        dept.name = cleaned

    if description is not None:
        dept.description = description or None

    db.commit()
    db.refresh(dept)
    return dept


def delete_department(
    db: Session,
    department_id,
    organization_id,
):
    """Delete a department from the same organization.

    Raises ValueError if the department is not found or belongs to another org.
    """
    dept = db.query(Department).filter(
        Department.id == department_id
    ).first()

    if dept is None:
        raise ValueError("Department not found")
    if str(dept.organization_id) != str(organization_id):
        raise ValueError("Department does not belong to this organization")

    db.delete(dept)
    db.commit()
    return {"id": str(department_id), "deleted": True}

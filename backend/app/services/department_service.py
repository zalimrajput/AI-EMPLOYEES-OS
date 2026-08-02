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

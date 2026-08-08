"""Thin data-access layer shared by services.

The application is deliberately explicit: every query is filtered by
``organization_id`` in addition to the RLS rules inside Postgres.  This is the
defense-in-depth layer the architecture requires.
"""
from typing import Any, Iterable, Optional
from uuid import UUID

from sqlalchemy.orm import Session


class BaseRepository:
    """Generic, org-scoped data access for a single SQLAlchemy model."""

    model: Any = None

    def __init__(self, db: Session, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    def scoped(self, **extra_filters):
        query = self.db.query(self.model).filter(
            self.model.organization_id == self.organization_id
        )
        for key, value in extra_filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query

    def get(self, item_id: UUID, raise_missing: bool = True):
        row = self.scoped(id=item_id).first()
        if row is None and raise_missing:
            raise ValueError(f"{self.model.__name__} not found")
        return row

    def list(self, order_by=None, limit: Optional[int] = None) -> list:
        query = self.scoped()
        if order_by is not None:
            query = query.order_by(order_by)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def create(self, **attributes):
        row = self.model(**attributes, organization_id=self.organization_id)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row, **attributes) -> Any:
        for key, value in attributes.items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row) -> None:
        self.db.delete(row)
        self.db.commit()
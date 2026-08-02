import uuid

from sqlalchemy import (
    Column,
    Text,
    Integer,
    DateTime,
    Date,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from sqlalchemy.sql import func

from app.models.base import Base


class Warehouse(Base):

    __tablename__ = "warehouses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(
        Text,
        nullable=False
    )
    address = Column(Text)

    manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Supplier(Base):

    __tablename__ = "suppliers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )

    name = Column(
        Text,
        nullable=False
    )
    email = Column(Text)
    phone = Column(Text)
    address = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class InventoryItem(Base):

    __tablename__ = "inventory_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True
    )

    warehouse_id = Column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=True
    )

    quantity = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    reorder_level = Column(Integer, default=0)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class StockMovement(Base):

    __tablename__ = "stock_movements"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True
    )

    inventory_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=True
    )

    movement_type = Column(Text)
    quantity = Column(Integer)
    reference_type = Column(Text)
    reference_id = Column(UUID(as_uuid=True))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True
    )

    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id"),
        nullable=True
    )

    order_number = Column(Text)
    status = Column(Text, default="draft")
    total_amount = Column(NUMERIC(12, 2))
    expected_date = Column(Date)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

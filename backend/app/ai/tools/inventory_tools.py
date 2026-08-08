"""Inventory tools: stock, suppliers, purchase orders."""
from app.ai.tools.base import ToolSpec


def list_inventory(db, org_id, user_id, arguments: dict):
    from app.models.inventory import InventoryItem

    rows = (
        db.query(InventoryItem)
        .filter(InventoryItem.organization_id == org_id)
        .limit(arguments.get("limit", 50))
        .all()
    )
    return [
        {
            "id": str(i.id),
            "product_id": str(i.product_id) if i.product_id else None,
            "warehouse_id": str(i.warehouse_id) if i.warehouse_id else None,
            "quantity": i.quantity or 0,
            "minimum_stock": i.minimum_stock or 0,
            "reorder_level": i.reorder_level or 0,
            "low_stock": (i.quantity or 0) <= (i.reorder_level or 0),
        }
        for i in rows
    ]


def list_suppliers(db, org_id, user_id, arguments: dict):
    from app.models.inventory import Supplier

    rows = (
        db.query(Supplier)
        .filter(Supplier.organization_id == org_id)
        .limit(arguments.get("limit", 50))
        .all()
    )
    return [
        {"id": str(s.id), "name": s.name, "email": s.email, "phone": s.phone}
        for s in rows
    ]


def list_purchase_orders(db, org_id, user_id, arguments: dict):
    from app.models.inventory import PurchaseOrder

    query = db.query(PurchaseOrder).filter(PurchaseOrder.organization_id == org_id)
    if arguments.get("status"):
        query = query.filter(PurchaseOrder.status == arguments["status"])
    rows = query.order_by(PurchaseOrder.created_at.desc()).limit(arguments.get("limit", 50)).all()
    return [
        {
            "id": str(p.id),
            "order_number": p.order_number,
            "status": p.status,
            "total_amount": float(p.total_amount) if p.total_amount is not None else None,
        }
        for p in rows
    ]


INVENTORY_TOOLS: dict[str, ToolSpec] = {
    "list_inventory": ToolSpec(
        name="list_inventory",
        description="List stock levels and flag low-stock items.",
        parameters={
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
        handler=list_inventory,
    ),
    "list_suppliers": ToolSpec(
        name="list_suppliers",
        description="List suppliers.",
        parameters={
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
        handler=list_suppliers,
    ),
    "list_purchase_orders": ToolSpec(
        name="list_purchase_orders",
        description="List purchase orders, optionally by status.",
        parameters={
            "type": "object",
            "properties": {"status": {"type": "string"}, "limit": {"type": "integer"}},
        },
        handler=list_purchase_orders,
    ),
}
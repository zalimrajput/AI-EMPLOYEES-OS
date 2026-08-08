"""Real-DB smoke tests for inventory tools (list_inventory, list_suppliers)."""
import sys
import uuid

sys.path.insert(0, ".")

import pytest

from sqlalchemy import text


def _teardown(db, org):
    for statement in [
        "DELETE FROM stock_movements WHERE organization_id = :id",
        "DELETE FROM inventory_items WHERE organization_id = :id",
        "DELETE FROM purchase_orders WHERE organization_id = :id",
        "DELETE FROM suppliers WHERE organization_id = :id",
        "DELETE FROM warehouses WHERE organization_id = :id",
        "DELETE FROM users WHERE organization_id = :id",
        "DELETE FROM organizations WHERE id = :id",
    ]:
        db.execute(text(statement), {"id": org.id})
    db.commit()


def _org(db):
    from app.models.organization import Organization

    org = Organization(name="Inv Org", slug=f"inv-{uuid.uuid4().hex[:10]}", settings={})
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.mark.db
def test_list_inventory_handler_returns_real_row_and_low_stock_flag(db):
    from app.ai.tools.inventory_tools import INVENTORY_TOOLS
    from app.models.inventory import InventoryItem

    org = _org(db)
    low = InventoryItem(
        organization_id=org.id, quantity=3, minimum_stock=10, reorder_level=5
    )
    well = InventoryItem(
        organization_id=org.id, quantity=100, minimum_stock=10, reorder_level=5
    )
    db.add_all([low, well])
    db.commit()
    db.refresh(low)
    db.refresh(well)

    try:
        result = INVENTORY_TOOLS["list_inventory"].handler(db, org.id, None, {})
        by_id = {i["id"]: i for i in result}
        assert by_id[str(low.id)]["quantity"] == 3
        assert by_id[str(low.id)]["low_stock"] is True
        assert by_id[str(well.id)]["quantity"] == 100
        assert by_id[str(well.id)]["low_stock"] is False
    finally:
        _teardown(db, org)


@pytest.mark.db
def test_list_suppliers_handler_returns_real_row(db):
    from app.ai.tools.inventory_tools import INVENTORY_TOOLS
    from app.models.inventory import Supplier

    org = _org(db)
    sup = Supplier(
        organization_id=org.id,
        name="Acme Supply Co",
        email="orders@acme.com",
        phone="555-0100",
    )
    db.add(sup)
    db.commit()
    db.refresh(sup)

    try:
        result = INVENTORY_TOOLS["list_suppliers"].handler(db, org.id, None, {})
        assert any(s["id"] == str(sup.id) for s in result)
        row = next(s for s in result if s["id"] == str(sup.id))
        assert row["name"] == "Acme Supply Co"
        assert row["email"] == "orders@acme.com"
    finally:
        _teardown(db, org)
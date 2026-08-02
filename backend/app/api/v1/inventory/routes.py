from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.inventory import (
    InventoryItem,
    PurchaseOrder,
    StockMovement,
    Supplier,
    Warehouse,
)


router = APIRouter()


router.include_router(
    crud_router(
        Warehouse,
        prefix="/warehouses",
        tags=["Inventory"],
        search_fields=["name"],
    )
)


router.include_router(
    crud_router(
        Supplier,
        prefix="/suppliers",
        tags=["Inventory"],
        search_fields=["name", "email"],
    )
)


router.include_router(
    crud_router(
        InventoryItem,
        prefix="/inventory-items",
        tags=["Inventory"],
        search_fields=["product_id"],
    )
)


router.include_router(
    crud_router(
        StockMovement,
        prefix="/stock-movements",
        tags=["Inventory"],
    )
)


router.include_router(
    crud_router(
        PurchaseOrder,
        prefix="/purchase-orders",
        tags=["Inventory"],
        search_fields=["order_number"],
    )
)

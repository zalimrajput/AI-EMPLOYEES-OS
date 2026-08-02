from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem


router = APIRouter()


router.include_router(
    crud_router(
        Quotation,
        prefix="/quotations",
        tags=["Sales"],
        search_fields=["quotation_number"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        QuotationItem,
        prefix="/quotation-items",
        tags=["Sales"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        Product,
        prefix="/products",
        tags=["Sales"],
        search_fields=["name"],
        write_scope="member",
    )
)

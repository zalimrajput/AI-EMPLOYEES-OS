from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.finance import Budget, Expense, ExpenseCategory
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment


router = APIRouter()


router.include_router(
    crud_router(
        Invoice,
        prefix="/invoices",
        tags=["Finance"],
        search_fields=["invoice_number"],
    )
)


router.include_router(
    crud_router(
        InvoiceItem,
        prefix="/invoice-items",
        tags=["Finance"],
    )
)


router.include_router(
    crud_router(
        Payment,
        prefix="/payments",
        tags=["Finance"],
    )
)


router.include_router(
    crud_router(
        ExpenseCategory,
        prefix="/expense-categories",
        tags=["Finance"],
        search_fields=["name"],
    )
)


router.include_router(
    crud_router(
        Expense,
        prefix="/expenses",
        tags=["Finance"],
        search_fields=["title"],
    )
)


router.include_router(
    crud_router(
        Budget,
        prefix="/budgets",
        tags=["Finance"],
    )
)

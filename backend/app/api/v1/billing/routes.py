from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1._crud import crud_router
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.subscription import BillingTransaction, Plan, Subscription


router = APIRouter(
    prefix="/billing",
    tags=["Billing"]
)


@router.get("/plans")
# Public catalog: subscription plans are platform-level, not tenant-scoped.
def list_plans(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return (
        db.query(Plan)
        .order_by(Plan.price_monthly)
        .all()
    )


router.include_router(
    crud_router(
        Subscription,
        prefix="/subscriptions",
        tags=["Billing"],
        search_fields=["status"],
    )
)


router.include_router(
    crud_router(
        BillingTransaction,
        prefix="/transactions",
        tags=["Billing"],
    )
)

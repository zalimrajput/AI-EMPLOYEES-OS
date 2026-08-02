from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.hr import Attendance, Employee, JobCandidate, LeaveRequest


router = APIRouter()


router.include_router(
    crud_router(
        Employee,
        prefix="/employees",
        tags=["HR"],
        search_fields=["first_name", "last_name", "email", "employee_code"],
    )
)


router.include_router(
    crud_router(
        Attendance,
        prefix="/attendance",
        tags=["HR"],
    )
)


router.include_router(
    crud_router(
        LeaveRequest,
        prefix="/leave-requests",
        tags=["HR"],
        search_fields=["leave_type"],
    )
)


router.include_router(
    crud_router(
        JobCandidate,
        prefix="/candidates",
        tags=["HR"],
        search_fields=["name", "email"],
    )
)

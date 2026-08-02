from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.storage import StorageFile, StorageQuota


router = APIRouter()


router.include_router(
    crud_router(
        StorageFile,
        prefix="/storage-files",
        tags=["Storage"],
        search_fields=["file_name", "file_path"],
    )
)


router.include_router(
    crud_router(
        StorageQuota,
        prefix="/storage-quotas",
        tags=["Storage"],
    )
)

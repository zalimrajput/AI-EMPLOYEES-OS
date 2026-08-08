"""Storage: record file metadata and keep per-org storage usage in sync."""
from sqlalchemy.orm import Session

from app.models.storage import StorageFile, StorageQuota


def get_or_create_quota(db: Session, organization_id) -> StorageQuota:
    quota = (
        db.query(StorageQuota)
        .filter(StorageQuota.organization_id == organization_id)
        .first()
    )
    if quota is None:
        quota = StorageQuota(organization_id=organization_id)
        db.add(quota)
        db.commit()
        db.refresh(quota)
    return quota


def register_file(
    db: Session,
    organization_id,
    uploaded_by,
    file_name: str,
    file_path: str,
    mime_type: str | None = None,
    file_size: int = 0,
    bucket: str = "documents",
    entity_type: str | None = None,
    entity_id=None,
    metadata: dict | None = None,
) -> StorageFile:
    row = StorageFile(
        organization_id=organization_id,
        uploaded_by=uploaded_by,
        file_name=file_name,
        file_path=file_path,
        mime_type=mime_type,
        file_size=file_size,
        bucket=bucket,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata or {},
    )
    db.add(row)
    quota = get_or_create_quota(db, organization_id)
    quota.used_storage_bytes = (quota.used_storage_bytes or 0) + file_size
    db.commit()
    db.refresh(row)
    return row


def delete_file(db: Session, file: StorageFile) -> None:
    quota = get_or_create_quota(db, file.organization_id)
    quota.used_storage_bytes = max(
        (quota.used_storage_bytes or 0) - (file.file_size or 0), 0
    )
    db.delete(file)
    db.commit()
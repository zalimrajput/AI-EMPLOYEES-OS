from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.v1._crud import crud_router, require_org_member
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.knowledge_base import KnowledgeArticle
from app.services.document_service import ingest_document


router = APIRouter()


router.include_router(
    crud_router(
        Document,
        prefix="/documents",
        tags=["Documents"],
        search_fields=["filename", "mime_type"],
        write_scope="member",
    )
)


router.include_router(
    crud_router(
        KnowledgeArticle,
        prefix="/knowledge",
        tags=["Documents"],
        search_fields=["title", "content"],
        write_scope="member",
    )
)


@router.post("/documents/upload", tags=["Documents"])
# Protected endpoint: uploads a file, extracts text and indexes it for RAG.
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    me = require_org_member(db, current_user)
    MAX_SIZE = 20 * 1024 * 1024
    raw = await file.read()
    if len(raw) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")
    if not raw:
        raise HTTPException(status_code=422, detail="Empty file")

    result = ingest_document(
        db,
        me.organization_id,
        str(me.id),
        file.filename or "untitled",
        raw,
        title=title,
    )
    return result
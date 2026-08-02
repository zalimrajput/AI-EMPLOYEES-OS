from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.document import Document
from app.models.knowledge_base import KnowledgeArticle


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

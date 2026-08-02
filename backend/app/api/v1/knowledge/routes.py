from fastapi import APIRouter

from app.api.v1._crud import crud_router
from app.models.knowledge_base import KnowledgeArticle


router = APIRouter()


router.include_router(
    crud_router(
        KnowledgeArticle,
        prefix="/knowledge-articles",
        tags=["Knowledge Base"],
        search_fields=["title", "content", "source"],
        write_scope="member",
    )
)

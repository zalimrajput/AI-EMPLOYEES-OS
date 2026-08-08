"""AI conversation lifecycle used by the chat API and the orchestrator."""
from sqlalchemy.orm import Session

from app.models.ai_conversation import AIConversation
from app.models.ai_employee import AIEmployee


def ensure_conversation_access(
    db: Session, conversation_id, organization_id, user_id
) -> AIConversation:
    """Return the conversation only if it belongs to the org and the caller."""
    conversation = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.organization_id == organization_id,
            AIConversation.user_id == user_id,
        )
        .first()
    )
    if conversation is None:
        raise ValueError("Conversation not found")
    return conversation


def create_conversation(
    db: Session,
    organization_id,
    user_id,
    ai_employee_id,
    title: str | None = None,
) -> AIConversation:
    return AIConversation(
        organization_id=organization_id,
        user_id=user_id,
        ai_employee_id=ai_employee_id,
        title=title or "New conversation",
        status="active",
    )


def list_conversations_for_org(
    db: Session, organization_id, user_id=None
) -> list[AIConversation]:
    query = db.query(AIConversation).filter(
        AIConversation.organization_id == organization_id
    )
    if user_id is not None:
        query = query.filter(AIConversation.user_id == user_id)
    return query.order_by(AIConversation.updated_at.desc()).all()


def get_employee(
    db: Session, ai_employee_id, organization_id
) -> AIEmployee | None:
    return (
        db.query(AIEmployee)
        .filter(
            AIEmployee.id == ai_employee_id,
            AIEmployee.organization_id == organization_id,
        )
        .first()
    )
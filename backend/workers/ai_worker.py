"""AI worker: batch/non-interactive agent turns (e.g. scheduled digests,
workflow triggers, and one-off automations).

The interactive chat path uses the engine inline; this worker is used for
fire-and-forget content generation requested from background flows.
"""
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from workers.celery_app import celery_app

logger = logging.getLogger("workers.ai")


@celery_app.task(name="workers.ai_generate", bind=True, max_retries=2)
def ai_generate_task(
    self,
    organization_id: str,
    employee_id: str | None,
    prompt: str,
    temperature: float = 0.3,
):
    from app.ai.agents import DEFAULT_AGENT, resolve_agent
    from app.ai.engine import run_agent
    from app.models.ai_employee import AIEmployee

    db: Session = SessionLocal()
    try:
        employee = None
        agent = DEFAULT_AGENT
        if employee_id:
            employee = db.query(AIEmployee).filter(
                AIEmployee.id == employee_id,
                AIEmployee.organization_id == organization_id,
            ).first()
            if employee is not None:
                agent = resolve_agent(employee.role)

        reply = run_agent(
            db,
            organization_id=organization_id,
            user_id=None,
            agent=agent,
            user_message=prompt,
            model=employee.model if employee else None,
        )
        return {"reply": reply, "agent": agent.key}
    except Exception as exc:
        logger.exception("ai generate failed")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
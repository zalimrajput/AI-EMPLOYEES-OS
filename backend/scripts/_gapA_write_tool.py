"""Gap A: real write-tool round trip (create_task via HR agent, real model).

Verifies a row lands in `tasks` under the caller's organization_id.
"""
import json
import sys

sys.path.insert(0, ".")

from app.ai import engine, executor
from app.ai.agents import resolve_agent
from app.core.database import SessionLocal
from app.models.task import Task

MODEL = "openai/gpt-oss-20b:free"
ORG = "4e41953e-2169-480b-8661-e7b738cb3599"
_trace = []
_original_run = executor.run


def _wrapped_execute(db, tool_name, org_id, user_id, arguments, allowed_tools=None):
    result = _original_run(db, tool_name, org_id, user_id, arguments, allowed_tools=allowed_tools)
    _trace.append({"tool": tool_name, "arguments": arguments, "result": result})
    return result


def main():
    print(f"MODEL: {MODEL}\nORG: {ORG}")
    db = SessionLocal()
    try:
        agent = resolve_agent("HR Assistant")
        message = (
            "Create a high-priority task titled 'Follow up with Acme Corp lead' "
            "with description 'Send the updated pricing deck'."
        )
        print("USER:", message)
        reply = engine.run_agent(
            db,
            organization_id=ORG,
            user_id=None,
            agent=agent,
            user_message=message,
            model=MODEL,
            temperature=0.2,
        )
        print("\nTOOL CALLS EXECUTED:")
        for t in _trace:
            print(f"  {t['tool']}({json.dumps(t['arguments'])}) -> {json.dumps(t['result'])[:200]}")
        print(f"\nFINAL REPLY:\n{reply}")

        created = [t for t in _trace if t["tool"] == "create_task" and t["result"].get("id")]
        if not created:
            print("\nNO create_task ROW CREATED — cannot verify write path")
            return
        tid = created[0]["result"]["id"]
        row = db.query(Task).filter(Task.id == tid).first()
        print("\n=== DB ROW (tasks) ===")
        print(f"  id:             {row.id}")
        print(f"  organization_id: {row.organization_id}")
        print(f"  expected org:    {ORG}  ->  {'MATCH' if str(row.organization_id) == ORG else 'MISMATCH!'}")
        print(f"  title:          {row.title}")
        print(f"  description:    {row.description}")
        print(f"  priority:       {row.priority}")
        print(f"  status:         {row.status}")
        print(f"  ai_created:     {row.ai_created}")
        org_count = db.query(Task).filter(Task.organization_id == ORG).count()
        print(f"  tasks in this org after write: {org_count}")
    finally:
        db.close()


if __name__ == "__main__":
    engine.executor.run = _wrapped_execute
    main()

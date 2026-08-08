"""Gap B: one tool-call round trip on the production gpt-5 family model.

openai/gpt-5-nano is the only gpt-5-family model this account's balance can
afford (with max_tokens capped); full gpt-5 remains out of balance.
"""
import json
import sys

sys.path.insert(0, ".")

from app.ai import engine, executor
from app.ai.agents import resolve_agent
from app.core.database import SessionLocal

MODEL = "openai/gpt-5-nano"
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
        agent = resolve_agent("Sales Assistant")
        message = "How many leads do we have? List their names."
        print("USER:", message)
        reply = engine.run_agent(
            db,
            organization_id=ORG,
            user_id=None,
            agent=agent,
            user_message=message,
            model=MODEL,
            temperature=0.2,
            max_tokens=700,
        )
        print("\nTOOL CALLS EXECUTED:")
        for t in _trace:
            print(f"  {t['tool']}({json.dumps(t['arguments'])}) -> {json.dumps(t['result'])[:120]}")
        print(f"\nFINAL REPLY:\n{reply}")
    finally:
        db.close()


if __name__ == "__main__":
    engine.executor.run = _wrapped_execute
    main()

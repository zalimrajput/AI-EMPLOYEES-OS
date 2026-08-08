"""Probe: raw native-tool loop trace for the empty-reply diagnosis."""
import json
import sys

sys.path.insert(0, ".")

from app.ai import model_router
from app.ai.agents import resolve_agent
from app.ai.engine import MAX_STEPS, _openai_tools, build_messages
from app.ai.tools import execute_tool
from app.core.database import SessionLocal

ORG = "e7eaa307-1d93-476f-bfd3-8198c32356de"

for MODEL in ["openai/gpt-oss-20b:free", "nvidia/nemotron-3-ultra-550b-a55b:free"]:
    print("\n######## MODEL:", MODEL)
    agent = resolve_agent("Sales Assistant")
    msgs = build_messages(
        agent=agent,
        employee_name=agent.display_name,
        role=agent.role,
        allowed_tools=agent.allowed_tools,
        user_message="How many leads are in our pipeline? List their names and scores.",
    )
    tools = _openai_tools(agent.allowed_tools)
    db = SessionLocal()
    try:
        for step in range(MAX_STEPS):
            if step:
                msgs.append({"role": "user", "content": "Please continue."})
            r = model_router.complete_with_tools(msgs, tools, model=MODEL, temperature=0.2)
            print(f"  step{step}: content={r['content'][:80]!r} calls={r['tool_calls']}")
            if not r["tool_calls"]:
                print("  -> final:", repr(r["content"][:200]))
                break
            msgs.append(
                {
                    "role": "assistant",
                    "content": r["content"],
                    "tool_calls": [
                        {
                            "id": c["id"],
                            "type": "function",
                            "function": {
                                "name": c["name"],
                                "arguments": json.dumps(c["arguments"]),
                            },
                        }
                        for c in r["tool_calls"]
                    ],
                }
            )
            for c in r["tool_calls"]:
                res = execute_tool(db, c["name"], ORG, None, c["arguments"])
                msgs.append(
                    {
                        "role": "tool",
                        "tool_call_id": c["id"],
                        "content": json.dumps(res, default=str),
                    }
                )
                print(f"  executed {c['name']} -> {json.dumps(res)[:100]}")
    finally:
        db.close()

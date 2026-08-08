"""Gap 1: real end-to-end engine round trips against a funded-free LLM model.

Runs three scenarios through app.ai.engine.run_agent:
  1. plain question (no tool call expected)
  2. tool-triggering question (list_leads against real tenant data)
  3. multi-step conversation requiring 2+ back-to-back tool calls

Usage:  python scripts/_gap1_roundtrip.py [model]
"""
import json
import sys
import uuid

sys.path.insert(0, ".")

from app.ai import engine, executor
from app.ai.agents import resolve_agent
from app.core.database import SessionLocal
from app.services.crm_service import get_crm_stats

MODEL = sys.argv[1] if len(sys.argv) > 1 else "openai/gpt-oss-20b:free"
ORG = "4e41953e-2169-480b-8661-e7b738cb3599"

_trace = []
_original_run = executor.run


def _wrapped_execute(db, tool_name, org_id, user_id, arguments, allowed_tools=None):
    result = _original_run(db, tool_name, org_id, user_id, arguments, allowed_tools=allowed_tools)
    _trace.append({"tool": tool_name, "arguments": arguments, "result": result})
    return result


def _run(label, message):
    global _trace
    _trace = []
    print(f"\n{'='*70}\nSCENARIO: {label}\nUSER: {message}\n{'='*70}")
    db = SessionLocal()
    try:
        agent = resolve_agent("Sales Assistant")
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
        if not _trace:
            print("  (none)")
        for t in _trace:
            result_preview = json.dumps(t["result"], default=str)[:220]
            print(f"  {t['tool']}({json.dumps(t['arguments'])}) -> {result_preview}")
        print(f"\nFINAL REPLY:\n{reply}")
        return reply, _trace
    finally:
        db.close()


def main():
    stats = SessionLocal()
    try:
        before = get_crm_stats(stats, ORG)
        print("pre-run stats:", json.dumps(before, default=str))
    finally:
        stats.close()

    print(f"MODEL: {MODEL}\nORG: {ORG}")
    scenarios = [
        ("1. Plain question (no tool)", "What can you help me with as my sales assistant? Keep it to two sentences."),
        ("2. Single tool call", "How many leads are in our pipeline right now? Please list their names and scores."),
        ("3. Multi-step tool use (2+ calls)",
         "Check our leads, then look up the customer Acme Corp and tell me their email address — how many leads do we have in total?"),
    ]
    results = []
    for label, msg in scenarios:
        reply, trace = _run(label, msg)
        results.append({"label": label, "message": msg, "reply": reply, "tools": trace})
        with open("scripts/_gap1_output.json", "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, default=str)
    print("\n\nFull transcript saved to scripts/_gap1_output.json")


if __name__ == "__main__":
    engine.executor.run = _wrapped_execute
    main()

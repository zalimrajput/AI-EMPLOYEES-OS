"""Bootstrap-free engine smoke test: mock model_router, run a real tool loop."""
import sys

sys.path.insert(0, ".")

import app.ai.model_router as mr
from app.ai.engine import extract_tool_call, run_agent

SEQ = [
    '{{to_call: {"name": "list_leads", "arguments": {"limit": 3}}}}',
    "I found 3 leads in the pipeline.",
]


def fake_complete(messages, model=None, temperature=0.3):
    if any(m["role"] == "tool" for m in messages):
        return SEQ[1]
    return SEQ[0]


mr.complete = fake_complete
mr.stream = lambda *a, **k: iter([])


from app.ai.agents import DEFAULT_AGENT


def test_extract():
    assert extract_tool_call("plain answer") is None
    call = extract_tool_call('{{to_call: {"name": "x", "arguments": {}}}}')
    assert call and call["name"] == "x"


def main():
    test_extract()
    # fake db session
    class FakeDB:
        def query(self, m):
            return self

        def filter(self, *a, **k):
            return self

        def order_by(self, *a, **k):
            return self

        def limit(self, n):
            return self

        def all(self):
            return []

    result = run_agent(
        FakeDB(),
        organization_id="00000000-0000-0000-0000-000000000000",
        user_id=None,
        agent=DEFAULT_AGENT,
        user_message="tour my leads",
    )
    assert "3 leads" in result, result
    print("PASS:", result)


if __name__ == "__main__":
    main()
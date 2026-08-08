"""Gap 3 re-run: clean report + benign email + failure test with fake integration."""
import sys
import time

sys.path.insert(0, ".")

from celery.result import AsyncResult
from workers.celery_app import celery_app

ORG = "4e41953e-2169-480b-8661-e7b738cb3599"
DOC_ID = "4a65ad0a-dad0-4d06-8749-8e7ea04d9fd8"


def wait_and_report(label, async_result: AsyncResult):
    deadline = time.time() + 100
    while time.time() < deadline:
        if async_result.ready():
            print(f"[{label}] state={async_result.state} result={async_result.result}")
            return
        time.sleep(2)
    print(f"[{label}] TIMEOUT state={async_result.state}")


def main():
    r1 = celery_app.send_task("workers.generate_report", args=[ORG, None, "crm_summary", {}])
    print("enqueued generate_report:", r1.id)
    wait_and_report("generate_report", r1)

    r2 = celery_app.send_task("workers.embed_document", args=[DOC_ID, ORG, "upload"])
    print("enqueued embed_document:", r2.id)
    wait_and_report("embed_document", r2)

    r3 = celery_app.send_task(
        "workers.send_email", args=[ORG, "test-sandbox@example.com", "Test", "Body"]
    )
    print("enqueued send_email (no integration):", r3.id)
    wait_and_report("send_email (no integration)", r3)


if __name__ == "__main__":
    main()

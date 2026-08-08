"""Gap 3: enqueue real Celery tasks and wait for results.

Tasks enqueued:
  1. workers.generate_report  (report_worker)  — real CRM stats snapshot -> Report row
  2. workers.embed_document   (embedding_worker) — real doc; no embedding provider -> graceful indexed:false
  3. workers.send_email       (email_worker)   — no gmail integration -> benign no-op result
  4. workers.send_email       (email_worker)   — fake integration row -> deliberate failure/retry path

Waits for each result via the Redis result backend and prints status + result.
"""
import sys
import time

sys.path.insert(0, ".")

from celery.result import AsyncResult
from workers.celery_app import celery_app

ORG = "4e41953e-2169-480b-8661-e7b738cb3599"
DOC_ID = "4a65ad0a-dad0-4d06-8749-8e7ea04d9fd8"


def wait_and_report(label, async_result: AsyncResult):
    deadline = time.time() + 120
    while time.time() < deadline:
        if async_result.ready():
            print(f"\n[{label}] state={async_result.state}")
            if async_result.successful():
                print(f"[{label}] result={async_result.result}")
            else:
                print(f"[{label}] FAILED (after retries): {async_result.result}")
            return
        time.sleep(2)
    print(f"\n[{label}] TIMEOUT waiting (state={async_result.state})")


def main():
    r1 = celery_app.send_task(
        "workers.generate_report",
        args=[ORG, None, "crm_summary", {}],
        queue="celery",
    )
    print("enqueued generate_report:", r1.id)
    wait_and_report("generate_report", r1)

    r2 = celery_app.send_task(
        "workers.embed_document",
        args=[DOC_ID, ORG, "upload"],
        queue="celery",
    )
    print("enqueued embed_document:", r2.id)
    wait_and_report("embed_document", r2)

    r3 = celery_app.send_task(
        "workers.send_email",
        args=[ORG, "test-sandbox@example.com", "Test subject", "Test body"],
        queue="celery",
    )
    print("enqueued send_email (no integration):", r3.id)
    wait_and_report("send_email (no integration)", r3)

    r4 = celery_app.send_task(
        "workers.send_email",
        args=[ORG, "test-sandbox@example.com", "Failure test", "This should fail"],
        queue="celery",
    )
    print("enqueued send_email (failure test):", r4.id)
    wait_and_report("send_email (failure test)", r4)

    print("\nALL DONE")


if __name__ == "__main__":
    main()
